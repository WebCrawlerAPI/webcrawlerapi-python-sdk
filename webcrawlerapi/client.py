import requests
from typing import Optional, Dict, Any
from urllib.parse import urljoin
import time

from .models import (
    CrawlResponse,
    ScrapeResponse,
    Job,
    ScrapeResult,
)


class WebCrawlerAPI:
    """Python SDK for WebCrawler API."""
    
    DEFAULT_POLL_DELAY_SECONDS = 5
    
    def __init__(self, api_key: str, base_url: str = "https://api.webcrawlerapi.com", version: str = "v1"):
        """
        Initialize the WebCrawler API client.
        
        Args:
            api_key (str): Your API key for authentication
            base_url (str): The base URL of the API (optional)
            version (str): API version to use (optional, defaults to 'v1')
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.version = version
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def crawl_async(
        self,
        url: str,
        scrape_type: str = "html",
        items_limit: int = 10,
        webhook_url: Optional[str] = None,
        allow_subdomains: bool = False,
        whitelist_regexp: Optional[str] = None,
        blacklist_regexp: Optional[str] = None
    ) -> CrawlResponse:
        """
        Start a new crawling job asynchronously.
        
        Args:
            url (str): The seed URL where the crawler starts
            scrape_type (str): Type of scraping (html, cleaned, markdown)
            items_limit (int): Maximum number of pages to crawl
            webhook_url (str, optional): URL for webhook notifications
            allow_subdomains (bool): Whether to crawl subdomains
            whitelist_regexp (str, optional): Regex pattern for URL whitelist
            blacklist_regexp (str, optional): Regex pattern for URL blacklist
        
        Returns:
            CrawlResponse: Response containing the job ID
        
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        payload = {
            "url": url,
            "scrape_type": scrape_type,
            "items_limit": items_limit,
            "allow_subdomains": allow_subdomains
        }

        if webhook_url:
            payload["webhook_url"] = webhook_url
        if whitelist_regexp:
            payload["whitelist_regexp"] = whitelist_regexp
        if blacklist_regexp:
            payload["blacklist_regexp"] = blacklist_regexp

        response = self.session.post(
            urljoin(self.base_url, f"/{self.version}/crawl"),
            json=payload
        )
        response.raise_for_status()
        return CrawlResponse(id=response.json()["id"])

    def get_job(self, job_id: str) -> Job:
        """
        Get the status and details of a specific job.
        
        Args:
            job_id (str): The unique identifier of the job
            
        Returns:
            Job: A Job object containing all job details and items
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        response = self.session.get(
            urljoin(self.base_url, f"/{self.version}/job/{job_id}")
        )
        response.raise_for_status()
        return Job(response.json())

    def cancel_job(self, job_id: str) -> Dict[str, str]:
        """
        Cancel a running job. All items that are not in progress and not done
        will be marked as canceled and will not be charged.
        
        Args:
            job_id (str): The unique identifier of the job to cancel
            
        Returns:
            dict: Response containing confirmation message
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        response = self.session.put(
            urljoin(self.base_url, f"/{self.version}/job/{job_id}/cancel")
        )
        response.raise_for_status()
        return response.json()

    def crawl(
        self,
        url: str,
        scrape_type: str = "html",
        items_limit: int = 10,
        webhook_url: Optional[str] = None,
        allow_subdomains: bool = False,
        whitelist_regexp: Optional[str] = None,
        blacklist_regexp: Optional[str] = None,
        max_polls: int = 100
    ) -> Job:
        """
        Start a new crawling job and wait for its completion.
        
        This method will start a crawling job and continuously poll its status
        until it reaches a terminal state (done, error, or cancelled) or until
        the maximum number of polls is reached.
        
        Args:
            url (str): The seed URL where the crawler starts
            scrape_type (str): Type of scraping (html, cleaned, markdown)
            items_limit (int): Maximum number of pages to crawl
            webhook_url (str, optional): URL for webhook notifications
            allow_subdomains (bool): Whether to crawl subdomains
            whitelist_regexp (str, optional): Regex pattern for URL whitelist
            blacklist_regexp (str, optional): Regex pattern for URL blacklist
            max_polls (int): Maximum number of status checks before returning (default: 100)
        
        Returns:
            Job: The final job state after completion or max polls
            
        Raises:
            requests.exceptions.RequestException: If any API request fails
        """
        # Start the crawling job
        response = self.crawl_async(
            url=url,
            scrape_type=scrape_type,
            items_limit=items_limit,
            webhook_url=webhook_url,
            allow_subdomains=allow_subdomains,
            whitelist_regexp=whitelist_regexp,
            blacklist_regexp=blacklist_regexp
        )
        
        job_id = response.id
        polls = 0
        
        while polls < max_polls:
            job = self.get_job(job_id)
            
            # Return immediately if job is in a terminal state
            if job.is_terminal:
                return job
            
            # Calculate delay for next poll
            delay_seconds = (
                job.recommended_pull_delay_ms / 1000
                if job.recommended_pull_delay_ms
                else self.DEFAULT_POLL_DELAY_SECONDS
            )
            
            time.sleep(delay_seconds)
            polls += 1
        
        # Return the last known state if max_polls is reached
        return job

    def scrape_async(
        self,
        crawler_id: str,
        input_data: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> ScrapeResponse:
        """
        Start a new scraping job asynchronously.
        
        Args:
            crawler_id (str): The ID of the custom scraper to use
            input_data (dict): Additional input parameters required by the scraper
            webhook_url (str, optional): URL to receive a POST request when scraping is complete
            
        Returns:
            ScrapeResponse: Response containing the scrape job ID
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        payload = {
            "crawler_id": crawler_id,
            "input": input_data
        }
        
        if webhook_url:
            payload["webhook_url"] = webhook_url

        response = self.session.post(
            urljoin(self.base_url, f"/{self.version}/scrape"),
            json=payload
        )
        response.raise_for_status()
        return ScrapeResponse(id=response.json()["id"])

    def get_scrape(self, scrape_id: str) -> ScrapeResult:
        """
        Get the status and results of a specific scraping job.
        
        Args:
            scrape_id (str): The unique identifier of the scraping job
            
        Returns:
            ScrapeResult: A ScrapeResult object containing status and structured data
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        response = self.session.get(
            urljoin(self.base_url, f"/{self.version}/scrape/{scrape_id}")
        )
        response.raise_for_status()
        return ScrapeResult(response.json())

    def scrape(
        self,
        crawler_id: str,
        input_data: Dict[str, Any],
        webhook_url: Optional[str] = None,
        max_polls: int = 100
    ) -> Dict[str, Any]:
        """
        Start a new scraping job and wait for its completion.
        Returns only the structured data from the scraping result.
        
        This method will start a scraping job and continuously poll its status
        until it reaches a terminal state (done or error) or until the maximum
        number of polls is reached.
        
        Args:
            crawler_id (str): The ID of the custom scraper to use
            input_data (dict): Additional input parameters required by the scraper
            webhook_url (str, optional): URL to receive a POST request when scraping is complete
            max_polls (int): Maximum number of status checks before returning (default: 100)
            
        Returns:
            Dict[str, Any]: The structured data from the scraping result
            
        Raises:
            requests.exceptions.RequestException: If any API request fails
            RuntimeError: If the scraping job failed or max polls was reached
        """
        # Start the scraping job
        response = self.scrape_async(
            crawler_id=crawler_id,
            input_data=input_data,
            webhook_url=webhook_url
        )
        
        scrape_id = response.id
        polls = 0
        
        while polls < max_polls:
            result = self.get_scrape(scrape_id)
            
            # Return immediately if scrape is done
            if result.status == "done":
                return result.structured_data
                
            # Raise error if scrape failed
            if result.status == "error":
                raise RuntimeError(f"Scraping failed: {result.error if hasattr(result, 'error') else 'Unknown error'}")
            
            # Use recommended delay or default
            delay_seconds = (
                result.recommended_pull_delay_ms / 1000
                if hasattr(result, 'recommended_pull_delay_ms') and result.recommended_pull_delay_ms
                else self.DEFAULT_POLL_DELAY_SECONDS
            )
            
            time.sleep(delay_seconds)
            polls += 1
        
        raise RuntimeError("Maximum number of polls reached without completion") 