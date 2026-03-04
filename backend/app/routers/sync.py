from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.cost_entry import Integration
from app.models.project import Project
from app.utils.security import get_current_user
from app.services.integrations.workyard import WorkyardClient, normalize_workyard_project, normalize_workyard_employee
import logging
from datetime import datetime, timedelta

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
    """Fetch all projects/jobs from Workyard for import preview.
    
    Also fetches recent time cards to determine which projects are actively
    being worked on. Projects with no clock-ins in the last 5 days are
    marked as inactive (not in construction).
    """
    client = _get_workyard_client(db, current_user.org_id)
    try:
        # Fetch projects and recent time cards in parallel
        raw_projects = await client.get_projects()

        # Fetch time cards from the last 5 days to check activity
        five_days_ago = (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d")
        try:
            recent_cards = await client.get_time_cards(start_date=five_days_ago, end_date=datetime.utcnow().strftime("%Y-%m-%d"))
        except Exception as e:
            logger.warning(f"Could not fetch time cards for activity check: {e}")
            recent_cards = []

        # Build set of project IDs with recent activity
        active_project_ids = set()
        for tc in recent_cards:
            pid = tc.get("project_id") or tc.get("project", {}).get("id") if isinstance(tc.get("project"), dict) else tc.get("project_id")
            if pid:
                active_project_ids.add(str(pid))

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
            proj["recently_active"] = proj["workyard_id"] in active_project_ids
            if not proj["recently_active"]:
                proj["activity_status"] = "inactive"
            else:
                proj["activity_status"] = "in_construction"

        # Sort: active first, then inactive
        normalized.sort(key=lambda p: (not p["recently_active"], p["site_name"]))

        active_count = sum(1 for p in normalized if p["recently_active"])
        return {
            "projects": normalized,
            "total": len(normalized),
            "active_count": active_count,
            "inactive_count": len(normalized) - active_count,
        }
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
            site_number=proj["site_number"] or None,
            carrier=proj.get("customer_name") or "AT&T",
            address=proj["address"] or None,
            state=proj["state"] or None,
            market=proj["market"] or None,
            notes=f"workyard_id:{wid}",
        )
        db.add(project)
        imported.append(proj["site_name"])

    db.commit()
    return {"imported": len(imported), "skipped": len(skipped), "details": {"imported": imported, "skipped": skipped}}


@router.get("/workyard/debug")
async def debug_workyard_data(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Debug endpoint - returns raw Workyard data to inspect field names."""
    client = _get_workyard_client(db, current_user.org_id)
    result = {}

    # Sample project
    try:
        projects = await client.get_projects()
        result["project_count"] = len(projects)
        result["sample_project_keys"] = list(projects[0].keys()) if projects else []
        result["sample_project"] = projects[0] if projects else None
    except Exception as e:
        result["project_error"] = str(e)

    # Sample employee
    try:
        employees = await client.get_employees()
        result["employee_count"] = len(employees)
        result["sample_employee_keys"] = list(employees[0].keys()) if employees else []
        result["sample_employee"] = employees[0] if employees else None
    except Exception as e:
        result["employee_error"] = str(e)

    # Sample time cards (last 5 days)
    five_days_ago = (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    try:
        cards = await client.get_time_cards(start_date=five_days_ago, end_date=today)
        result["time_card_count"] = len(cards)
        result["sample_time_card_keys"] = list(cards[0].keys()) if cards else []
        result["sample_time_card"] = cards[0] if cards else None
    except Exception as e:
        result["time_card_error"] = str(e)

    return result
