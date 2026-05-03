import io
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from app.routers.recipes import _require_user

router = APIRouter()

UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", "/app/uploads"))
MAX_ORIGINAL_PX = 2000
THUMB_PX = 400
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def _save_image(file_bytes: bytes, filename_stem: str, ext: str) -> tuple[str, str]:
    """Process, resize, and save original + thumbnail. Returns (filename, thumb_filename)."""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
        img = Image.open(io.BytesIO(file_bytes))
    except (UnidentifiedImageError, Exception) as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image") from exc

    if img.format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported image format: {img.format}")

    img = img.convert("RGB")

    # Save original, capped at MAX_ORIGINAL_PX on the long edge
    orig = img.copy()
    if max(orig.size) > MAX_ORIGINAL_PX:
        orig.thumbnail((MAX_ORIGINAL_PX, MAX_ORIGINAL_PX), Image.LANCZOS)

    filename = f"{filename_stem}.jpg"
    orig.save(UPLOADS_DIR / filename, format="JPEG", quality=85, optimize=True)

    # Save thumbnail
    thumb = img.copy()
    thumb.thumbnail((THUMB_PX, THUMB_PX), Image.LANCZOS)
    thumb_filename = f"thumb_{filename_stem}.jpg"
    thumb.save(UPLOADS_DIR / thumb_filename, format="JPEG", quality=80, optimize=True)

    return filename, thumb_filename


@router.post("/api/uploads", status_code=201)
async def upload_image(file: UploadFile, request: Request):
    _require_user(request)

    contents = await file.read()
    stem = uuid.uuid4().hex
    filename, thumb_filename = _save_image(contents, stem, "jpg")

    return {
        "filename": filename,
        "url": f"/uploads/{filename}",
        "thumb_url": f"/uploads/{thumb_filename}",
    }
