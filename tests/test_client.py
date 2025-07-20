from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import requests
import responses

from webcrawlerapi.client import WebCrawlerAPI
from webcrawlerapi.models import (
    CrawlResponse,
    Job,
    JobItem,
    ScrapeId,
    ScrapeResponse,
    ScrapeResponseError,
    UploadS3Action,
)


class TestWebCrawlerAPI:
    """Test suite for WebCrawlerAPI client."""

    @pytest.fixture
    def client(self):
        """Create a WebCrawlerAPI client for testing."""
        return WebCrawlerAPI(api_key="test-api-key", base_url="https://api.test.com")

    @pytest.fixture
    def mock_job_data(self):
        """Mock job data for testing."""
        return {
            "id": "job-123",
            "org_id": "org-456",
            "url": "https://example.com",
            "status": "done",
            "scrape_type": "markdown",
            "items_limit": 10,
            "allow_subdomains": False,
            "created_at": "2023-01-01T12:00:00.000Z",
            "updated_at": "2023-01-01T12:30:00.000Z",
            "finished_at": "2023-01-01T12:30:00.000Z",
            "recommended_pull_delay_ms": 5000,
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
                    "markdown_content_url": "https://storage.test.com/content1.md",
                }
            ],
        }

    def test_client_initialization(self):
        """Test client initialization with API key and base URL."""
        client = WebCrawlerAPI("test-key", "https://custom.api.com")
        assert client.api_key == "test-key"
        assert client.base_url == "https://custom.api.com"
        assert client.session.headers["Authorization"] == "Bearer test-key"
        assert client.session.headers["Content-Type"] == "application/json"

    def test_client_initialization_default_url(self):
        """Test client initialization with default base URL."""
        client = WebCrawlerAPI("test-key")
        assert client.base_url == "https://api.webcrawlerapi.com"

    @responses.activate
    def test_crawl_async_success(self, client):
        """Test successful asynchronous crawl request."""
        responses.add(
            responses.POST,
            "https://api.test.com/v1/crawl",
            json={"id": "crawl-123"},
            status=200,
        )

        result = client.crawl_async(
            url="https://example.com",
            scrape_type="markdown",
            items_limit=5,
            allow_subdomains=True,
            respect_robots_txt=True,
        )

        assert isinstance(result, CrawlResponse)
        assert result.id == "crawl-123"

        # Verify request payload
        request = responses.calls[0].request
        import json

        payload = json.loads(request.body)
        assert payload["url"] == "https://example.com"
        assert payload["scrape_type"] == "markdown"
        assert payload["items_limit"] == 5
        assert payload["allow_subdomains"] is True
        assert payload["respect_robots_txt"] is True

    @responses.activate
    def test_crawl_async_with_actions(self, client):
        """Test crawl_async with S3 upload action."""
        responses.add(
            responses.POST,
            "https://api.test.com/v1/crawl",
            json={"id": "crawl-456"},
            status=200,
        )

        s3_action = UploadS3Action(
            path="crawl-results/",
            access_key_id="AKIAEXAMPLE",
            secret_access_key="secret123",
            bucket="my-bucket",
        )

        result = client.crawl_async(url="https://example.com", actions=[s3_action])

        assert result.id == "crawl-456"

        # Verify action in payload
        request = responses.calls[0].request
        import json

        payload = json.loads(request.body)
        assert "actions" in payload
        assert len(payload["actions"]) == 1
        assert payload["actions"][0]["type"] == "upload_s3"
        assert payload["actions"][0]["bucket"] == "my-bucket"

    @responses.activate
    def test_crawl_async_http_error(self, client):
        """Test crawl_async with HTTP error response."""
        responses.add(
            responses.POST,
            "https://api.test.com/v1/crawl",
            json={"error": "Invalid URL"},
            status=400,
        )

        with pytest.raises(requests.exceptions.HTTPError):
            client.crawl_async(url="invalid-url")

    @responses.activate
    def test_get_job_success(self, client, mock_job_data):
        """Test successful job retrieval."""
        responses.add(
            responses.GET,
            "https://api.test.com/v1/job/job-123",
            json=mock_job_data,
            status=200,
        )

        job = client.get_job("job-123")

        assert isinstance(job, Job)
        assert job.id == "job-123"
        assert job.status == "done"
        assert job.scrape_type == "markdown"
        assert len(job.job_items) == 1
        assert job.job_items[0].title == "Page 1"

    @responses.activate
    def test_cancel_job_success(self, client):
        """Test successful job cancellation."""
        responses.add(
            responses.PUT,
            "https://api.test.com/v1/job/job-123/cancel",
            json={"message": "Job cancelled successfully"},
            status=200,
        )

        result = client.cancel_job("job-123")
        assert result["message"] == "Job cancelled successfully"

    @responses.activate
    def test_crawl_with_polling_terminal_state(self, client, mock_job_data):
        """Test crawl method that polls until terminal state."""
        # Mock crawl_async response
        responses.add(
            responses.POST,
            "https://api.test.com/v1/crawl",
            json={"id": "job-123"},
            status=200,
        )

        # Mock get_job response with terminal state
        responses.add(
            responses.GET,
            "https://api.test.com/v1/job/job-123",
            json=mock_job_data,
            status=200,
        )

        with patch("time.sleep") as mock_sleep:
            job = client.crawl(url="https://example.com", max_polls=5)

            assert isinstance(job, Job)
            assert job.id == "job-123"
            assert job.status == "done"
            # Should not sleep since job is already in terminal state
            mock_sleep.assert_not_called()

    @responses.activate
    def test_crawl_with_polling_max_polls_reached(self, client):
        """Test crawl method that reaches max_polls limit."""
        # Mock crawl_async response
        responses.add(
            responses.POST,
            "https://api.test.com/v1/crawl",
            json={"id": "job-123"},
            status=200,
        )

        # Mock get_job responses with non-terminal state
        in_progress_data = {
            "id": "job-123",
            "org_id": "org-456",
            "url": "https://example.com",
            "status": "in_progress",
            "scrape_type": "markdown",
            "items_limit": 10,
            "allow_subdomains": False,
            "created_at": "2023-01-01T12:00:00.000Z",
            "updated_at": "2023-01-01T12:30:00.000Z",
            "recommended_pull_delay_ms": 1000,
            "job_items": [],
        }

        for _ in range(3):
            responses.add(
                responses.GET,
                "https://api.test.com/v1/job/job-123",
                json=in_progress_data,
                status=200,
            )

        with patch("time.sleep") as mock_sleep:
            job = client.crawl(url="https://example.com", max_polls=3)

            assert job.status == "in_progress"
            # Should sleep 3 times (once after each poll)
            assert mock_sleep.call_count == 3
            mock_sleep.assert_called_with(1.0)  # recommended_pull_delay_ms / 1000

    @responses.activate
    def test_scrape_async_success(self, client):
        """Test successful asynchronous scrape request."""
        responses.add(
            responses.POST,
            "https://api.test.com/v2/scrape?async=true",
            json={"id": "scrape-123"},
            status=200,
        )

        result = client.scrape_async(
            url="https://example.com",
            output_format="cleaned",
            clean_selectors=".ads, .footer",
            prompt="Extract main content",
            respect_robots_txt=True,
        )

        assert isinstance(result, ScrapeId)
        assert result.id == "scrape-123"

        # Verify request payload
        request = responses.calls[0].request
        import json

        payload = json.loads(request.body)
        assert payload["url"] == "https://example.com"
        assert payload["output_format"] == "cleaned"
        assert payload["clean_selectors"] == ".ads, .footer"
        assert payload["prompt"] == "Extract main content"
        assert payload["respect_robots_txt"] is True

    @responses.activate
    def test_scrape_async_error_response(self, client):
        """Test scrape_async with error response."""
        responses.add(
            responses.POST,
            "https://api.test.com/v2/scrape?async=true",
            json={"error": "Invalid URL format"},
            status=400,
        )

        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            client.scrape_async(url="invalid-url")

        assert "400" in str(exc_info.value)
        assert "Invalid URL format" in str(exc_info.value)

    @responses.activate
    def test_get_scrape_success_done(self, client):
        """Test get_scrape with successful completion."""
        scrape_data = {
            "status": "done",
            "success": True,
            "markdown": "# Test Content",
            "cleaned_content": "Test Content",
            "raw_content": "<h1>Test Content</h1>",
            "page_status_code": 200,
            "page_title": "Test Page",
            "structured_data": {"title": "Test Page"},
        }

        responses.add(
            responses.GET,
            "https://api.test.com/v2/scrape/scrape-123",
            json=scrape_data,
            status=200,
        )

        result = client.get_scrape("scrape-123")

        assert isinstance(result, ScrapeResponse)
        assert result.status == "done"
        assert result.success is True
        assert result.markdown == "# Test Content"
        assert result.page_title == "Test Page"

    @responses.activate
    def test_get_scrape_error_status(self, client):
        """Test get_scrape with error status."""
        error_data = {
            "status": "error",
            "success": False,
            "error_code": "TIMEOUT",
            "error_message": "Request timed out",
        }

        responses.add(
            responses.GET,
            "https://api.test.com/v2/scrape/scrape-123",
            json=error_data,
            status=200,
        )

        result = client.get_scrape("scrape-123")

        assert isinstance(result, ScrapeResponseError)
        assert result.status == "error"
        assert result.success is False
        assert result.error_code == "TIMEOUT"
        assert result.error_message == "Request timed out"

    @responses.activate
    def test_get_scrape_in_progress(self, client):
        """Test get_scrape with in_progress status."""
        progress_data = {"status": "in_progress", "success": False}

        responses.add(
            responses.GET,
            "https://api.test.com/v2/scrape/scrape-123",
            json=progress_data,
            status=200,
        )

        result = client.get_scrape("scrape-123")

        assert isinstance(result, ScrapeResponse)
        assert result.status == "in_progress"
        assert result.success is False

    @responses.activate
    def test_scrape_with_polling_success(self, client):
        """Test scrape method that polls until completion."""
        # Mock scrape_async response
        responses.add(
            responses.POST,
            "https://api.test.com/v2/scrape?async=true",
            json={"id": "scrape-123"},
            status=200,
        )

        # Mock get_scrape response with done status
        scrape_data = {
            "status": "done",
            "success": True,
            "markdown": "# Scraped Content",
        }

        responses.add(
            responses.GET,
            "https://api.test.com/v2/scrape/scrape-123",
            json=scrape_data,
            status=200,
        )

        with patch("time.sleep") as mock_sleep:
            result = client.scrape(url="https://example.com")

            assert isinstance(result, ScrapeResponse)
            assert result.status == "done"
            assert result.markdown == "# Scraped Content"
            # Should not sleep since scrape is already done
            mock_sleep.assert_not_called()

    @responses.activate
    def test_scrape_with_polling_error(self, client):
        """Test scrape method that polls and gets error."""
        # Mock scrape_async response
        responses.add(
            responses.POST,
            "https://api.test.com/v2/scrape?async=true",
            json={"id": "scrape-123"},
            status=200,
        )

        # Mock get_scrape response with error
        error_data = {
            "status": "error",
            "success": False,
            "error_code": "FETCH_ERROR",
            "error_message": "Failed to fetch page",
        }

        responses.add(
            responses.GET,
            "https://api.test.com/v2/scrape/scrape-123",
            json=error_data,
            status=200,
        )

        with patch("time.sleep") as mock_sleep:
            result = client.scrape(url="https://example.com")

            assert isinstance(result, ScrapeResponseError)
            assert result.error_code == "FETCH_ERROR"
            # Should not sleep since error is immediate
            mock_sleep.assert_not_called()

    @responses.activate
    def test_scrape_with_polling_max_polls(self, client):
        """Test scrape method that reaches max_polls."""
        # Mock scrape_async response
        responses.add(
            responses.POST,
            "https://api.test.com/v2/scrape?async=true",
            json={"id": "scrape-123"},
            status=200,
        )

        # Mock get_scrape responses with in_progress status
        progress_data = {"status": "in_progress", "success": False}

        for _ in range(3):
            responses.add(
                responses.GET,
                "https://api.test.com/v2/scrape/scrape-123",
                json=progress_data,
                status=200,
            )

        with patch("time.sleep") as mock_sleep:
            result = client.scrape(url="https://example.com", max_polls=3)

            assert isinstance(result, ScrapeResponse)
            assert result.status == "in_progress"
            # Should sleep 3 times (once after each poll)
            assert mock_sleep.call_count == 3
            mock_sleep.assert_called_with(5)  # DEFAULT_POLL_DELAY_SECONDS
