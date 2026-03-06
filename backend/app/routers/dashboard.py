from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas import DashboardStats, ProjectSummary
from app.utils.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get high-level dashboard statistics."""
    projects = db.query(Project).filter(Project.org_id == current_user.org_id).all()

    active_statuses = {"pre_construction", "active", "in_progress", "punch_list"}
    active = [p for p in projects if p.status in active_statuses]
    total_budget = sum(p.total_budget or 0 for p in projects)
    total_actual = sum(p.total_actual or 0 for p in projects)
    over_budget = [p for p in projects if (p.total_actual or 0) > (p.total_budget or 0) and (p.total_budget or 0) > 0]

    return DashboardStats(
        total_projects=len(projects),
        active_projects=len(active),
        total_budget=total_budget,
        total_actual=total_actual,
        over_budget_count=len(over_budget),
        on_track_count=len(active) - len([p for p in active if p in over_budget]),
    )


@router.get("/projects", response_model=list[ProjectSummary])
def get_dashboard_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get project summaries for the dashboard cards."""
    projects = db.query(Project).filter(
        Project.org_id == current_user.org_id,
        Project.status.in_(["pre_construction", "active", "in_progress", "punch_list"]),
    ).order_by(Project.updated_at.desc()).all()

    summaries = []
    for p in projects:
        budget = p.total_budget or 0
        actual = p.total_actual or 0
        budget_pct = (actual / budget * 100) if budget > 0 else 0

        days_active = None
        if p.start_date:
            days_active = (date.today() - p.start_date).days

        summaries.append(ProjectSummary(
            id=p.id,
            site_name=p.site_name,
            carrier=p.carrier,
            status=p.status,
            total_budget=budget,
            total_actual=actual,
            budget_pct=round(budget_pct, 1),
            days_active=days_active,
        ))
    return summaries
