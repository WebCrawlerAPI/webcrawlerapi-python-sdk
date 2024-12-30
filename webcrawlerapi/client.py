import requests
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from datetime import datetime


class JobItem:
    """Represents a single crawled page item in a job."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.job_id: str = data["job_id"]
        self.original_url: str = data["original_url"]
        self.page_status_code: int = data["page_status_code"]
        self.status: str = data["status"]
        self.title: str = data["title"]
        self.created_at: datetime = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        self.updated_at: datetime = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        self.cost: int = data["cost"]
        self.referred_url: str = data["referred_url"]
        self.last_error: str = data["last_error"]
        
        # Optional content URLs based on scrape_type
        self.raw_content_url: Optional[str] = data.get("raw_content_url")
        self.cleaned_content_url: Optional[str] = data.get("cleaned_content_url")
        self.markdown_content_url: Optional[str] = data.get("markdown_content_url")


class Job:
    """Represents a crawling job."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id: str = data["id"]
        self.org_id: str = data["org_id"]
        self.url: str = data["url"]
        self.status: str = data["status"]
        self.scrape_type: str = data["scrape_type"]
        self.whitelist_regexp: str = data["whitelist_regexp"]
        self.blacklist_regexp: str = data["blacklist_regexp"]
        self.allow_subdomains: bool = data["allow_subdomains"]
        self.items_limit: int = data["items_limit"]
        self.created_at: datetime = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        self.updated_at: datetime = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        self.webhook_url: str = data["webhook_url"]
        
        # Optional fields
        self.finished_at: Optional[datetime] = None
        if data.get("finished_at"):
            self.finished_at = datetime.fromisoformat(data["finished_at"].replace('Z', '+00:00'))
        
        self.webhook_status: Optional[str] = data.get("webhook_status")
        self.webhook_error: Optional[str] = data.get("webhook_error")
        
        # Parse job items
        self.job_items: List[JobItem] = [JobItem(item) for item in data.get("job_items", [])]


class WebCrawlerAPI:
    """Python SDK for WebCrawler API."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.webcrawlerapi.com/v1"):
        """
        Initialize the WebCrawler API client.
        
        Args:
            api_key (str): Your API key for authentication
            base_url (str): The base URL of the API (optional)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def crawl(
        self,
        url: str,
        scrape_type: str = "html",
        items_limit: int = 10,
        webhook_url: Optional[str] = None,
        allow_subdomains: bool = False,
        whitelist_regexp: Optional[str] = None,
        blacklist_regexp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new crawling job.
        
        Args:
            url (str): The seed URL where the crawler starts
            scrape_type (str): Type of scraping (html, cleaned, markdown)
            items_limit (int): Maximum number of pages to crawl
            webhook_url (str, optional): URL for webhook notifications
            allow_subdomains (bool): Whether to crawl subdomains
            whitelist_regexp (str, optional): Regex pattern for URL whitelist
            blacklist_regexp (str, optional): Regex pattern for URL blacklist
        
        Returns:
            dict: Response containing the job_id
        
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
            urljoin(self.base_url, "/crawl"),
            json=payload
        )
        response.raise_for_status()
        return response.json()

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
            urljoin(self.base_url, f"/job/{job_id}")
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
            urljoin(self.base_url, f"/job/{job_id}/cancel")
        )
        response.raise_for_status()
        return response.json() 