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


def detect_colored_blocks(frame, *, min_area: float = 120.0, max_results: int = 12) -> list[dict]:
    """Detect saturated tabletop blocks by HSV color blobs.

    This is intentionally modest: it returns target candidates, not ground truth.
    Agents should combine the result with `look(camera="scene")` until we have a
    calibrated hand-eye model.
    """
    import cv2
    import numpy as np

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
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
            if area < min_area:
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
            blobs.append(ColorBlob(label=label, center=(cx, cy), bbox=(x, y, w, h), area=area))

    blobs.sort(key=lambda b: b.area, reverse=True)
    return [blob.as_dict() for blob in blobs[:max_results]]
