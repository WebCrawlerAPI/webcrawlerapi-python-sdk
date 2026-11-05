"""
WebCrawler API Python SDK
~~~~~~~~~~~~~~~~~~~~~

A Python SDK for interacting with the WebCrawler API.

Basic usage:

    >>> from webcrawlerapi import WebCrawlerAPI
    >>> crawler = WebCrawlerAPI(api_key="your_api_key")
    >>> # Synchronous crawling
    >>> job = crawler.crawl(url="https://example.com")
    >>> print(f"Job status: {job.status}")
    >>> # Or asynchronous crawling
    >>> response = crawler.crawl_async(url="https://example.com")
    >>> job = crawler.get_job(response.id)
    >>> # Single page scraping (starts the scrape and waits for the result)
    >>> result = crawler.scrape(url="https://example.com", output_format="markdown")
    >>> if result.success:
    ...     print(result.markdown)  # Access the scraped content
    ... else:
    ...     print(f"Error: {result.error_message}")
"""

from .client import WebCrawlerAPI
from .models import (
    Action,
    AgentRun,
    BatchScrape,
    BatchScrapeError,
    BatchScrapeErrors,
    BatchScrapeId,
    BatchScrapeInvalidUrl,
    BatchScrapeItem,
    CrawlResponse,
    Job,
    JobItem,
    JobMarkdownResponse,
    MarkdownResponse,
    ScrapeId,
    ScrapeResponse,
    ScrapeResponseError,
    UploadS3Action,
    WebCrawlerApiError,
)

__version__ = "2.1.8"
__all__ = [
    "WebCrawlerAPI",
    "WebCrawlerApiError",
    "Job",
    "JobItem",
    "JobMarkdownResponse",
    "MarkdownResponse",
    "CrawlResponse",
    "ScrapeId",
    "ScrapeResponse",
    "ScrapeResponseError",
    "Action",
    "UploadS3Action",
    "AgentRun",
    "BatchScrape",
    "BatchScrapeError",
    "BatchScrapeErrors",
    "BatchScrapeId",
    "BatchScrapeInvalidUrl",
    "BatchScrapeItem",
]
