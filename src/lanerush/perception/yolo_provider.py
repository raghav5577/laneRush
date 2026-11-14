"""YOLO-based DetectionProvider — demo only, not for production use.

Requires ultralytics and PyTorch; install only in the ml/ environment.
This module is NOT imported by the main lanerush package at runtime.
"""

from __future__ import annotations

from lanerush.models import LaneObservation


class YoloProvider:
    """Demo: runs a YOLOv8 classifier on camera frames to count vehicles.

    Label: DEMO ONLY. Not validated for production use.
    Not imported by the core pipeline; only used for demonstration.
    """

    def __init__(self, model_path: str, camera_sources: dict[str, str]) -> None:
        try:
            from ultralytics import YOLO  # type: ignore[import-untyped]  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "ultralytics is not installed. Install it in the ml/ environment only."
            ) from exc
        self._model = YOLO(model_path)
        self._sources = camera_sources  # lane_id -> camera source path/index

    def observe(self, t: int) -> dict[str, LaneObservation]:
        result: dict[str, LaneObservation] = {}
        for lane_id, src in self._sources.items():
            # Placeholder: would run model on a frame from src
            result[lane_id] = LaneObservation(
                lane_id=lane_id,
                count=0,
                halting=0,
                max_wait=0.0,
                emergency=False,
                source="yolo",
            )
        return result
