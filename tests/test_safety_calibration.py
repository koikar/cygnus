"""Tests for the safety supervisor, motion lock, and camera→table calibration."""

import threading

import numpy as np
import pytest

from cygnus.calibration import TableCalibration, fit
from cygnus.motion_lock import MotionBusy, current_owner, motion_lock
from cygnus.safety import check_ee_target, clamp_action, within_workspace


# --- safety supervisor -----------------------------------------------------
def test_clamp_drops_unknown_keys_and_clamps():
    out = clamp_action({"shoulder_pan.pos": 999.0, "bogus.key": 5.0})
    assert out["shoulder_pan.pos"] == 110.0  # clamped to limit
    assert "bogus.key" not in out  # injected key never forwarded


def test_workspace_bounds_fail_closed():
    assert within_workspace(0.30, 0.0, 0.10)
    assert not within_workspace(0.60, 0.0, 0.10)  # x past reach
    check_ee_target(0.30, 0.0, 0.10)  # in-bounds: no raise
    with pytest.raises(ValueError):
        check_ee_target(0.60, 0.0, 0.10)  # out-of-bounds: fail closed


# --- motion lock -----------------------------------------------------------
def test_motion_lock_serializes_concurrent_clients():
    started, release = threading.Event(), threading.Event()

    def hold_a():
        with motion_lock(owner="A", timeout=1.0):
            started.set()
            release.wait(2.0)

    t = threading.Thread(target=hold_a)
    t.start()
    assert started.wait(1.0)
    # While A holds the arm, B's motion fails closed instead of interleaving.
    with pytest.raises(MotionBusy):
        with motion_lock(owner="B", timeout=0.15):
            pass
    release.set()
    t.join(2.0)
    # Lock is free again after A releases.
    with motion_lock(owner="C", timeout=1.0):
        assert current_owner() == "C"
    assert current_owner() is None


# --- camera→table calibration ---------------------------------------------
def test_calibration_homography_roundtrip():
    H_true = np.array([[1.2, 0.10, 30.0], [0.05, 1.10, -20.0], [3e-4, 2e-4, 1.0]])
    pixels = [(100, 80), (400, 90), (420, 360), (110, 350), (250, 200), (300, 120)]
    corr = []
    for u, v in pixels:
        p = H_true @ np.array([u, v, 1.0])
        p /= p[2]
        corr.append({"pixel": [u, v], "table": [float(p[0]), float(p[1])]})
    cal = fit(corr, table_z=-0.05, camera="scene")
    assert cal.max_residual_m < 1e-4  # fits the correspondences

    # A fresh pixel projects to the same point the true homography would give.
    u, v = 220, 240
    p = H_true @ np.array([u, v, 1.0])
    p /= p[2]
    got = cal.pixel_to_table(u, v)
    assert abs(got["x"] - p[0]) < 1e-3
    assert abs(got["y"] - p[1]) < 1e-3
    assert got["z"] == -0.05


def test_calibration_needs_four_points():
    with pytest.raises(ValueError):
        fit([{"pixel": [0, 0], "table": [0, 0]}], table_z=0.0)
