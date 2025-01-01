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
    >>> # Single page scraping (returns structured data directly)
    >>> structured_data = crawler.scrape(
    ...     crawler_id="webcrawler/url-to-md",
    ...     input_data={"url": "https://example.com"}
    ... )
    >>> print(structured_data)  # Direct access to structured data
    >>> # Or asynchronous scraping
    >>> response = crawler.scrape_async(
    ...     crawler_id="webcrawler/url-to-md",
    ...     input_data={"url": "https://example.com"}
    ... )
    >>> result = crawler.get_scrape(response.id)  # Get full scrape result
    >>> print(result.structured_data)  # Access structured data from result
"""

from .models import (
    CrawlResponse,
    ScrapeResponse,
    Job,
    JobItem,
    ScrapeResult,
)
from .client import WebCrawlerAPI

__version__ = "1.0.0"
__all__ = [
    "WebCrawlerAPI",
    "Job",
    "JobItem",
    "CrawlResponse",
    "ScrapeResponse",
    "ScrapeResult",
] 