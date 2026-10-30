from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class QualityCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    check_name: str
    result: str
    reason: str
    measured_value: Optional[str] = None

class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    decision: str
    reviewer: str
    comments: Optional[str] = None
    reviewed_at: datetime

class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    original_filename: str
    file_size: int
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    status: str
    review_status: str
    upload_date: datetime
    quality_checks: list[QualityCheckOut] = []
    review: Optional[ReviewOut] = None

class ReviewCreate(BaseModel):
    decision: str
    reviewer: str = "Reviewer"
    comments: Optional[str] = None
