from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class NormalizedTimeEntry:
    """Universal time entry format that all adapters output."""
    worker_name: str
    worker_external_id: str | None
    project_name: str | None
    project_external_id: str | None
    work_date: date
    clock_in: datetime | None
    clock_out: datetime | None
    hours: float
    overtime_hours: float
    latitude: float | None
    longitude: float | None
    source_platform: str
    source_id: str


class TimeTrackingAdapter(ABC):
    """Base class for all time-tracking platform integrations.

    Each platform (Workyard, Busybusy, ExakTime, ClockShark) gets its own
    adapter that inherits from this class and implements the abstract methods.

    The adapter pattern normalizes data from any source into NormalizedTimeEntry
    objects that the rest of the app can work with uniformly.
    """

    def __init__(self, api_key: str, api_url: str | None = None):
        self.api_key = api_key
        self.api_url = api_url

    @abstractmethod
    async def fetch_time_entries(
        self, start_date: date, end_date: date
    ) -> list[NormalizedTimeEntry]:
        """Fetch and normalize time entries for a date range."""
        ...

    @abstractmethod
    async def fetch_workers(self) -> list[dict]:
        """Fetch worker/employee list from the platform."""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify API credentials are valid."""
        ...
