import cv2
from pathlib import Path
from sqlalchemy.orm import Session
from .. import models
from ..config import (
    MIN_DURATION_SECONDS, MAX_DURATION_SECONDS, MIN_WIDTH, MIN_HEIGHT,
    MIN_FPS, MAX_FPS, MIN_BLUR_SCORE, BLACK_FRAME_THRESHOLD
)

def _add(db, video_id, name, result, reason, value=None):
    db.add(models.QualityCheck(
        video_id=video_id, check_name=name, result=result,
        reason=reason, measured_value=None if value is None else str(value)
    ))

def run_quality_checks(db: Session, video: models.Video):
    """Run deterministic, explainable baseline checks. Thresholds are configurable."""
    path = Path(video.storage_path)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        _add(db, video.id, "file_integrity", "FAIL", "OpenCV could not open/decode this video.")
        video.status = "QC_FAILED"
        db.commit()
        return

    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration = (frame_count / fps) if fps > 0 else 0
    video.duration_seconds = round(duration, 3)
    video.width, video.height = width, height
    video.fps = round(fps, 3)

    _add(db, video.id, "file_integrity", "PASS", "Video container opened and metadata was read.")
    duration_ok = MIN_DURATION_SECONDS <= duration <= MAX_DURATION_SECONDS
    _add(db, video.id, "duration", "PASS" if duration_ok else "FAIL",
         f"Duration must be between {MIN_DURATION_SECONDS:g} and {MAX_DURATION_SECONDS:g} seconds.",
         f"{duration:.2f}s")
    resolution_ok = width >= MIN_WIDTH and height >= MIN_HEIGHT
    _add(db, video.id, "resolution", "PASS" if resolution_ok else "FAIL",
         f"Minimum resolution is {MIN_WIDTH}x{MIN_HEIGHT}.", f"{width}x{height}")
    fps_ok = MIN_FPS <= fps <= MAX_FPS
    _add(db, video.id, "frame_rate", "PASS" if fps_ok else "FAIL",
         f"Frame rate must be between {MIN_FPS:g} and {MAX_FPS:g} FPS.", f"{fps:.2f} FPS")

    blur_scores, black_frames = [], 0
    sample_count = min(20, int(frame_count)) if frame_count > 0 else 0
    if sample_count:
        indices = sorted(set(int(i * max(frame_count - 1, 0) / max(sample_count - 1, 1))
                             for i in range(sample_count)))
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur_scores.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
            if float(gray.mean()) < 8:
                black_frames += 1
    cap.release()

    if blur_scores:
        avg_blur = sum(blur_scores) / len(blur_scores)
        blur_ok = avg_blur >= MIN_BLUR_SCORE
        _add(db, video.id, "blur", "PASS" if blur_ok else "FAIL",
             f"Average sampled-frame Laplacian variance should be at least {MIN_BLUR_SCORE:g}.",
             f"{avg_blur:.2f}")
        black_pct = (black_frames / len(blur_scores)) * 100
        black_ok = black_pct <= BLACK_FRAME_THRESHOLD
        _add(db, video.id, "black_frames", "PASS" if black_ok else "FAIL",
             f"Black/dark sampled frames should not exceed {BLACK_FRAME_THRESHOLD}% (simple brightness heuristic).",
             f"{black_pct:.1f}%")
    else:
        _add(db, video.id, "frame_analysis", "WARN",
             "No frames could be sampled; visual quality checks were not completed.")

    db.flush()
    failures = db.query(models.QualityCheck).filter_by(video_id=video.id, result="FAIL").count()
    video.status = "QC_FAILED" if failures else "QC_PASSED"
    db.commit()
