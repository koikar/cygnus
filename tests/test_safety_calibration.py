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


def test_motion_lock_allows_nested_motion_helpers_same_thread():
    with motion_lock(owner="outer", timeout=1.0):
        assert current_owner() == "outer"
        with motion_lock(owner="inner", timeout=1.0):
            assert current_owner() == "inner"
        assert current_owner() == "outer"
    assert current_owner() is None


def test_server_ee_target_fails_closed_outside_workspace(monkeypatch):
    from cygnus import server
    from cygnus.robot.sim import SimBackend

    robot = SimBackend()
    robot.connect()
    monkeypatch.setattr(server, "_robot", robot)

    with pytest.raises(ValueError, match="outside the safe workspace"):
        server.move_ee_to(x=0.90, y=0.0, z=0.20)


def test_server_calibration_tools_project_safe_table_targets(monkeypatch, tmp_path):
    from cygnus import calibration, server

    monkeypatch.setattr(calibration, "CALIB_DIR", tmp_path)
    correspondences = [
        {"pixel": [100, 100], "table": [0.20, -0.10]},
        {"pixel": [300, 100], "table": [0.40, -0.10]},
        {"pixel": [300, 300], "table": [0.40, 0.10]},
        {"pixel": [100, 300], "table": [0.20, 0.10]},
    ]

    fitted = server.fit_table_calibration(correspondences, table_z=-0.04, camera="scene")
    assert fitted["samples"] == 4
    assert (tmp_path / "scene.json").exists()

    projected = server.project_pixel_to_table(200, 200, camera="scene")
    assert projected["workspace_ok"] is True
    assert projected["table_target"]["z"] == -0.04
    assert abs(projected["table_target"]["x"] - 0.30) < 1e-6
    assert abs(projected["table_target"]["y"]) < 1e-6


def test_so101_observation_falls_back_to_joints_when_camera_is_stale():
    from cygnus.robot.so101 import SO101Backend

    class Bus:
        def sync_read(self, key):
            assert key == "Present_Position"
            return {"shoulder_pan": 1.0, "gripper": 60.0}

    class Robot:
        bus = Bus()

        def get_observation(self):
            raise RuntimeError("OpenCVCamera(0) latest frame is too old")

    backend = SO101Backend(port="/dev/null")
    backend._robot = Robot()
    obs = backend.get_observation()

    assert obs.joints == {"shoulder_pan.pos": 1.0, "gripper.pos": 60.0}
    assert obs.frames == {}
    assert "camera unavailable/stale" in obs.note


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
