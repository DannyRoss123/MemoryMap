# for pictures 
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid

from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()  # enable HEIC/HEIF support in Pillow for phones 
    HEIF_OK = True
except Exception:
    HEIF_OK = False

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("")
async def upload(file: UploadFile = File(...)):
    # Only allow images
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(415, "Only image files are allowed.")

    # If it's HEIC but we couldn't enable pillow-heif, ask for JPG/PNG instead
    if "heic" in (file.content_type or "").lower() and not HEIF_OK:
        raise HTTPException(415, "HEIC not supported on this server yet. Upload JPG/PNG or install pillow-heif.")

    uploads = Path("uploads")
    uploads.mkdir(parents=True, exist_ok=True)

    # Normalize all uploads to JPEG for browser compatibility
    fname = f"{uuid.uuid4().hex}.jpg"
    dest = uploads / fname

    try:
        file.file.seek(0)
        img = Image.open(file.file)
        # Convert to RGB (JPEG doesn't support alpha)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(dest, format="JPEG", quality=85, optimize=True)
    except Exception as e:
        raise HTTPException(400, f"Invalid image: {e}")
    finally:
        file.file.close()

    # Public URL that <img> can display inline
    return {"url": f"/uploads/{fname}"}
