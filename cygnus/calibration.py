"""Camera→table calibration: map pixel detections to robot/table coordinates.

`detect_colored_blocks` returns **pixels**; grasping needs a **table (x, y)** in
the robot base frame. Assuming the blocks sit on a flat table plane at a known
base-frame ``z``, a planar **homography** maps image pixels → table xy. Collect
≥4 correspondences (drive the gripper to known table points, note the pixel of a
marker there), fit once, and thereafter project any detection to a real
`move_ee_to` target. Without this, vision-guided grasping is trial-and-error
(SayCan/Code-as-Policies assume *grounded* perception).

Dependency-light: the homography is solved with a numpy DLT (no OpenCV needed),
so it's testable in a minimal env. Persisted to ``calibration/<camera>.json``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

CALIB_DIR = Path(os.getenv("CYGNUS_CALIB_DIR", "calibration"))


def _solve_homography(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Least-squares planar homography H (3x3) with H @ [u,v,1] ∝ [x,y,1].

    Direct Linear Transform: stack 2 rows per correspondence, solve by SVD.
    Needs ≥4 non-collinear point pairs.
    """
    if len(src) < 4:
        raise ValueError("need at least 4 correspondences to fit a homography")
    rows = []
    for (u, v), (x, y) in zip(src, dst):
        rows.append([-u, -v, -1, 0, 0, 0, u * x, v * x, x])
        rows.append([0, 0, 0, -u, -v, -1, u * y, v * y, y])
    _, _, vh = np.linalg.svd(np.asarray(rows, dtype=float))
    H = vh[-1].reshape(3, 3)
    return H / H[2, 2]


class TableCalibration:
    """Projects image pixels onto the table plane (base-frame x, y, fixed z)."""

    def __init__(self, H, table_z: float, camera: str):
        self.H = np.asarray(H, dtype=float)
        self.table_z = float(table_z)
        self.camera = camera

    def pixel_to_table(self, u: float, v: float) -> dict:
        """Map a pixel to a base-frame point on the table plane → {x, y, z}."""
        p = self.H @ np.array([float(u), float(v), 1.0])
        p = p / p[2]
        return {"x": float(p[0]), "y": float(p[1]), "z": self.table_z}

    # -- persistence -------------------------------------------------------
    def to_dict(self) -> dict:
        return {"camera": self.camera, "table_z": self.table_z, "H": self.H.tolist()}

    def save(self, path: Path | None = None) -> Path:
        CALIB_DIR.mkdir(parents=True, exist_ok=True)
        path = path or CALIB_DIR / f"{self.camera}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2))
        return path

    @classmethod
    def load(cls, camera: str, path: Path | None = None) -> "TableCalibration":
        path = path or CALIB_DIR / f"{camera}.json"
        d = json.loads(Path(path).read_text())
        return cls(d["H"], d["table_z"], d["camera"])


def fit(correspondences: list[dict], table_z: float, camera: str = "scene") -> TableCalibration:
    """Fit from correspondences ``[{"pixel": [u, v], "table": [x, y]}, ...]``.

    Reports the fit residual so a bad/degenerate calibration fails loud rather
    than silently producing wrong grasp targets.
    """
    src = np.array([c["pixel"] for c in correspondences], dtype=float)
    dst = np.array([c["table"] for c in correspondences], dtype=float)
    H = _solve_homography(src, dst)
    cal = TableCalibration(H, table_z, camera)
    resid = max(
        ((cal.pixel_to_table(u, v)["x"] - x) ** 2 + (cal.pixel_to_table(u, v)["y"] - y) ** 2) ** 0.5
        for (u, v), (x, y) in zip(src, dst)
    )
    cal.max_residual_m = float(resid)  # type: ignore[attr-defined]
    return cal
