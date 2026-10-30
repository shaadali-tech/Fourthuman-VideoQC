import hashlib
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from ..database import get_db, SessionLocal
from .. import models
from ..schemas import VideoOut, ReviewCreate
from ..config import UPLOAD_DIR, MAX_UPLOAD_MB, ALLOWED_EXTENSIONS
from ..services.qc import run_quality_checks

router = APIRouter(prefix="/api", tags=["videos"])
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def process_video(video_id: str):
    db = SessionLocal()
    try:
        video = db.query(models.Video).filter_by(id=video_id).first()
        if video:
            video.status = "PROCESSING"
            db.commit()
            run_quality_checks(db, video)
    except Exception:
        db.rollback()
        video = db.query(models.Video).filter_by(id=video_id).first()
        if video:
            video.status = "PROCESSING_ERROR"
            db.commit()
    finally:
        db.close()

@router.post("/videos/upload", response_model=list[VideoOut])
async def upload_videos(background_tasks: BackgroundTasks,
                        files: list[UploadFile] = File(...),
                        db: Session = Depends(get_db)):
    created = []
    for upload in files:
        original = Path(upload.filename or "video").name
        suffix = Path(original).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, f"Unsupported file extension for {original}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
        video_id = str(uuid.uuid4())
        stored_name = f"{video_id}{suffix}"
        destination = UPLOAD_DIR / stored_name
        digest = hashlib.sha256()
        total = 0
        try:
            with destination.open("wb") as out:
                while chunk := await upload.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_UPLOAD_MB * 1024 * 1024:
                        raise HTTPException(413, f"{original} exceeds the {MAX_UPLOAD_MB} MB upload limit.")
                    digest.update(chunk)
                    out.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()
        if total == 0:
            destination.unlink(missing_ok=True)
            raise HTTPException(400, f"{original} is empty.")
        video = models.Video(
            id=video_id, original_filename=original, stored_filename=stored_name,
            storage_path=str(destination.resolve()), content_type=upload.content_type,
            file_size=total, sha256=digest.hexdigest(), status="UPLOADED",
            review_status="PENDING"
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        created.append(video)
        background_tasks.add_task(process_video, video_id)
    return created

@router.get("/videos", response_model=list[VideoOut])
def list_videos(status: str | None = None, review_status: str | None = None,
                db: Session = Depends(get_db)):
    q = db.query(models.Video).options(joinedload(models.Video.quality_checks), joinedload(models.Video.review))
    if status:
        q = q.filter(models.Video.status == status.upper())
    if review_status:
        q = q.filter(models.Video.review_status == review_status.upper())
    return q.order_by(models.Video.upload_date.desc()).all()

@router.get("/videos/{video_id}", response_model=VideoOut)
def get_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(models.Video).options(joinedload(models.Video.quality_checks), joinedload(models.Video.review)).filter_by(id=video_id).first()
    if not video:
        raise HTTPException(404, "Video not found.")
    return video

@router.get("/videos/{video_id}/file")
def stream_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(models.Video).filter_by(id=video_id).first()
    if not video or not Path(video.storage_path).is_file():
        raise HTTPException(404, "Video file not found.")
    return FileResponse(video.storage_path, media_type=video.content_type or "video/mp4",
                        filename=video.original_filename)

@router.post("/videos/{video_id}/review", response_model=VideoOut)
def review_video(video_id: str, payload: ReviewCreate, db: Session = Depends(get_db)):
    decision = payload.decision.upper()
    if decision not in {"APPROVED", "REJECTED"}:
        raise HTTPException(400, "Decision must be APPROVED or REJECTED.")
    video = db.query(models.Video).options(joinedload(models.Video.quality_checks), joinedload(models.Video.review)).filter_by(id=video_id).first()
    if not video:
        raise HTTPException(404, "Video not found.")
    review = video.review
    if review is None:
        review = models.Review(video_id=video_id, decision=decision,
                               reviewer=payload.reviewer, comments=payload.comments)
        db.add(review)
    else:
        review.decision, review.reviewer, review.comments = decision, payload.reviewer, payload.comments
    video.review_status = decision
    db.commit()
    db.refresh(video)
    return video

@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    videos = db.query(models.Video).all()
    return {
        "total": len(videos),
        "qc_passed": sum(v.status == "QC_PASSED" for v in videos),
        "qc_failed": sum(v.status == "QC_FAILED" for v in videos),
        "processing": sum(v.status in {"UPLOADED", "PROCESSING"} for v in videos),
        "pending_review": sum(v.review_status == "PENDING" for v in videos),
        "approved": sum(v.review_status == "APPROVED" for v in videos),
        "rejected": sum(v.review_status == "REJECTED" for v in videos),
    }
