import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


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


class WebCrawlerApiError(Exception):
    """Custom exception for WebCrawlerAPI API errors."""

    def __init__(
        self, error_code: str, error_message: str, status_code: Optional[int] = None
    ):
        super().__init__(error_message)
        self.error_code = error_code
        self.error_message = error_message
        self.status_code = status_code

    def __repr__(self) -> str:
        return f"WebCrawlerApiError(error_code={self.error_code!r}, status_code={self.status_code})"


@dataclass
class CrawlResponse:
    """Response from an asynchronous crawl request."""

    id: str


@dataclass
class JobMarkdownResponse:
    """Response from the get_job_markdown endpoint."""

    content_url: str


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
        self.link: Optional[str] = data.get("link")
        self.links: Optional[List[str]] = data.get("links")

        # Optional content URLs based on output_formats / scrape_type
        self.raw_content_url: Optional[str] = data.get("raw_content_url")
        self.cleaned_content_url: Optional[str] = data.get("cleaned_content_url")
        self.markdown_content_url: Optional[str] = data.get("markdown_content_url")

        # Reference to parent job
        self._job = job

        # Cache for content property
        self._content: Optional[str] = None

    @property
    def job(self) -> "Job":
        """Get the parent job this item belongs to."""
        return self._job

    def _fetch_content_url(self, url: Optional[str]) -> Optional[str]:
        """Fetch text content from a URL. Returns None if url is None."""
        if not url:
            return None
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _resolve_content_url(self) -> Optional[str]:
        """
        Resolve the content URL based on output_formats (priority: markdown > cleaned > html),
        falling back to scrape_type for backward compatibility.
        """
        job = self._job
        if job.output_formats:
            priority = ["markdown", "cleaned", "html"]
            for fmt in priority:
                if fmt in job.output_formats:
                    if fmt == "markdown":
                        return self.markdown_content_url
                    elif fmt == "cleaned":
                        return self.cleaned_content_url
                    elif fmt == "html":
                        return self.raw_content_url
            return None
        # Fall back to scrape_type for backward compatibility
        if job.scrape_type == "html":
            return self.raw_content_url
        elif job.scrape_type == "cleaned":
            return self.cleaned_content_url
        elif job.scrape_type == "markdown":
            return self.markdown_content_url
        return None

    def get_content(self) -> Optional[str]:
        """
        Fetch content in the highest-priority format (markdown > cleaned > html).
        Returns None if either the job or item status is not 'done'.
        """
        if self._job.status != "done" or self.status != "done":
            return None
        return self._fetch_content_url(self._resolve_content_url())

    def get_markdown(self) -> Optional[str]:
        """Fetch markdown content for this item."""
        return self._fetch_content_url(self.markdown_content_url)

    def get_cleaned(self) -> Optional[str]:
        """Fetch cleaned HTML content for this item."""
        return self._fetch_content_url(self.cleaned_content_url)

    def get_html(self) -> Optional[str]:
        """Fetch raw HTML content for this item."""
        return self._fetch_content_url(self.raw_content_url)

    @property
    def content(self) -> Optional[str]:
        """
        Get the content of the crawled page based on the job's output_formats / scrape_type.
        Requires both job status and item status to be 'done'. Result is cached.

        Returns:
            Optional[str]: The content of the page, or None if not available or not done.

        Raises:
            requests.exceptions.RequestException: If the content request fails
        """
        if self._job.status != "done" or self.status != "done":
            return None

        # Return cached content if available
        if self._content is not None:
            return self._content

        self._content = self._fetch_content_url(self._resolve_content_url())
        return self._content


class Job:
    """Represents a crawling job."""

    TERMINAL_STATUSES = {"done", "error", "cancelled"}

    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.org_id: str = data["org_id"]
        self.url: str = data["url"]
        self.status: str = data["status"]
        self.scrape_type: Optional[str] = data.get("scrape_type")
        self.output_formats: Optional[List[str]] = data.get("output_formats")
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
