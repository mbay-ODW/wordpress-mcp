"""WordPress REST API client – Basic Auth via Application Passwords."""

import base64
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


def _base_url() -> str:
    url = os.getenv("WP_URL", "")
    if not url:
        raise ValueError("WP_URL ist nicht gesetzt.")
    return url.rstrip("/")


def _auth_headers() -> dict[str, str]:
    username = os.getenv("WP_USERNAME", "")
    password = os.getenv("WP_APP_PASSWORD", "")
    if not username or not password:
        raise ValueError("WP_USERNAME oder WP_APP_PASSWORD ist nicht gesetzt.")
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Accept": "application/json",
    }


async def wp_request(
    method: str,
    endpoint: str,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    url = f"{_base_url()}/wp-json/wp/v2/{endpoint.lstrip('/')}"
    headers = _auth_headers()
    if json_data is not None:
        headers["Content-Type"] = "application/json"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=json_data,
            params=params,
        )
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return {}


async def wp_upload_media(
    filename: str,
    content_type: str,
    file_data: bytes,
    title: str | None = None,
    alt_text: str | None = None,
) -> dict[str, Any]:
    """Upload media via WordPress REST API binary upload."""
    url = f"{_base_url()}/wp-json/wp/v2/media"
    headers = _auth_headers()
    headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    headers["Content-Type"] = content_type

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, content=file_data)
        resp.raise_for_status()
        media = resp.json()

    media_id = media["id"]
    update: dict[str, Any] = {}
    if title:
        update["title"] = title
    if alt_text:
        update["alt_text"] = alt_text
    if update:
        media = await wp_request("POST", f"media/{media_id}", json_data=update)

    return media
