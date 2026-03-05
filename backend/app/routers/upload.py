import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Annotated

router = APIRouter()
MAX_FILES = 10

def _get_upload_dir() -> Path:
    upload_dir = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir

@router.post("/upload")
async def upload_images(files: Annotated[list[UploadFile], File()]):
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Max {MAX_FILES} files per upload")

    upload_dir = _get_upload_dir()
    job_id = str(uuid.uuid4())
    paths = []

    for file in files:
        ext = Path(file.filename or "img.jpg").suffix or ".jpg"
        dest = upload_dir / f"{uuid.uuid4()}{ext}"
        content = await file.read()
        dest.write_bytes(content)
        paths.append(str(dest))

    from app.tasks import process_image
    for path in paths:
        process_image.delay(path, job_id)

    return {"job_id": job_id, "queued": len(paths)}
