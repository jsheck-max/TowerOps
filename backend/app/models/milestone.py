import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Milestone(Base):
    """Schedule milestones per project, with carrier-specific templates."""
    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))

    name: Mapped[str] = mapped_column(String(255))
    # Common: ntp_received, permits_submitted, permits_approved, crew_dispatched,
    #         construction_start, construction_complete, punch_list, closeout_submitted, closeout_approved
    target_date: Mapped[date | None] = mapped_column(Date)
    actual_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, in_progress, complete, overdue
    sort_order: Mapped[int | None] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="milestones")


class Document(Base):
    """Project documents linked or uploaded per site."""
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))

    doc_type: Mapped[str] = mapped_column(String(100))
    # Types: ntp, construction_drawings, structural_analysis, rfds, permit,
    #        closeout_package, photos, safety, other
    filename: Mapped[str] = mapped_column(String(500))
    file_url: Mapped[str | None] = mapped_column(Text)  # S3 URL or local path
    status: Mapped[str] = mapped_column(String(50), default="received")  # received, reviewed, approved
    notes: Mapped[str | None] = mapped_column(Text)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="documents")
