import uuid
from datetime import datetime, date
from sqlalchemy import String, Float, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class TimeEntry(Base):
    """Normalized time entry from any clock-in/out platform."""
    __tablename__ = "time_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    crew_member_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("crew_members.id"))

    # Time data
    work_date: Mapped[date] = mapped_column(Date, index=True)
    clock_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clock_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hours: Mapped[float] = mapped_column(Float)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0.0)

    # Source tracking
    source_platform: Mapped[str] = mapped_column(String(50))  # workyard, busybusy, exaktime, clockshark, manual, csv
    source_id: Mapped[str | None] = mapped_column(String(255))  # external ID from the platform

    # GPS (if available)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    # Calculated cost (filled by cost calculator service)
    labor_cost: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="time_entries")
    crew_member: Mapped["CrewMember | None"] = relationship(back_populates="time_entries")
