from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import responses

from webcrawlerapi.models import (
    Action,
    CrawlResponse,
    Job,
    JobItem,
    ScrapeId,
    ScrapeResponse,
    ScrapeResponseError,
    UploadS3Action,
    parse_datetime,
)


class TestParseDatetime:
    """Test suite for datetime parsing utility."""

    def test_parse_datetime_with_z_timezone(self):
        """Test parsing datetime with Z timezone."""
        dt_str = "2023-01-15T14:30:45.123456Z"
        result = parse_datetime(dt_str)

        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45
        assert result.microsecond == 123456

    def test_parse_datetime_with_offset_timezone(self):
        """Test parsing datetime with offset timezone."""
        dt_str = "2023-01-15T14:30:45.123+02:00"
        result = parse_datetime(dt_str)

        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_parse_datetime_short_microseconds(self):
        """Test parsing datetime with short microseconds (padding)."""
        dt_str = "2023-01-15T14:30:45.123Z"
        result = parse_datetime(dt_str)

        assert result.microsecond == 123000  # Should be padded

    def test_parse_datetime_long_microseconds(self):
        """Test parsing datetime with long microseconds (truncation)."""
        dt_str = "2023-01-15T14:30:45.1234567890Z"
        result = parse_datetime(dt_str)

        assert result.microsecond == 123456  # Should be truncated

    def test_parse_datetime_no_microseconds(self):
        """Test parsing datetime without microseconds."""
        dt_str = "2023-01-15T14:30:45Z"
        result = parse_datetime(dt_str)

        assert isinstance(result, datetime)
        assert result.microsecond == 0


class TestDataclassModels:
    """Test suite for simple dataclass models."""

    def test_crawl_response(self):
        """Test CrawlResponse dataclass."""
        response = CrawlResponse(id="crawl-123")
        assert response.id == "crawl-123"

    def test_scrape_id(self):
        """Test ScrapeId dataclass."""
        scrape_id = ScrapeId(id="scrape-456")
        assert scrape_id.id == "scrape-456"

    def test_scrape_response_minimal(self):
        """Test ScrapeResponse with minimal data."""
        response = ScrapeResponse(success=True)
        assert response.success is True
        assert response.status is None
        assert response.markdown is None
        assert response.page_status_code == 0

    def test_scrape_response_full(self):
        """Test ScrapeResponse with full data."""
        response = ScrapeResponse(
            success=True,
            status="done",
            markdown="# Test",
            cleaned_content="Test",
            raw_content="<h1>Test</h1>",
            page_status_code=200,
            page_title="Test Page",
            structured_data={"title": "Test"},
        )

        assert response.success is True
        assert response.status == "done"
        assert response.markdown == "# Test"
        assert response.cleaned_content == "Test"
        assert response.raw_content == "<h1>Test</h1>"
        assert response.page_status_code == 200
        assert response.page_title == "Test Page"
        assert response.structured_data == {"title": "Test"}

    def test_scrape_response_error(self):
        """Test ScrapeResponseError dataclass."""
        error = ScrapeResponseError(
            success=False,
            error_code="TIMEOUT",
            error_message="Request timed out",
            status="error",
        )

        assert error.success is False
        assert error.error_code == "TIMEOUT"
        assert error.error_message == "Request timed out"
        assert error.status == "error"

    def test_action_base_class(self):
        """Test Action base class."""
        action = Action(type="custom")
        assert action.type == "custom"

    def test_upload_s3_action(self):
        """Test UploadS3Action with all parameters."""
        action = UploadS3Action(
            path="uploads/",
            access_key_id="AKIATEST",
            secret_access_key="secret123",
            bucket="my-bucket",
            endpoint="https://s3.custom.com",
        )

        assert action.type == "upload_s3"
        assert action.path == "uploads/"
        assert action.access_key_id == "AKIATEST"
        assert action.secret_access_key == "secret123"
        assert action.bucket == "my-bucket"
        assert action.endpoint == "https://s3.custom.com"

    def test_upload_s3_action_no_endpoint(self):
        """Test UploadS3Action without endpoint."""
        action = UploadS3Action(
            path="uploads/",
            access_key_id="AKIATEST",
            secret_access_key="secret123",
            bucket="my-bucket",
        )

        assert action.endpoint is None


