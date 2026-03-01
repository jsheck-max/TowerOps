import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class CostEntry(Base):
    """Manual or auto-calculated cost entries per project."""
    __tablename__ = "cost_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))

    category: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text)
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(50), default="manual")  # manual, auto_labor, invoice

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="cost_entries")


class CrewMember(Base):
    """Field workers synced from time-tracking platforms."""
    __tablename__ = "crew_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))

    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(100), default="technician")  # foreman, technician, ground_hand
    crew_name: Mapped[str | None] = mapped_column(String(255))  # "Crew A", "Brandon's Crew"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    external_id: Mapped[str | None] = mapped_column(String(255))  # ID in source platform
    source_platform: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="crew_members")
    time_entries: Mapped[list["TimeEntry"]] = relationship(back_populates="crew_member")


class LaborRate(Base):
    """Configurable labor rates by role."""
    __tablename__ = "labor_rates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))

    role: Mapped[str] = mapped_column(String(100))  # foreman, technician, ground_hand
    hourly_rate: Mapped[float] = mapped_column(Float)
    overtime_multiplier: Mapped[float] = mapped_column(Float, default=1.5)
    per_diem: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="labor_rates")


class Integration(Base):
    """Connected time-tracking platform configurations."""
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))

    platform: Mapped[str] = mapped_column(String(50))  # workyard, busybusy, exaktime, clockshark
    api_key_encrypted: Mapped[str | None] = mapped_column(Text)
    api_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_frequency_minutes: Mapped[int] = mapped_column(Integer, default=30)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="integrations")
