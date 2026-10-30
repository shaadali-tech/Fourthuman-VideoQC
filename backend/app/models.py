from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Video(Base):
    __tablename__ = "videos"
    id = Column(String(36), primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    storage_path = Column(Text, nullable=False)
    content_type = Column(String(120), nullable=True)
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    duration_seconds = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    status = Column(String(30), default="UPLOADED", nullable=False, index=True)
    review_status = Column(String(30), default="PENDING", nullable=False, index=True)
    upload_date = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    quality_checks = relationship("QualityCheck", back_populates="video", cascade="all, delete-orphan")
    review = relationship("Review", back_populates="video", uselist=False, cascade="all, delete-orphan")

class QualityCheck(Base):
    __tablename__ = "quality_checks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    check_name = Column(String(80), nullable=False)
    result = Column(String(12), nullable=False)  # PASS, FAIL, WARN
    reason = Column(Text, nullable=False)
    measured_value = Column(String(120), nullable=True)
    checked_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    video = relationship("Video", back_populates="quality_checks")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, unique=True)
    decision = Column(String(20), nullable=False)
    reviewer = Column(String(120), nullable=False, default="Reviewer")
    comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    video = relationship("Video", back_populates="review")
