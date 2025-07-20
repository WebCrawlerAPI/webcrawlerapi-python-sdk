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
    >>> # Single page scraping (synchronous)
    >>> result = crawler.scrape(url="https://example.com", output_format="markdown")
    >>> if result.success:
    ...     print(result.markdown)  # Access the scraped content
    ... else:
    ...     print(f"Error: {result.error_message}")
"""

from .client import WebCrawlerAPI
from .models import (
    Action,
    CrawlResponse,
    Job,
    JobItem,
    ScrapeId,
    ScrapeResponse,
    ScrapeResponseError,
    UploadS3Action,
)

__version__ = "1.0.0"
__all__ = [
    "WebCrawlerAPI",
    "Job",
    "JobItem",
    "CrawlResponse",
    "ScrapeId",
    "ScrapeResponse",
    "ScrapeResponseError",
    "Action",
    "UploadS3Action",
]
