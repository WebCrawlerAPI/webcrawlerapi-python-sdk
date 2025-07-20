# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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