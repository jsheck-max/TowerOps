import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

WORKYARD_BASE_URL = "https://api.workyard.com"


class WorkyardClient:
    """Client for Workyard REST API."""

    def __init__(self, api_key: str, org_id: str = "20752"):
        self.api_key = api_key
        self.org_id = org_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make GET request to Workyard API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{WORKYARD_BASE_URL}{endpoint}"
            logger.info(f"Workyard GET {url} params={params}")
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_projects(self) -> list[dict]:
        """Fetch all projects/jobs from Workyard."""
        try:
            # Try /v1/projects first (common pattern)
            data = await self._get("/v1/projects", {"org_id": self.org_id})
            projects = data.get("data", data.get("projects", data.get("results", [])))
            if isinstance(projects, list):
                return projects
            return [projects] if projects else []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Fall back to /v1/jobs
                try:
                    data = await self._get("/v1/jobs", {"org_id": self.org_id})
                    return data.get("data", data.get("jobs", data.get("results", [])))
                except Exception:
                    pass
            logger.error(f"Workyard API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Workyard connection error: {e}")
            raise

    async def get_employees(self) -> list[dict]:
        """Fetch all employees/crew members from Workyard."""
        try:
            data = await self._get("/v1/employees", {"org_id": self.org_id})
            return data.get("data", data.get("employees", data.get("results", [])))
        except Exception as e:
            logger.error(f"Workyard employees error: {e}")
            raise

    async def get_time_entries(self, start_date: str, end_date: str, project_id: str | None = None) -> list[dict]:
        """Fetch time entries from Workyard."""
        params = {
            "org_id": self.org_id,
            "start_date": start_date,
            "end_date": end_date,
        }
        if project_id:
            params["project_id"] = project_id
        try:
            data = await self._get("/v1/time_entries", params)
            return data.get("data", data.get("time_entries", data.get("results", [])))
        except Exception as e:
            logger.error(f"Workyard time entries error: {e}")
            raise

    async def test_connection(self) -> dict:
        """Test the API connection."""
        try:
            # Simple request to verify credentials
            data = await self._get("/v1/projects", {"org_id": self.org_id, "limit": 1})
            return {"status": "connected", "message": "Workyard API connection successful"}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "message": f"API returned {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def normalize_workyard_project(raw: dict) -> dict:
    """Normalize a Workyard project/job into TowerOps format.
    
    Workyard may return fields under different names depending on the endpoint.
    This function handles the most common field mappings.
    """
    # Try multiple possible field names for each value
    def pick(*keys, default=None):
        for k in keys:
            val = raw.get(k)
            if val is not None and val != "":
                return val
        return default

    # Parse address components
    address = pick("address", "location", "site_address", "job_address", default="")
    state = pick("state", "address_state", default="")
    city = pick("city", "address_city", "market", default="")

    # If address is a dict (some APIs nest it)
    if isinstance(address, dict):
        state = address.get("state", state)
        city = address.get("city", city)
        address = address.get("full_address", address.get("street", ""))

    return {
        "workyard_id": str(pick("id", "project_id", "job_id", default="")),
        "site_name": pick("name", "project_name", "job_name", "title", default="Unknown"),
        "site_number": pick("code", "project_code", "job_code", "number", "external_id", default=""),
        "address": address,
        "state": state,
        "market": city,
        "status": pick("status", default="active"),
        "customer_name": pick("customer", "customer_name", "client", "client_name", default=""),
        "created_at": pick("created_at", "created", "date_created", default=""),
        "cost_codes": pick("cost_codes", "codes", default=[]),
        "raw": raw,  # Include full raw data so frontend can display anything
    }


def normalize_workyard_employee(raw: dict) -> dict:
    """Normalize a Workyard employee into TowerOps format."""
    def pick(*keys, default=None):
        for k in keys:
            val = raw.get(k)
            if val is not None and val != "":
                return val
        return default

    return {
        "workyard_id": str(pick("id", "employee_id", "user_id", default="")),
        "name": pick("name", "full_name", "display_name", default=""),
        "first_name": pick("first_name", default=""),
        "last_name": pick("last_name", default=""),
        "role": pick("role", "job_title", "position", default="technician"),
        "email": pick("email", default=""),
        "phone": pick("phone", "phone_number", default=""),
        "is_active": pick("is_active", "active", default=True),
        "crew": pick("crew", "crew_name", "team", "group", default=""),
    }