class TestJobItem:
    """Test suite for JobItem model."""

    @pytest.fixture
    def mock_job(self):
        """Create a mock job for testing."""
        job_data = {
            "id": "job-123",
            "org_id": "org-456",
            "url": "https://example.com",
            "status": "done",
            "scrape_type": "markdown",
            "items_limit": 10,
            "allow_subdomains": False,
            "created_at": "2023-01-01T12:00:00.000Z",
            "updated_at": "2023-01-01T12:30:00.000Z",
            "job_items": [],
        }
        return Job(job_data)

    @pytest.fixture
    def job_item_data(self):
        """Mock job item data."""
        return {
            "id": "item-123",
            "job_id": "job-456",
            "original_url": "https://example.com/page1",
            "page_status_code": 200,
            "status": "done",
            "title": "Test Page",
            "created_at": "2023-01-01T12:00:00.000Z",
            "updated_at": "2023-01-01T12:15:00.000Z",
            "cost": 1,
            "referred_url": "https://example.com",
            "raw_content_url": "https://storage.test.com/raw.html",
            "cleaned_content_url": "https://storage.test.com/cleaned.txt",
            "markdown_content_url": "https://storage.test.com/markdown.md",
        }

    def test_job_item_initialization(self, job_item_data, mock_job):
        """Test JobItem initialization."""
        item = JobItem(job_item_data, mock_job)

        assert item.id == "item-123"
        assert item.job_id == "job-456"
        assert item.original_url == "https://example.com/page1"
        assert item.page_status_code == 200
        assert item.status == "done"
        assert item.title == "Test Page"
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
        assert item.cost == 1
        assert item.referred_url == "https://example.com"
        assert item.job is mock_job

    def test_job_item_optional_fields(self, mock_job):
        """Test JobItem with minimal required fields."""
        minimal_data = {
            "id": "item-123",
            "job_id": "job-456",
            "original_url": "https://example.com/page1",
            "page_status_code": 200,
            "status": "done",
            "title": "Test Page",
            "created_at": "2023-01-01T12:00:00.000Z",
            "updated_at": "2023-01-01T12:15:00.000Z",
        }

        item = JobItem(minimal_data, mock_job)

        assert item.cost == 0  # Default value
        assert item.referred_url is None
        assert item.last_error is None
        assert item.error_code is None

    @responses.activate
    def test_job_item_content_markdown(self, job_item_data, mock_job):
        """Test JobItem content property for markdown scrape type."""
        mock_job.scrape_type = "markdown"

        responses.add(
            responses.GET,
            "https://storage.test.com/markdown.md",
            body="# Test Content\n\nThis is test content.",
            status=200,
        )

        item = JobItem(job_item_data, mock_job)
        content = item.content

        assert content == "# Test Content\n\nThis is test content."
        # Test caching - second call should return cached content
        assert item.content == content

    @responses.activate
    def test_job_item_content_html(self, job_item_data, mock_job):
        """Test JobItem content property for html scrape type."""
        mock_job.scrape_type = "html"

        responses.add(
            responses.GET,
            "https://storage.test.com/raw.html",
            body="<h1>Test Content</h1>",
            status=200,
        )

        item = JobItem(job_item_data, mock_job)
        content = item.content

        assert content == "<h1>Test Content</h1>"

    @responses.activate
    def test_job_item_content_cleaned(self, job_item_data, mock_job):
        """Test JobItem content property for cleaned scrape type."""
        mock_job.scrape_type = "cleaned"

        responses.add(
            responses.GET,
            "https://storage.test.com/cleaned.txt",
            body="Test Content",
            status=200,
        )

        item = JobItem(job_item_data, mock_job)
        content = item.content

        assert content == "Test Content"

    def test_job_item_content_not_done(self, job_item_data, mock_job):
        """Test JobItem content returns None when status is not done."""
        job_item_data["status"] = "in_progress"
        item = JobItem(job_item_data, mock_job)

        assert item.content is None

    def test_job_item_content_no_url(self, job_item_data, mock_job):
        """Test JobItem content returns None when no content URL available."""
        job_item_data["markdown_content_url"] = None
        mock_job.scrape_type = "markdown"

        item = JobItem(job_item_data, mock_job)

        assert item.content is None


