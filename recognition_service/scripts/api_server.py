"""管线仪屏幕识别 HTTP API。"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from screen_ocr import is_calibrated, load_calib_config, recognize, save_calib_config  # noqa: E402
from screen_ocr import core as ocr_core  # noqa: E402

app = FastAPI(
    title="Pipeline Locator Screen API",
    description="OCR API for a specific pipeline locator model (<MODEL_NAME>).",
    version="1.0.0",
)

CALIB = load_calib_config()
OCR_LOCK = threading.Lock()


class CompassConfig(BaseModel):
    center: list[int] = Field(..., min_length=2, max_length=2)
    radius: int = Field(..., gt=0)


class CalibConfig(BaseModel):
    rois: dict[str, list[int]]
    compass: CompassConfig


def _decode_image(content: bytes) -> np.ndarray:
    arr = np.frombuffer(content, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _recognize_with_profile(
    img: np.ndarray,
    rois: dict,
    compass: dict,
    debug: bool = False,
    frame_id: str = "",
) -> tuple[dict[str, Any] | None, dict[str, float]]:
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    debug_ctx = ocr_core.DebugContext(enabled=debug)
    debug_ctx.setup(tag=frame_id or "api")
    img = ocr_core.prepare_image(img)
    timings["prepare_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    templates = ocr_core._get_templates(img, rois)
    timings["templates_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    intensity_roi = img[rois["intensity"][1] : rois["intensity"][3], rois["intensity"][0] : rois["intensity"][2]]
    intensity = ocr_core.ocr_signal_strength(intensity_roi, templates, debug=debug_ctx)
    timings["intensity_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    current_roi = img[rois["current"][1] : rois["current"][3], rois["current"][0] : rois["current"][2]]
    current = ocr_core.ocr_integer_value(current_roi, "current", templates)
    timings["current_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    depth_roi = img[rois["depth"][1] : rois["depth"][3], rois["depth"][0] : rois["depth"][2]]
    depth = ocr_core.ocr_integer_value(depth_roi, "depth", templates)
    timings["depth_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    arrow = ocr_core.arrow_detect(img, rois["arrow_right"], rois["arrow_left"], debug=debug_ctx)
    timings["arrow_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    compass_angle = ocr_core.get_compass_info(img, compass, debug=debug_ctx)
    timings["compass_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    if compass_angle == "none" or intensity == "none":
        return None, timings

    return {
        "signal_strength": intensity,
        "pipeline_current": "none" if current == "none" else f"{current} mA",
        "burial_depth": f"{depth} m",
        "arrow_direction": ocr_core.normalize_arrow(arrow),
        "compass_angle": compass_angle,
        "compass_angle_deg": ocr_core.parse_compass_angle(compass_angle),
    }, timings


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "model_loaded": True,
        "calibrated": is_calibrated(CALIB),
    }


@app.get("/v1/config")
def get_config() -> dict[str, Any]:
    return {
        "rois": CALIB.get("rois"),
        "compass": CALIB.get("compass"),
        "calibrated": is_calibrated(CALIB),
    }


@app.put("/v1/config")
def put_config(config: CalibConfig) -> dict[str, Any]:
    global CALIB

    required_rois = {
        "intensity",
        "current",
        "depth",
        "arrow_left",
        "arrow_right",
    }
    missing = required_rois - set(config.rois.keys())
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing ROI keys: {sorted(missing)}",
        )

    for name, rect in config.rois.items():
        if len(rect) != 4:
            raise HTTPException(
                status_code=400,
                detail=f"ROI '{name}' must have 4 integers [x1, y1, x2, y2]",
            )

    rois = config.rois
    compass = config.compass.model_dump()
    save_calib_config(rois, compass)
    CALIB = {"rois": rois, "compass": compass}

    return {
        "success": True,
        "calibrated": True,
        "config": CALIB,
    }


@app.post("/v1/recognize")
async def recognize_api(
    image: UploadFile = File(...),
    debug: bool = Form(False),
    frame_id: str = Form(""),
    profile: bool = Form(False),
) -> dict[str, Any]:
    if not is_calibrated(CALIB):
        return {
            "success": False,
            "error": {
                "code": "NOT_CALIBRATED",
                "message": "Missing config files. Use PUT /v1/config to upload calibration.",
            },
        }

    content = await image.read()
    if not content:
        return {
            "success": False,
            "error": {
                "code": "EMPTY_IMAGE",
                "message": "Uploaded image is empty",
            },
        }

    img = _decode_image(content)
    if img is None:
        return {
            "success": False,
            "error": {
                "code": "INVALID_IMAGE",
                "message": "Failed to decode image. Use jpg/png/bmp.",
            },
        }

    t0 = time.perf_counter()
    with OCR_LOCK:
        if profile:
            result, timings = _recognize_with_profile(
                img,
                CALIB["rois"],
                CALIB["compass"],
                debug=debug,
                frame_id=frame_id,
            )
        else:
            result = recognize(
                img,
                CALIB["rois"],
                CALIB["compass"],
                debug=debug,
                frame_id=frame_id,
            )
            timings = {}
    cost_ms = (time.perf_counter() - t0) * 1000
    fps = 1000 / cost_ms if cost_ms > 0 else 0

    meta = {
        "process_time_ms": round(cost_ms, 1),
        "fps": round(fps, 2),
        "frame_id": frame_id,
    }
    if profile:
        meta["timings"] = timings

    if result is None:
        return {
            "success": False,
            "error": {
                "code": "RECOGNITION_FAILED",
                "message": "Compass or signal strength not detected",
            },
            "meta": meta,
        }

    return {
        "success": True,
        "data": result,
        "meta": meta,
    }


def main() -> None:
    import os

    host = os.environ.get("SCREEN_OCR_API_HOST", "127.0.0.1")
    port = int(os.environ.get("SCREEN_OCR_API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
