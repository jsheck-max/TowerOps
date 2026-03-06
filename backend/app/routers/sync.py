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
        today = datetime.utcnow().strftime("%Y-%m-%d")
        try:
            recent_cards = await client.get_time_cards(start_date=five_days_ago, end_date=today)
            logger.warning(f"Time cards fetched: {len(recent_cards)} entries in last 5 days")
        except Exception as e:
            logger.warning(f"Could not fetch time cards for activity check: {type(e).__name__}: {e}")
            recent_cards = []

        # Build set of project IDs with recent activity
        # Workyard stores project refs in cost_allocations[].org_project_id
        active_project_ids = set()
        for tc in recent_cards:
            for alloc in tc.get("cost_allocations", []):
                if isinstance(alloc, dict):
                    pid = alloc.get("org_project_id")
                    if pid:
                        active_project_ids.add(str(pid))
        logger.warning(f"Active project IDs from time cards: {len(active_project_ids)}")

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



@router.post("/workyard/sync-time")
async def sync_workyard_time(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Pull time cards from Workyard and sync hours + costs to TowerOps projects.
    
    1. Fetches time cards for the last N days
    2. Fetches employees to get pay rates
    3. Matches time cards to imported projects via org_project_id
    4. Creates/updates time entries and calculates labor costs
    5. Updates project total_actual with real spend
    """
    from app.models.time_entry import TimeEntry
    from app.models.cost_entry import CrewMember
    
    client = _get_workyard_client(db, current_user.org_id)
    
    start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Fetch time cards and employees in sequence
    logger.warning(f"Syncing time cards for last {days} days...")
    time_cards = await client.get_time_cards(start_date=start_date, end_date=end_date)
    logger.warning(f"Fetched {len(time_cards)} time cards")
    
    employees_raw = await client.get_employees()
    logger.warning(f"Fetched {len(employees_raw)} employees")
    
    # Build employee lookup: employee_id -> {name, pay_rate}
    emp_lookup = {}
    for emp in employees_raw:
        eid = emp.get("id") or emp.get("employee_id")
        if not eid:
            continue
        pay_rate = emp.get("pay_rate") or emp.get("hourly_rate") or emp.get("rate") or emp.get("wage")
        if isinstance(pay_rate, dict):
            pay_rate = pay_rate.get("amount") or pay_rate.get("rate")
        try:
            pay_rate = float(pay_rate) if pay_rate else 0.0
        except (ValueError, TypeError):
            pay_rate = 0.0
        name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        emp_lookup[str(eid)] = {"name": name, "pay_rate": pay_rate}
    
    logger.warning(f"Employee lookup built: {len(emp_lookup)} employees, {sum(1 for e in emp_lookup.values() if e['pay_rate'] > 0)} with pay rates")
    
    # Build project lookup: workyard_id -> TowerOps project
    projects = db.query(Project).filter(Project.org_id == current_user.org_id).all()
    project_lookup = {}
    for p in projects:
        if p.notes and "workyard_id:" in (p.notes or ""):
            wid = p.notes.split("workyard_id:")[1].split(",")[0].strip()
            project_lookup[wid] = p
    
    logger.warning(f"Project lookup built: {len(project_lookup)} imported projects")
    
    # Process time cards
    synced = 0
    skipped_no_project = 0
    skipped_no_hours = 0
    total_cost = 0.0
    project_costs = {}  # project_id -> total cost
    
    for tc in time_cards:
        # Get hours from time_summary
        summary = tc.get("time_summary_v2", tc.get("time_summary", {}))
        duration_secs = summary.get("duration_secs", 0) or summary.get("duration", 0) or 0
        regular_secs = summary.get("regular_secs", 0) or summary.get("regular", 0) or 0
        ot_secs = summary.get("over_time_secs", 0) or summary.get("over_time", 0) or 0
        
        total_hours = duration_secs / 3600.0
        reg_hours = regular_secs / 3600.0
        ot_hours = ot_secs / 3600.0
        
        if total_hours < 0.01:
            skipped_no_hours += 1
            continue
        
        # Get employee info
        emp_id = str(tc.get("employee_id", ""))
        emp_info = emp_lookup.get(emp_id, {"name": "Unknown", "pay_rate": 0.0})
        pay_rate = emp_info["pay_rate"]
        
        # TNTS Cost Formula (from site budget sheets):
        # Cost = (burden × reg_hrs + burden × 1.5 × OT_hrs) × 1.25 × 1.10 + per_diem
        # 25% = overhead/insurance/workers comp
        # 10% = general & administrative
        # Combined markup = × 1.375
        MARKUP_OVERHEAD = 1.25   # 25% overhead
        MARKUP_GA = 1.10         # 10% G&A
        
        raw_labor = (reg_hours * pay_rate) + (ot_hours * pay_rate * 1.5)
        if raw_labor == 0 and pay_rate == 0:
            # Fallback: use $35/hr default burden rate if no rate found
            raw_labor = (reg_hours * 35.0) + (ot_hours * 35.0 * 1.5)
        
        # Apply 25%/10% markup (per diem added separately, NOT marked up)
        labor_cost = raw_labor * MARKUP_OVERHEAD * MARKUP_GA
        
        # Match to project via cost_allocations
        matched_project = None
        for alloc in tc.get("cost_allocations", []):
            if isinstance(alloc, dict):
                wpid = str(alloc.get("org_project_id", ""))
                if wpid and wpid in project_lookup:
                    matched_project = project_lookup[wpid]
                    break
        
        if not matched_project:
            skipped_no_project += 1
            continue
        
        # Track costs per project
        pid = str(matched_project.id)
        project_costs[pid] = project_costs.get(pid, 0.0) + labor_cost
        total_cost += labor_cost
        synced += 1
    
    # Track per-project: unique crew members and latest activity
    # project_crew[pid] = set of employee burden rates that worked on it
    # project_latest[pid] = most recent time card start timestamp
    project_crew = {}   # pid -> set of burden rates
    project_latest = {} # pid -> latest unix timestamp
    
    # Re-scan time cards for crew and recency info
    five_days_ago_unix = (datetime.utcnow() - timedelta(days=5)).timestamp()
    
    for tc in time_cards:
        emp_id = str(tc.get("employee_id", ""))
        emp_info = emp_lookup.get(emp_id, {"name": "Unknown", "pay_rate": 0.0})
        start_unix = tc.get("start_dt_unix", 0) or 0
        
        for alloc in tc.get("cost_allocations", []):
            if isinstance(alloc, dict):
                wpid = str(alloc.get("org_project_id", ""))
                if wpid and wpid in project_lookup:
                    pid = str(project_lookup[wpid].id)
                    # Track crew rates
                    if pid not in project_crew:
                        project_crew[pid] = set()
                    if emp_info["pay_rate"] > 0:
                        project_crew[pid].add(emp_info["pay_rate"])
                    # Track latest activity
                    if start_unix > project_latest.get(pid, 0):
                        project_latest[pid] = start_unix
    
    # Update projects with costs, budgets, and status
    import uuid as uuid_mod
    MARKUP = 1.25 * 1.10  # 25% overhead + 10% G&A = 1.375
    BUDGET_REG_HRS = 90
    BUDGET_OT_HRS = 20
    TRAVEL_FLAT = 2000.0
    
    updated_projects = 0
    for pid_str, cost in project_costs.items():
        proj = db.query(Project).filter(Project.id == uuid_mod.UUID(pid_str)).first()
        if not proj:
            continue
        
        # Set actual spend
        proj.total_actual = round(cost, 2)
        
        # Auto-calculate default budget if not manually set
        # Formula: for each crew member, (burden × 90 + burden × 1.5 × 20) × 1.375 + $2000 travel
        crew_rates = project_crew.get(pid_str, set())
        if crew_rates and (proj.total_budget or 0) == 0:
            budget = 0.0
            for rate in crew_rates:
                budget += (rate * BUDGET_REG_HRS + rate * 1.5 * BUDGET_OT_HRS) * MARKUP
            budget += TRAVEL_FLAT
            proj.total_budget = round(budget, 2)
        
        # Set status based on RECENT activity (last 5 days)
        latest = project_latest.get(pid_str, 0)
        if latest >= five_days_ago_unix:
            proj.status = "in_progress"
        elif cost > 0:
            # Has historical spend but no recent activity
            proj.status = "active"
        
        updated_projects += 1
    
    db.commit()
    
    active_count = sum(1 for pid in project_latest if project_latest[pid] >= five_days_ago_unix)
    
    logger.warning(f"Sync complete: {synced} entries, {skipped_no_project} no project, {skipped_no_hours} no hours, ${total_cost:.2f} cost, {updated_projects} projects, {active_count} recently active")
    
    return {
        "synced": synced,
        "skipped_no_project": skipped_no_project,
        "skipped_no_hours": skipped_no_hours,
        "total_cost": round(total_cost, 2),
        "projects_updated": updated_projects,
        "recently_active": active_count,
        "employees_with_rates": sum(1 for e in emp_lookup.values() if e["pay_rate"] > 0),
        "days": days,
    }


@router.get("/workyard/employees")
async def fetch_workyard_employees_with_rates(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Fetch all employees from Workyard with pay rates."""
    client = _get_workyard_client(db, current_user.org_id)
    try:
        raw_employees = await client.get_employees()
        normalized = [normalize_workyard_employee(e) for e in raw_employees]
        return {
            "employees": normalized,
            "total": len(normalized),
            "with_rates": sum(1 for e in normalized if e.get("pay_rate")),
        }
    except Exception as e:
        logger.error(f"Failed to fetch Workyard employees: {e}")
        raise HTTPException(status_code=502, detail=f"Workyard API error: {str(e)}")
