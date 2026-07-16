#!/usr/bin/env python3
"""CLI: read a screenshot and print JSON recognition result."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2

from paddle_ocr import is_calibrated, load_calib_config, recognize


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PaddleOCR pipeline locator screen recognition",
    )
    default_image = (
        Path(__file__).resolve().parents[1] / "examples" / "images" / "image0000000.bmp"
    )
    parser.add_argument("image", nargs="?", default=str(default_image), help="Image path")
    parser.add_argument("--debug", action="store_true", help="Save debug images to output/")
    args = parser.parse_args()

    config = load_calib_config()
    if not is_calibrated(config):
        print("Missing rois.json or compass.json in recognition_service/config.", file=sys.stderr)
        return 1

    img = cv2.imread(args.image)
    if img is None:
        print(f"Failed to read image: {args.image}", file=sys.stderr)
        return 1

    t0 = time.perf_counter()
    result = recognize(
        img,
        config["rois"],
        config["compass"],
        debug=args.debug,
        frame_id="cli",
    )
    cost_ms = (time.perf_counter() - t0) * 1000

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result is None:
        print(f"Recognition failed, elapsed: {cost_ms:.0f} ms", file=sys.stderr)
        return 2

    print(f"Elapsed: {cost_ms:.0f} ms", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