class TestJob:
    """Test suite for Job model."""

    @pytest.fixture
    def job_data(self):
        """Mock job data for testing."""
        return {
            "id": "job-123",
            "org_id": "org-456",
            "url": "https://example.com",
            "status": "done",
            "scrape_type": "markdown",
            "items_limit": 10,
            "allow_subdomains": True,
            "created_at": "2023-01-01T12:00:00.000Z",
            "updated_at": "2023-01-01T12:30:00.000Z",
            "finished_at": "2023-01-01T12:30:00.000Z",
            "webhook_url": "https://webhook.example.com",
            "webhook_status": "success",
            "recommended_pull_delay_ms": 5000,
            "whitelist_regexp": ".*\\.example\\.com.*",
            "blacklist_regexp": ".*\\.ads\\..*",
            "job_items": [
                {
                    "id": "item-1",
                    "job_id": "job-123",
                    "original_url": "https://example.com/page1",
                    "page_status_code": 200,
                    "status": "done",
                    "title": "Page 1",
                    "created_at": "2023-01-01T12:00:00.000Z",
                    "updated_at": "2023-01-01T12:15:00.000Z",
                    "cost": 1,
                },
                {
                    "id": "item-2",
                    "job_id": "job-123",
                    "original_url": "https://example.com/page2",
                    "page_status_code": 200,
                    "status": "done",
                    "title": "Page 2",
                    "created_at": "2023-01-01T12:05:00.000Z",
                    "updated_at": "2023-01-01T12:20:00.000Z",
                    "cost": 1,
                },
            ],
        }

    def test_job_initialization(self, job_data):
        """Test Job initialization with full data."""
        job = Job(job_data)

        assert job.id == "job-123"
        assert job.org_id == "org-456"
        assert job.url == "https://example.com"
        assert job.status == "done"
        assert job.scrape_type == "markdown"
        assert job.items_limit == 10
        assert job.allow_subdomains is True
        assert isinstance(job.created_at, datetime)
        assert isinstance(job.updated_at, datetime)
        assert isinstance(job.finished_at, datetime)
        assert job.webhook_url == "https://webhook.example.com"
        assert job.webhook_status == "success"
        assert job.recommended_pull_delay_ms == 5000
        assert job.whitelist_regexp == ".*\\.example\\.com.*"
        assert job.blacklist_regexp == ".*\\.ads\\..*"
        assert len(job.job_items) == 2

        # Test that job items have reference to parent job
        for item in job.job_items:
            assert isinstance(item, JobItem)
            assert item.job is job

    def test_job_minimal_data(self):
        """Test Job initialization with minimal required data."""
        minimal_data = {
            "id": "job-123",
            "org_id": "org-456",
            "url": "https://example.com",
            "status": "in_progress",
            "scrape_type": "markdown",
            "items_limit": 10,
            "created_at": "2023-01-01T12:00:00.000Z",
            "updated_at": "2023-01-01T12:30:00.000Z",
            "recommended_pull_delay_ms": 0,
        }

        job = Job(minimal_data)

        assert job.id == "job-123"
        assert job.allow_subdomains is False  # Default value
        assert job.finished_at is None
        assert job.webhook_url is None
        assert job.webhook_status is None
        assert job.webhook_error is None
        assert job.whitelist_regexp is None
        assert job.blacklist_regexp is None
        assert len(job.job_items) == 0

    def test_job_is_terminal_done(self, job_data):
        """Test is_terminal property for done status."""
        job_data["status"] = "done"
        job = Job(job_data)
        assert job.is_terminal is True

    def test_job_is_terminal_error(self, job_data):
        """Test is_terminal property for error status."""
        job_data["status"] = "error"
        job = Job(job_data)
        assert job.is_terminal is True

    def test_job_is_terminal_cancelled(self, job_data):
        """Test is_terminal property for cancelled status."""
        job_data["status"] = "cancelled"
        job = Job(job_data)
        assert job.is_terminal is True

    def test_job_is_not_terminal(self, job_data):
        """Test is_terminal property for non-terminal statuses."""
        non_terminal_statuses = ["in_progress", "pending", "starting"]

        for status in non_terminal_statuses:
            job_data["status"] = status
            job = Job(job_data)
            assert job.is_terminal is False

    def test_job_terminal_statuses_constant(self):
        """Test that TERMINAL_STATUSES constant is correctly defined."""
        assert Job.TERMINAL_STATUSES == {"done", "error", "cancelled"}
