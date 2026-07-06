import uuid
from pathlib import Path

from fastapi import UploadFile

from .config import settings

# Dev local: disco. Prod: reemplazar por R2 (S3-compatible) manteniendo la interfaz.

ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


async def save_image(file: UploadFile) -> str | None:
    ext = ALLOWED_TYPES.get(file.content_type or "")
    if ext is None:
        return None
    key = f"{uuid.uuid4().hex}{ext}"
    dest = Path(settings.uploads_dir) / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())
    return key


def image_url(key: str | None) -> str | None:
    if not key:
        return None
    return f"/uploads/{key}"
