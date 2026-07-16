from pathlib import Path

from setuptools import find_packages, setup


def _requirements() -> list[str]:
    req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
    lines: list[str] = []
    for raw in req_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


setup(
    name="paddle-ocr-recognition-service",
    version="1.0.0",
    packages=find_packages(),
    install_requires=_requirements(),
    entry_points={
        "console_scripts": [
            "paddle_ocr_api = paddle_ocr.api_server:main",
            "paddle_ocr_recognize = paddle_ocr.recognize_cli:main",
        ],
    },
)
