from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.cost_entry import Integration
from app.models.project import Project
from app.utils.security import get_current_user
from app.services.integrations.workyard import WorkyardClient, normalize_workyard_project, normalize_workyard_employee
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sync", tags=["sync"])


class ImportProjectRequest(BaseModel):
    workyard_id: str
    site_name: str
    site_number: str | None = None
    carrier: str = "AT&T"
    address: str | None = None
    state: str | None = None
    market: str | None = None
    scope_type: str | None = None
    tower_type: str | None = None
    total_budget: float = 0.0


def _get_workyard_client(db: Session, org_id: str) -> WorkyardClient:
    """Get Workyard client from stored integration credentials."""
    integration = db.query(Integration).filter(
        Integration.org_id == org_id,
        Integration.platform == "workyard",
        Integration.is_active == True,
    ).first()
    if not integration or not integration.api_key_encrypted:
        raise HTTPException(status_code=400, detail="Workyard is not connected. Go to Settings > Integrations to connect.")
    return WorkyardClient(api_key=integration.api_key_encrypted)


@router.get("/workyard/projects")
async def fetch_workyard_projects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch all projects/jobs from Workyard for import preview."""
    client = _get_workyard_client(db, current_user.org_id)
    try:
        raw_projects = await client.get_projects()
        normalized = [normalize_workyard_project(p) for p in raw_projects]

        # Mark which ones are already imported
        existing_ids = set()
        projects = db.query(Project).filter(Project.org_id == current_user.org_id).all()
        for p in projects:
            if p.notes and "workyard_id:" in (p.notes or ""):
                wid = p.notes.split("workyard_id:")[1].split(",")[0].strip()
                existing_ids.add(wid)

        for proj in normalized:
            proj["already_imported"] = proj["workyard_id"] in existing_ids

        return {"projects": normalized, "total": len(normalized)}
    except Exception as e:
        logger.error(f"Failed to fetch Workyard projects: {e}")
        raise HTTPException(status_code=502, detail=f"Workyard API error: {str(e)}")


@router.get("/workyard/employees")
async def fetch_workyard_employees(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch all employees from Workyard."""
    client = _get_workyard_client(db, current_user.org_id)
    try:
        raw_employees = await client.get_employees()
        normalized = [normalize_workyard_employee(e) for e in raw_employees]
        return {"employees": normalized, "total": len(normalized)}
    except Exception as e:
        logger.error(f"Failed to fetch Workyard employees: {e}")
        raise HTTPException(status_code=502, detail=f"Workyard API error: {str(e)}")


@router.post("/workyard/import")
async def import_workyard_project(
    data: ImportProjectRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Import a single Workyard project into TowerOps."""
    # Check if already imported
    existing = db.query(Project).filter(
        Project.org_id == current_user.org_id,
        Project.notes.contains(f"workyard_id:{data.workyard_id}"),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"This project is already imported as '{existing.site_name}'")

    project = Project(
        org_id=current_user.org_id,
        site_name=data.site_name,
        site_number=data.site_number,
        carrier=data.carrier,
        address=data.address,
        state=data.state,
        market=data.market,
        scope_type=data.scope_type,
        tower_type=data.tower_type,
        total_budget=data.total_budget,
        notes=f"workyard_id:{data.workyard_id}",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": str(project.id), "site_name": project.site_name, "message": "Project imported successfully"}


@router.post("/workyard/import-bulk")
async def import_workyard_projects_bulk(
    project_ids: list[str],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Bulk import multiple Workyard projects."""
    client = _get_workyard_client(db, current_user.org_id)
    raw_projects = await client.get_projects()
    normalized = {normalize_workyard_project(p)["workyard_id"]: normalize_workyard_project(p) for p in raw_projects}

    imported = []
    skipped = []
    for wid in project_ids:
        proj = normalized.get(wid)
        if not proj:
            skipped.append({"workyard_id": wid, "reason": "Not found in Workyard"})
            continue

        existing = db.query(Project).filter(
            Project.org_id == current_user.org_id,
            Project.notes.contains(f"workyard_id:{wid}"),
        ).first()
        if existing:
            skipped.append({"workyard_id": wid, "reason": f"Already imported as {existing.site_name}"})
            continue

        project = Project(
            org_id=current_user.org_id,
            site_name=proj["site_name"],
            site_number=proj["site_number"],
            address=proj["address"],
            state=proj["state"],
            market=proj["market"],
            notes=f"workyard_id:{wid}",
        )
        db.add(project)
        imported.append(proj["site_name"])

    db.commit()
    return {"imported": len(imported), "skipped": len(skipped), "details": {"imported": imported, "skipped": skipped}}
