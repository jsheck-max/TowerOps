from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from uuid import UUID


# --- Auth ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    org_id: UUID

    class Config:
        from_attributes = True


# --- Organization ---
class OrgCreate(BaseModel):
    name: str
    admin_email: EmailStr
    admin_password: str
    admin_name: str


# --- Project ---
class ProjectCreate(BaseModel):
    site_name: str
    site_number: str | None = None
    carrier: str
    market: str | None = None
    region: str | None = None
    state: str | None = None
    address: str | None = None
    scope_type: str | None = None
    tower_type: str | None = None
    ntp_date: date | None = None
    target_completion: date | None = None
    total_budget: float | None = 0.0
    notes: str | None = None

class ProjectUpdate(BaseModel):
    site_name: str | None = None
    status: str | None = None
    carrier: str | None = None
    market: str | None = None
    total_budget: float | None = None
    notes: str | None = None

class ProjectResponse(BaseModel):
    id: UUID
    site_name: str
    site_number: str | None
    carrier: str
    market: str | None
    state: str | None
    scope_type: str | None
    tower_type: str | None
    status: str
    ntp_date: date | None
    target_completion: date | None
    total_budget: float | None
    total_actual: float | None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Budget ---
class BudgetLineCreate(BaseModel):
    category: str
    description: str | None = None
    budgeted_amount: float

class BudgetLineResponse(BaseModel):
    id: UUID
    category: str
    description: str | None
    budgeted_amount: float
    actual_amount: float

    class Config:
        from_attributes = True


# --- Time Entry ---
class TimeEntryCreate(BaseModel):
    project_id: UUID
    crew_member_id: UUID | None = None
    work_date: date
    hours: float
    overtime_hours: float = 0.0
    source_platform: str = "manual"

class TimeEntryResponse(BaseModel):
    id: UUID
    project_id: UUID
    crew_member_id: UUID | None
    work_date: date
    hours: float
    overtime_hours: float
    source_platform: str
    labor_cost: float | None

    class Config:
        from_attributes = True


# --- Dashboard ---
class DashboardStats(BaseModel):
    total_projects: int
    active_projects: int
    total_budget: float
    total_actual: float
    over_budget_count: int
    on_track_count: int

class ProjectSummary(BaseModel):
    id: UUID
    site_name: str
    carrier: str
    status: str
    total_budget: float
    total_actual: float
    budget_pct: float  # actual / budget as percentage
    days_active: int | None
