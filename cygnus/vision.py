"""Lightweight visual perception helpers for the tabletop block task."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ColorBlob:
    label: str
    center: tuple[int, int]
    bbox: tuple[int, int, int, int]
    area: float

    def as_dict(self) -> dict[str, Any]:
        x, y, w, h = self.bbox
        return {
            "label": self.label,
            "center": {"x": self.center[0], "y": self.center[1]},
            "bbox": {"x": x, "y": y, "width": w, "height": h},
            "area_px": self.area,
        }


def detect_colored_blocks(
    frame,
    *,
    min_area: float = 120.0,
    max_area: float = 3000.0,
    max_results: int = 12,
    roi: dict[str, int] | None = None,
) -> list[dict]:
    """Detect saturated tabletop blocks by HSV color blobs.

    This is intentionally modest: it returns target candidates, not ground truth.
    Agents should combine the result with `look(camera="scene")` until we have a
    calibrated hand-eye model.
    """
    import cv2
    import numpy as np

    x_offset = 0
    y_offset = 0
    if roi:
        h, w = frame.shape[:2]
        x = max(0, min(w - 1, int(roi.get("x", 0))))
        y = max(0, min(h - 1, int(roi.get("y", 0))))
        width = max(1, min(w - x, int(roi.get("width", w - x))))
        height = max(1, min(h - y, int(roi.get("height", h - y))))
        frame = frame[y : y + height, x : x + width]
        x_offset = x
        y_offset = y

    # LeRobot's OpenCV camera delivers RGB frames (not OpenCV's native BGR).
    # Using BGR2HSV here swaps red/blue and mislabels a blue cube as "orange",
    # which was observed live on the SO-101 wrist cam.
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    ranges = {
        "orange": [((5, 80, 50), (35, 255, 255))],
        "cyan": [((80, 60, 45), (105, 255, 255))],
        "blue": [((105, 60, 45), (130, 255, 255))],
        "purple": [((130, 45, 35), (165, 255, 255))],
    }
    kernel = np.ones((3, 3), np.uint8)
    blobs: list[ColorBlob] = []
    for label, parts in ranges.items():
        mask = None
        for lo, hi in parts:
            part = cv2.inRange(hsv, np.array(lo, dtype=np.uint8), np.array(hi, dtype=np.uint8))
            mask = part if mask is None else cv2.bitwise_or(mask, part)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < min_area or area > max_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            # Reject long skinny highlights/cables; blocks are compact-ish.
            aspect = w / max(h, 1)
            if aspect < 0.25 or aspect > 4.0:
                continue
            moments = cv2.moments(contour)
            if moments["m00"] == 0:
                continue
            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])
            blobs.append(
                ColorBlob(
                    label=label,
                    center=(cx + x_offset, cy + y_offset),
                    bbox=(x + x_offset, y + y_offset, w, h),
                    area=area,
                )
            )

    blobs.sort(key=lambda b: b.area, reverse=True)
    return [blob.as_dict() for blob in blobs[:max_results]]
