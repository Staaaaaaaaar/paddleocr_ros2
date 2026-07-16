"""PaddleOCR 管线仪屏幕识别核心库（HTTP 识别服务专用）。"""

from paddle_ocr.core import (
    is_calibrated,
    load_calib_config,
    recognize,
    save_calib_config,
)

__all__ = ["is_calibrated", "load_calib_config", "recognize", "save_calib_config"]
