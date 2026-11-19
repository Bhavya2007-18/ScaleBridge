import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class ReportRow(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    format = Column(String(16), nullable=False, default="json")  # pdf, html, json, markdown
    title = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=True)
    summary_markdown = Column(Text, nullable=False)
    sections = Column(JSON, nullable=False, default=dict)
    provenance_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    assessment = relationship("Assessment", back_populates="reports")
    signoffs = relationship("ReviewSignoff", back_populates="report", cascade="all, delete-orphan")

class ReviewSignoff(Base):
    __tablename__ = "review_signoffs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="pending")  # approved, rejected, pending
    comment = Column(Text, nullable=True)
    signed_at = Column(DateTime, nullable=True)

    report = relationship("ReportRow", back_populates="signoffs")
    user = relationship("User")
