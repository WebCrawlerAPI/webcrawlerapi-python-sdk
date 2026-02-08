# WebcrawlerAPI Python SDK guide for LLM, OpenAI Codex, Claude Code

## Overview

This is a Python SDK for the WebCrawlerAPI service. The SDK provides both synchronous and asynchronous methods for web crawling and single-page scraping functionality.

## Common Commands

### Package Management
```bash
# Install the package in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Build the package
python setup.py sdist bdist_wheel

# Install the package for distribution
pip install webcrawlerapi
```

### Development Commands
Since this is a simple Python package without a complex build system, common development tasks include:
- Running Python scripts that use the SDK
- Testing individual methods by importing the package
- Building distribution packages with `python setup.py sdist bdist_wheel`

## Architecture

### Core Components

**webcrawlerapi/client.py** - Main SDK client class `WebCrawlerAPI`
- Handles API authentication with Bearer token
- Provides both sync (`crawl`, `scrape`) and async (`crawl_async`, `scrape_async`) methods
- Implements polling logic for long-running operations
- Uses requests.Session for HTTP communication
- Supports two API versions: v1 for crawling, v2 for scraping

**webcrawlerapi/models.py** - Data models and response objects
- `Job` - Represents a crawling job with items and status tracking
- `JobItem` - Individual crawled page with lazy content loading
- `ScrapeResponse`/`ScrapeResponseError` - Single page scraping results
- `Action` classes - For advanced operations like S3 uploads
- Custom datetime parsing for API response formats

**webcrawlerapi/__init__.py** - Package interface
- Exports main classes for public API
- Current version marked as "1.0.0" in code vs "2.0.5" in setup.py

### Key Patterns

**Lazy Content Loading**: JobItem.content property fetches and caches content from URLs only when accessed, respecting the job's scrape_type (html/cleaned/markdown).

**Polling Logic**: Both `crawl()` and `scrape()` methods implement polling with configurable max_polls and server-recommended delays for status checking.

**API Versioning**: The client uses CRAWLER_VERSION="v1" for crawling endpoints and SCRAPER_VERSION="v2" for scraping endpoints.

**Action System**: Supports extensible actions (like S3 uploads) that can be attached to crawl/scrape operations.

### API Methods Overview

- `crawl_async()` / `crawl()` - Start crawling from a seed URL, returning Job with multiple pages
- `scrape_async()` / `scrape()` - Scrape a single URL, returning content directly
- `get_job()` / `get_scrape()` - Check status of ongoing operations
- `cancel_job()` - Cancel running crawl jobs

### Dependencies

- **requests**: HTTP client library (>=2.25.0)
- **Python 3.6+**: Minimum supported version

The codebase has minimal external dependencies and follows standard Python packaging conventions with setuptools.

## Testing

### Local Test Suite

A comprehensive test suite is available in the `../local-test` directory that tests the SDK against real API endpoints using the local SDK code.

#### Running Tests

```bash
cd ../local-test
source venv/bin/activate  # if using venv
python runner.py
```

The test suite includes:
- **Scrape Tests**: Tests `scrape()` method with various output formats (markdown, cleaned, html), prompts, and structured outputs
- **Scrape Async Tests**: Tests `scrape_async()` and `get_scrape()` methods with prompt and structured output support
- **Crawl Tests**: Tests `crawl()` method with filters, different output formats, and main_content_only option
- **Crawl Async Tests**: Tests `crawl_async()` and job polling
- **Markdown Tests**: Tests `crawl_raw_markdown()` and `get_job_markdown()` methods
- **Job Tests**: Tests `get_job()` and `get_scrape()` methods

All tests use real API endpoints with books.toscrape.com as the test URL. The suite tests every parameter that each method accepts.

### Test Structure

Tests are organized in `tests/` directory:
- `test_scrape.py` - Synchronous scraping tests (5 tests)
- `test_scrape_async.py` - Asynchronous scraping tests (2 tests)
- `test_crawl.py` - Crawling tests with various configurations (4 tests)
- `test_crawl_async.py` - Asynchronous crawling tests (1 test)
- `test_markdown.py` - Markdown extraction tests (2 tests)
- `test_job.py` - Job retrieval tests (2 tests)

The `runner.py` file orchestrates all tests and provides real-time feedback with a comprehensive summary.

**Total Tests**: 16 tests across 6 modules
**Target**: 100% success rate

## API Source of Truth

The WebCrawlerAPI implementation and behavior is defined in:
- **Backend API**: `/zeus/apiv2.go` and `/zeus/api.go` in the main repository
- **Documentation**: `/artemis/content/docs/api/` in the main repository

When implementing new features or fixing bugs, always refer to these files for the canonical API behavior.

## Recent Features

### Structured Outputs (response_schema)

Added support for JSON Schema-based structured responses when using prompts:
- Define a JSON schema to enforce strict type-safety on AI responses
- Follows OpenAI Structured Outputs format
- Available on `scrape()` and `scrape_async()` methods via the `response_schema` parameter
- Works in conjunction with the `prompt` parameter
- Response data returned in `structured_data` field

**Example usage:**
```python
from webcrawlerapi import WebCrawlerAPI

client = WebCrawlerAPI(api_key="your_api_key")

response_schema = {
    "type": "object",
    "properties": {
        "site_name": {"type": "string"},
        "main_heading": {"type": "string"},
        "is_bookstore": {"type": "boolean"}
    },
    "required": ["site_name", "main_heading", "is_bookstore"],
    "additionalProperties": False
}

result = client.scrape(
    url="https://example.com",
    prompt="Extract site information",
    response_schema=response_schema
)

print(result.structured_data)  # Type-safe structured output
```

### Links Field

Added `links` field to `ScrapeResponse` model to return list of URLs found on the scraped page.