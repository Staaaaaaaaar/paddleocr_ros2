"""HTTP client for the recognition service."""

from __future__ import annotations

import json
import uuid
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def recognize_image(
    image_bytes: bytes,
    *,
    api_base_url: str,
    frame_id: str = "",
    debug: bool = False,
    timeout_sec: float = 5.0,
    filename: str = "frame.jpg",
) -> dict[str, Any] | None:
    url = f"{api_base_url.rstrip('/')}/v1/recognize"
    boundary = uuid.uuid4().hex

    body = bytearray()
    for name, value in (("frame_id", frame_id), ("debug", "true" if debug else "false")):
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )

    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        (
            f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
            "Content-Type: image/jpeg\r\n\r\n"
        ).encode()
    )
    body.extend(image_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    request = Request(
        url,
        data=bytes(body),
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )

    try:
        with urlopen(request, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    if not payload.get("success"):
        return None
    return payload.get("data")
