import hashlib
import mimetypes
import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import MediaAsset, Question, QuestionMedia
from ..schemas import MediaClipCreate, MediaOut

router = APIRouter(prefix="/api/media", tags=["media"])
settings = get_settings()


def detect_type(mime: str | None, filename: str) -> str:
    mime = mime or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("audio/"):
        return "audio"
    if mime.startswith("video/"):
        return "video"
    return "other"


def probe_duration(path: Path) -> float | None:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


@router.post("", response_model=MediaOut, status_code=201)
async def upload_media(
    file: UploadFile = File(...),
    role: str = Form("question"),
    title: str | None = Form(None),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    if not contents:
        raise HTTPException(400, "Empty file")
    digest = hashlib.sha256(contents).hexdigest()
    existing = db.scalar(select(MediaAsset).where(MediaAsset.sha256 == digest))
    if existing:
        return existing

    media_type = detect_type(file.content_type, file.filename or "upload.bin")
    extension = Path(file.filename or "upload.bin").suffix.lower() or ".bin"
    relative = Path(media_type) / f"{uuid.uuid4().hex}{extension}"
    absolute = settings.media_root / relative
    absolute.parent.mkdir(parents=True, exist_ok=True)
    absolute.write_bytes(contents)

    width = height = None
    duration = None
    if media_type == "image":
        try:
            with Image.open(absolute) as img:
                width, height = img.size
        except Exception:
            pass
    elif media_type in {"audio", "video"}:
        duration = probe_duration(absolute)

    row = MediaAsset(
        media_type=media_type,
        role=role,
        path=relative.as_posix(),
        mime_type=file.content_type,
        sha256=digest,
        width=width,
        height=height,
        duration_seconds=duration,
        title=title or file.filename,
        description=description,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[MediaOut])
def list_media(db: Session = Depends(get_db)):
    return list(db.scalars(select(MediaAsset).order_by(MediaAsset.id.desc()).limit(500)).all())


@router.post("/{media_id}/attach/{question_id}", status_code=204)
def attach_media(media_id: int, question_id: int, db: Session = Depends(get_db)):
    media = db.get(MediaAsset, media_id)
    question = db.get(Question, question_id)
    if not media or not question:
        raise HTTPException(404, "Media or question not found")
    exists = db.scalar(
        select(QuestionMedia).where(
            QuestionMedia.media_asset_id == media_id,
            QuestionMedia.question_id == question_id,
        )
    )
    if not exists:
        db.add(QuestionMedia(question_id=question_id, media_asset_id=media_id))
        db.commit()


@router.post("/{media_id}/clip", response_model=MediaOut, status_code=201)
def create_audio_clip(media_id: int, payload: MediaClipCreate, db: Session = Depends(get_db)):
    source = db.get(MediaAsset, media_id)
    if not source:
        raise HTTPException(404, "Media not found")
    if source.media_type != "audio":
        raise HTTPException(400, "Only audio assets can be clipped")

    source_path = settings.media_root / source.path
    if not source_path.exists():
        raise HTTPException(404, "Source media file is missing")

    relative = Path("audio") / "clips" / f"{uuid.uuid4().hex}.mp3"
    output_path = settings.media_root / relative
    output_path.parent.mkdir(parents=True, exist_ok=True)

    filters = []
    if payload.normalize:
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    if payload.fade:
        fade_out_start = max(0.0, payload.duration_seconds - 0.35)
        filters.extend(["afade=t=in:st=0:d=0.15", f"afade=t=out:st={fade_out_start:.3f}:d=0.35"])

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", str(payload.start_seconds),
        "-i", str(source_path),
        "-t", str(payload.duration_seconds),
        "-vn",
    ]
    if filters:
        command.extend(["-af", ",".join(filters)])
    command.extend(["-codec:a", "libmp3lame", "-b:a", "192k", str(output_path)])

    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    except FileNotFoundError as exc:
        raise HTTPException(500, "ffmpeg is not installed") from exc
    except subprocess.CalledProcessError as exc:
        raise HTTPException(400, f"ffmpeg failed: {exc.stderr[-500:]}") from exc

    contents = output_path.read_bytes()
    digest = hashlib.sha256(contents).hexdigest()
    duplicate = db.scalar(select(MediaAsset).where(MediaAsset.sha256 == digest))
    if duplicate:
        output_path.unlink(missing_ok=True)
        return duplicate

    clip = MediaAsset(
        media_type="audio",
        role="question",
        path=relative.as_posix(),
        mime_type="audio/mpeg",
        sha256=digest,
        duration_seconds=probe_duration(output_path) or payload.duration_seconds,
        title=f"{source.title or 'Audio'} — {payload.start_seconds:g}s clip",
        description=f"Derived from media #{source.id}; start={payload.start_seconds:g}s duration={payload.duration_seconds:g}s",
        source_id=source.source_id,
    )
    db.add(clip)
    db.commit()
    db.refresh(clip)
    return clip
