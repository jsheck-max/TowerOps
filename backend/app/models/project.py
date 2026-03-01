import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))

    # Site identifiers
    site_name: Mapped[str] = mapped_column(String(255))
    site_number: Mapped[str | None] = mapped_column(String(100))
    carrier: Mapped[str] = mapped_column(String(100))  # AT&T, Verizon, T-Mobile, L3Harris
    market: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)

    # Project info
    scope_type: Mapped[str | None] = mapped_column(String(100))  # new build, mod, decom, maintenance
    tower_type: Mapped[str | None] = mapped_column(String(100))  # monopole, self-support, guyed, rooftop
    status: Mapped[str] = mapped_column(String(50), default="pre_construction")
    # Statuses: pre_construction, active, punch_list, closeout, complete, on_hold

    # Dates
    ntp_date: Mapped[date | None] = mapped_column(Date)
    start_date: Mapped[date | None] = mapped_column(Date)
    target_completion: Mapped[date | None] = mapped_column(Date)
    actual_completion: Mapped[date | None] = mapped_column(Date)

    # Budget summary (denormalized for dashboard speed)
    total_budget: Mapped[float | None] = mapped_column(default=0.0)
    total_actual: Mapped[float | None] = mapped_column(default=0.0)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="projects")
    budget_lines: Mapped[list["BudgetLine"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    time_entries: Mapped[list["TimeEntry"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    cost_entries: Mapped[list["CostEntry"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    milestones: Mapped[list["Milestone"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="project", cascade="all, delete-orphan")
