from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.budget import BudgetLine
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, BudgetLineCreate, BudgetLineResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    status: str | None = None,
    carrier: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all projects for the user's organization."""
    query = db.query(Project).filter(Project.org_id == current_user.org_id)
    if status:
        query = query.filter(Project.status == status)
    if carrier:
        query = query.filter(Project.carrier == carrier)
    return query.order_by(Project.updated_at.desc()).all()


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new project (tower site)."""
    project = Project(org_id=current_user.org_id, **data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single project by ID."""
    project = db.query(Project).filter(
        Project.id == project_id, Project.org_id == current_user.org_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a project."""
    project = db.query(Project).filter(
        Project.id == project_id, Project.org_id == current_user.org_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


# --- Budget Lines ---
@router.get("/{project_id}/budget", response_model=list[BudgetLineResponse])
def get_budget(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get budget lines for a project."""
    return db.query(BudgetLine).filter(BudgetLine.project_id == project_id).all()


@router.post("/{project_id}/budget", response_model=BudgetLineResponse, status_code=201)
def add_budget_line(
    project_id: UUID,
    data: BudgetLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a budget line to a project."""
    line = BudgetLine(project_id=project_id, **data.model_dump())
    db.add(line)
    db.commit()
    db.refresh(line)
    return line
