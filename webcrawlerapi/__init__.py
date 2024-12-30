"""
WebCrawler API Python SDK
~~~~~~~~~~~~~~~~~~~~~

A Python SDK for interacting with the WebCrawler API.

Basic usage:

    >>> from webcrawlerapi import WebCrawlerAPI
    >>> crawler = WebCrawlerAPI(api_key="your_api_key")
    >>> response = crawler.crawl(url="https://example.com")
    >>> job_id = response["job_id"]
    >>> job = crawler.get_job(job_id)
"""

from .client import WebCrawlerAPI, Job, JobItem

__version__ = "1.0.0"
__all__ = ["WebCrawlerAPI", "Job", "JobItem"] 