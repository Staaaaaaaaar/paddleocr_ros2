"""Map screen OCR recognition output to screen_ocr_msgs/SensorMsg."""

from __future__ import annotations

import math
import re
from typing import Any

from geometry_msgs.msg import Vector3
from screen_ocr_msgs.msg import SensorMsg
from std_msgs.msg import Header


_UNKNOWN_COVARIANCE = -1.0


def _parse_number(text: str) -> float | None:
    if not text or text == "none":
        return None
    match = re.search(r"([-+]?\d*\.?\d+)", text)
    return float(match.group(1)) if match else None


def _heading_to_magnetic_field(heading_deg: float | None) -> Vector3:
    vector = Vector3()
    if heading_deg is None:
        return vector

    radians = math.radians(heading_deg)
    vector.x = math.sin(radians)
    vector.y = math.cos(radians)
    vector.z = 0.0
    return vector


def _default_covariance() -> list[float]:
    return [
        _UNKNOWN_COVARIANCE, 0.0, 0.0,
        0.0, _UNKNOWN_COVARIANCE, 0.0,
        0.0, 0.0, _UNKNOWN_COVARIANCE,
    ]


def _arrow_flags(arrow_direction: str) -> tuple[bool, bool]:
    direction = (arrow_direction or "none").lower()
    left = direction in {"left", "both"}
    right = direction in {"right", "both"}
    return left, right


def recognition_to_sensor_msg(
    recognition: dict[str, Any],
    header: Header,
) -> SensorMsg:
    percent = _parse_number(recognition.get("signal_strength", ""))
    current = _parse_number(recognition.get("pipeline_current", ""))
    depth = _parse_number(recognition.get("burial_depth", ""))
    heading = recognition.get("compass_angle_deg")
    if heading is None:
        heading = _parse_number(recognition.get("compass_angle", ""))

    left_arrow, right_arrow = _arrow_flags(recognition.get("arrow_direction", "none"))

    msg = SensorMsg()
    msg.header = header
    msg.magnetic_field = _heading_to_magnetic_field(heading)
    msg.magnetic_field_covariance = _default_covariance()
    msg.signal_strength_percent = float(percent) if percent is not None else float("nan")
    msg.signal_strength = (
        float(percent) / 100.0 if percent is not None else float("nan")
    )
    msg.depth_meters = float(depth) if depth is not None else float("nan")
    msg.current_milliamps = float(current) if current is not None else float("nan")
    msg.pipeline_heading_degrees = float(heading) if heading is not None else float("nan")
    msg.left_arrow = left_arrow
    msg.right_arrow = right_arrow
    return msg
