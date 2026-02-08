import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


def parse_datetime(datetime_str: str) -> datetime:
    """
    Parse datetime string from API response, handling various microsecond formats.

    Args:
        datetime_str (str): Datetime string from API

    Returns:
        datetime: Parsed datetime object
    """
    # Replace 'Z' with '+00:00' for timezone
    datetime_str = datetime_str.replace("Z", "+00:00")

    # Handle microseconds - pad to 6 digits or remove if present
    # Pattern matches: YYYY-MM-DDTHH:MM:SS.microseconds followed by timezone or end
    pattern = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d+)(.*)"
    match = re.match(pattern, datetime_str)

    if match:
        base_time, microseconds, timezone_part = match.groups()
        # Pad microseconds to 6 digits or truncate if longer
        microseconds = microseconds.ljust(6, "0")[:6]
        datetime_str = f"{base_time}.{microseconds}{timezone_part}"

    return datetime.fromisoformat(datetime_str)


@dataclass
class CrawlResponse:
    """Response from an asynchronous crawl request."""

    id: str


@dataclass
class ScrapeId:
    """Response from an asynchronous scrape request."""

    id: str


@dataclass
class ScrapeResponse:
    """Response from a scrape request."""

    success: bool
    status: Optional[str] = None
    markdown: Optional[str] = None
    cleaned_content: Optional[str] = None
    raw_content: Optional[str] = None
    page_status_code: int = 0
    page_title: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    links: Optional[List[str]] = None


@dataclass
class ScrapeResponseError:
    """Error response from a scrape request."""

    success: bool
    error_code: str
    error_message: str
    status: Optional[str] = None


@dataclass
class Action:
    """Base class for actions that can be performed during crawling."""

    type: str


@dataclass
class UploadS3Action(Action):
    """Action to upload crawled content to S3."""

    path: str
    access_key_id: str
    secret_access_key: str
    bucket: str
    endpoint: Optional[str] = None

    def __init__(
        self,
        path: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        endpoint: Optional[str] = None,
    ):
        super().__init__(type="upload_s3")
        self.path = path
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.bucket = bucket
        self.endpoint = endpoint


class JobItem:
    """Represents a single crawled page item in a job."""

    def __init__(self, data: Dict[str, Any], job: "Job"):
        """
        Initialize a JobItem.

        Args:
            data (Dict[str, Any]): The raw item data from the API
            job (Job): The parent job this item belongs to
        """
        self.id: str = data["id"]
        self.job_id: str = data["job_id"]
        self.original_url: str = data["original_url"]
        self.page_status_code: int = data["page_status_code"]
        self.status: str = data["status"]
        self.title: str = data["title"]
        self.created_at: datetime = parse_datetime(data["created_at"])
        self.updated_at: datetime = parse_datetime(data["updated_at"])
        self.cost: int = data.get("cost", 0)
        self.referred_url: Optional[str] = data.get("referred_url")
        self.last_error: Optional[str] = data.get("last_error")
        self.error_code: Optional[str] = data.get("error_code")
        self.depth: Optional[int] = data.get("depth")

        # Optional content URLs based on scrape_type
        self.raw_content_url: Optional[str] = data.get("raw_content_url")
        self.cleaned_content_url: Optional[str] = data.get("cleaned_content_url")
        self.markdown_content_url: Optional[str] = data.get("markdown_content_url")

        # Reference to parent job
        self._job = job

        # Cache for content
        self._content: Optional[str] = None

    @property
    def job(self) -> "Job":
        """Get the parent job this item belongs to."""
        return self._job

    @property
    def content(self) -> Optional[str]:
        """
        Get the content of the crawled page based on the job's scrape_type.
        The content is fetched from the appropriate URL (raw, cleaned, or markdown)
        and cached for subsequent access.

        Returns:
            Optional[str]: The content of the page, or None if content is not available
                         or if the item's status is not "done"

        Raises:
            requests.exceptions.RequestException: If the content request fails
        """
        # Return None if item is not done
        if self.status != "done":
            return None

        # Return cached content if available
        if self._content is not None:
            return self._content

        # Get the appropriate content URL based on scrape_type
        content_url = None
        if self.job.scrape_type == "html":
            content_url = self.raw_content_url
        elif self.job.scrape_type == "cleaned":
            content_url = self.cleaned_content_url
        elif self.job.scrape_type == "markdown":
            content_url = self.markdown_content_url

        # If no URL is available, return None
        if not content_url:
            return None

        # Fetch and cache the content
        import requests

        response = requests.get(content_url)
        response.raise_for_status()
        self._content = response.text
        return self._content


class Job:
    """Represents a crawling job."""

    TERMINAL_STATUSES = {"done", "error", "cancelled"}

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.org_id: str = data["org_id"]
        self.url: str = data["url"]
        self.status: str = data["status"]
        self.scrape_type: str = data["scrape_type"]
        self.whitelist_regexp: Optional[str] = data.get("whitelist_regexp")
        self.blacklist_regexp: Optional[str] = data.get("blacklist_regexp")
        self.items_limit: int = data["items_limit"]
        self.max_depth: Optional[int] = data.get("max_depth")
        self.created_at: datetime = parse_datetime(data["created_at"])
        self.updated_at: datetime = parse_datetime(data["updated_at"])
        self.webhook_url: Optional[str] = data.get("webhook_url")
        self.recommended_pull_delay_ms: int = data.get("recommended_pull_delay_ms", 0)

        # Optional fields
        self.finished_at: Optional[datetime] = None
        if data.get("finished_at"):
            self.finished_at = parse_datetime(data["finished_at"])

        self.webhook_status: Optional[str] = data.get("webhook_status")
        self.webhook_error: Optional[str] = data.get("webhook_error")

        # Parse job items with reference to self
        self.job_items: List[JobItem] = [
            JobItem(item, self) for item in data.get("job_items", [])
        ]

    @property
    def is_terminal(self) -> bool:
        """Check if the job is in a terminal state (done, error, or cancelled)."""
        return self.status in self.TERMINAL_STATUSES
