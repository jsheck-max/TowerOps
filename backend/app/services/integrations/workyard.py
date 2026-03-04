import httpx
import logging

logger = logging.getLogger(__name__)

WORKYARD_BASE_URL = "https://api.workyard.com"


class WorkyardClient:
    """Client for Workyard REST API.
    
    Workyard API structure:
    - GET /orgs -> list orgs, get org_id
    - GET /orgs/{org_id}/projects -> list projects
    - GET /orgs/{org_id}/employees.v2?status=eq:active -> list employees
    - GET /orgs/{org_id}/time_cards?clock_in=gte:{start}&clock_in=lte:{end} -> time cards
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._org_id: str | None = None

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        """Make GET request to Workyard API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{WORKYARD_BASE_URL}{path}"
            logger.info(f"Workyard GET {url}")
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_org_id(self) -> str:
        """Get the organization ID from Workyard."""
        if self._org_id:
            return self._org_id
        data = await self._get("/orgs")
        if isinstance(data, list) and len(data) > 0:
            self._org_id = str(data[0]["id"])
        elif isinstance(data, dict):
            orgs = data.get("data", [])
            if orgs:
                self._org_id = str(orgs[0]["id"])
        if not self._org_id:
            raise Exception("Could not find Workyard organization")
        logger.info(f"Workyard org_id: {self._org_id}")
        return self._org_id

    async def get_projects(self) -> list[dict]:
        """Fetch all projects from Workyard."""
        org_id = await self.get_org_id()
        try:
            data = await self._get(f"/orgs/{org_id}/projects", None)
            if isinstance(data, list):
                return data
            return data.get("data", data.get("projects", []))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Try alternative endpoint
                try:
                    data = await self._get(f"/orgs/{org_id}/jobs", None)
                    if isinstance(data, list):
                        return data
                    return data.get("data", [])
                except Exception:
                    pass
            raise

    async def get_employees(self) -> list[dict]:
        """Fetch active employees from Workyard."""
        org_id = await self.get_org_id()
        data = await self._get(f"/orgs/{org_id}/employees.v2", {"status": "eq:active"})
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def get_time_cards(self, start_date: str, end_date: str) -> list[dict]:
        """Fetch time cards from Workyard for a date range."""
        org_id = await self.get_org_id()
        params = {
            "clock_in": f"gte:{start_date}",
            "limit": 500,
        }
        data = await self._get(f"/orgs/{org_id}/time_cards", params)
        if isinstance(data, list):
            return data
        return data.get("data", [])

    async def test_connection(self) -> dict:
        """Test the API connection by fetching org info."""
        try:
            org_id = await self.get_org_id()
            return {"status": "connected", "message": f"Connected to Workyard (org {org_id})"}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "message": f"API returned {e.response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def normalize_workyard_project(raw: dict) -> dict:
    """Normalize a Workyard project into TowerOps format."""
    def pick(*keys, default=None):
        for k in keys:
            val = raw.get(k)
            if val is not None and val != "":
                return val
        return default

    # Handle address - could be string or nested object
    address_raw = pick("address", "location", "site_address", default="")
    state = pick("state", default="")
    city = pick("city", "market", default="")

    if isinstance(address_raw, dict):
        state = address_raw.get("state", address_raw.get("region", state))
        city = address_raw.get("city", city)
        address_str = address_raw.get("full_address", address_raw.get("street", address_raw.get("line1", "")))
    else:
        address_str = str(address_raw) if address_raw else ""

    return {
        "workyard_id": str(pick("id", "project_id", default="")),
        "site_name": pick("name", "project_name", "title", default="Unknown"),
        "site_number": pick("code", "number", "external_id", "reference", default=""),
        "address": address_str,
        "state": state,
        "market": city,
        "status": pick("status", default="active"),
        "customer_name": pick("customer", "customer_name", "client", "client_name", default=""),
        "created_at": pick("created_at", "created", default=""),
        "raw": raw,
    }


def normalize_workyard_employee(raw: dict) -> dict:
    """Normalize a Workyard employee into TowerOps format."""
    def pick(*keys, default=None):
        for k in keys:
            val = raw.get(k)
            if val is not None and val != "":
                return val
        return default

    first = pick("first_name", default="")
    last = pick("last_name", default="")
    full = pick("name", "full_name", "display_name", default="")
    if not full and (first or last):
        full = f"{first} {last}".strip()

    return {
        "workyard_id": str(pick("id", "employee_id", default="")),
        "name": full,
        "first_name": first,
        "last_name": last,
        "role": pick("role", "job_title", "position", default="technician"),
        "email": pick("email", default=""),
        "phone": pick("phone", "mobile_phone", "phone_number", default=""),
        "is_active": pick("is_active", "active", default=True),
        "crew": pick("crew", "crew_name", "team", "group", default=""),
    }
