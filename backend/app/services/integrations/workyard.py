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
    - GET /orgs/{org_id}/time_cards?clock_in=gte:{start} -> time cards
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._org_id: str | None = None

    async def _get_raw(self, url: str) -> dict | list:
        """Make GET request to a full URL."""
        async with httpx.AsyncClient(timeout=45.0) as client:
            logger.warning(f"Workyard GET {url}")
            response = await client.get(url, headers=self.headers)
            logger.warning(f"Workyard response: {response.status_code} len={len(response.text)}")
            response.raise_for_status()
            return response.json()

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        """Make GET request to Workyard API."""
        url = f"{WORKYARD_BASE_URL}{path}"
        if params:
            # Build query string manually to preserve special chars like gte:
            parts = []
            for k, v in params.items():
                parts.append(f"{k}={v}")
            url = url + "?" + "&".join(parts)
        return await self._get_raw(url)

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
        logger.warning(f"Workyard org_id: {self._org_id}")
        return self._org_id

    async def _get_paginated(self, path: str, extra_params: dict | None = None) -> list[dict]:
        """Fetch all pages from a paginated Workyard endpoint."""
        all_results = []
        page = 1
        while True:
            p = dict(extra_params or {})
            p["page"] = str(page)
            data = await self._get(path, p)
            if isinstance(data, list):
                if not data:
                    break
                all_results.extend(data)
                if len(data) < 50:
                    break
            elif isinstance(data, dict):
                items = data.get("data", data.get("projects", data.get("results", [])))
                if not items:
                    break
                all_results.extend(items)
                meta = data.get("meta", {})
                last_page = meta.get("last_page", meta.get("total_pages", 0))
                if last_page and page >= last_page:
                    break
                if len(items) < 50:
                    break
            else:
                break
            page += 1
            if page > 20:
                break
        logger.warning(f"Workyard paginated {path}: {len(all_results)} total results")
        return all_results

    async def get_projects(self) -> list[dict]:
        """Fetch ALL projects from Workyard with pagination."""
        org_id = await self.get_org_id()
        try:
            return await self._get_paginated(f"/orgs/{org_id}/projects")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                try:
                    return await self._get_paginated(f"/orgs/{org_id}/jobs")
                except Exception:
                    pass
            raise

    async def get_employees(self) -> list[dict]:
        """Fetch active employees from Workyard (paginated)."""
        org_id = await self.get_org_id()
        return await self._get_paginated(f"/orgs/{org_id}/employees.v2", {"status": "eq:active"})

    async def get_time_cards(self, start_date: str, end_date: str) -> list[dict]:
        """Fetch time cards from Workyard for a date range (paginated).
        
        Uses Workyard filter syntax: clock_in=gte:{date}
        """
        org_id = await self.get_org_id()
        params = {
            "clock_in": f"gte:{start_date}",
        }
        logger.warning(f"Fetching time cards from {start_date} to {end_date}")
        try:
            results = await self._get_paginated(f"/orgs/{org_id}/time_cards", params)
            logger.warning(f"Got {len(results)} time cards")
            return results
        except httpx.HTTPStatusError as e:
            logger.warning(f"Time cards endpoint error: {e.response.status_code} - {e.response.text[:300]}")
            # Try without filter
            try:
                logger.warning("Retrying time_cards without date filter...")
                results = await self._get_paginated(f"/orgs/{org_id}/time_cards")
                logger.warning(f"Got {len(results)} time cards (unfiltered)")
                return results
            except Exception as e2:
                logger.warning(f"Time cards unfiltered also failed: {e2}")
                raise
        except Exception as e:
            logger.warning(f"Time cards fetch error: {e}")
            raise

    async def get_cost_codes(self) -> list[dict]:
        """Fetch cost codes from Workyard."""
        org_id = await self.get_org_id()
        try:
            return await self._get_paginated(f"/orgs/{org_id}/cost_codes")
        except Exception as e:
            logger.warning(f"Cost codes fetch error: {e}")
            return []

    async def test_connection(self) -> dict:
        """Test the API connection by fetching org info."""
        try:
            org_id = await self.get_org_id()
            return {"status": "connected", "message": f"Connected to Workyard (org {org_id})"}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "message": f"API returned {e.response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


def _to_str(val) -> str:
    """Safely convert any value to a string. Handles nested objects."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return str(val.get("name", val.get("title", val.get("label", ""))))
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return str(val)


def normalize_workyard_project(raw: dict) -> dict:
    """Normalize a Workyard project into TowerOps format."""
    def pick(*keys, default=None):
        for k in keys:
            val = raw.get(k)
            if val is not None and val != "":
                return val
        return default

    address_raw = pick("address", "location", "site_address", default="")
    state = _to_str(pick("state", default=""))
    city = _to_str(pick("city", "market", default=""))

    if isinstance(address_raw, dict):
        state = address_raw.get("state", address_raw.get("region", state))
        city = address_raw.get("city", city)
        address_str = address_raw.get("full_address", address_raw.get("street", address_raw.get("line1", "")))
    else:
        address_str = str(address_raw) if address_raw else ""

    customer_raw = pick("customer", "customer_name", "client", "client_name", default="")
    customer_name = _to_str(customer_raw)

    return {
        "workyard_id": str(pick("id", "project_id", default="")),
        "site_name": _to_str(pick("name", "project_name", "title", default="Unknown")),
        "site_number": _to_str(pick("code", "number", "external_id", "reference", default="")),
        "address": _to_str(address_str),
        "state": _to_str(state),
        "market": _to_str(city),
        "status": _to_str(pick("status", default="active")),
        "customer_name": customer_name,
        "created_at": _to_str(pick("created_at", "created", default="")),
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

    first = _to_str(pick("first_name", default=""))
    last = _to_str(pick("last_name", default=""))
    full = _to_str(pick("name", "full_name", "display_name", default=""))
    if not full and (first or last):
        full = f"{first} {last}".strip()

    # Pay rate - Workyard stores hourly rate on employee
    pay_rate = pick("pay_rate", "hourly_rate", "rate", "wage", "pay", default=None)
    if isinstance(pay_rate, dict):
        pay_rate = pay_rate.get("amount", pay_rate.get("rate", None))
    try:
        pay_rate = float(pay_rate) if pay_rate else None
    except (ValueError, TypeError):
        pay_rate = None

    return {
        "workyard_id": str(pick("id", "employee_id", default="")),
        "name": _to_str(full),
        "first_name": _to_str(first),
        "last_name": _to_str(last),
        "role": _to_str(pick("role", "job_title", "position", "type", default="technician")),
        "email": _to_str(pick("email", default="")),
        "phone": _to_str(pick("phone", "mobile_phone", "phone_number", default="")),
        "is_active": pick("is_active", "active", default=True),
        "crew": _to_str(pick("crew", "crew_name", "team", "group", default="")),
        "pay_rate": pay_rate,
        "pay_type": _to_str(pick("pay_type", "compensation_type", default="")),
    }
