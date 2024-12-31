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
"""

from .client import WebCrawlerAPI, Job, JobItem, CrawlResponse

__version__ = "1.0.0"
__all__ = ["WebCrawlerAPI", "Job", "JobItem", "CrawlResponse"] 