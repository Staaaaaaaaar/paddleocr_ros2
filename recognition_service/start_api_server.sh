#!/usr/bin/env bash
# 在 conda 环境 ocr 中启动识别 HTTP 服务。
# 用法:
#   conda activate ocr
#   ./start_api_server.sh
#
# 可选环境变量:
#   SCREEN_OCR_API_HOST  默认 127.0.0.1
#   SCREEN_OCR_API_PORT  默认 8000
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH:-}"
exec python scripts/api_server.py
