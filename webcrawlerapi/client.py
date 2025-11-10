import time
from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import urljoin

import requests

from .models import (
    Action,
    CrawlResponse,
    Job,
    ScrapeId,
    ScrapeResponse,
    ScrapeResponseError,
)

CRAWLER_VERSION = "v1"
SCRAPER_VERSION = "v2"


class WebCrawlerAPI:
    """Python SDK for WebCrawler API."""

    DEFAULT_POLL_DELAY_SECONDS = 5

    def __init__(self, api_key: str, base_url: str = "https://api.webcrawlerapi.com"):
        """
        Initialize the WebCrawler API client.

        Args:
            api_key (str): Your API key for authentication
            base_url (str): The base URL of the API (optional)
            version (str): API version to use (optional, defaults to 'v1')
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

    def crawl_async(
        self,
        url: str,
        scrape_type: str = "markdown",
        items_limit: int = 10,
        webhook_url: Optional[str] = None,
        allow_subdomains: bool = False,
        whitelist_regexp: Optional[str] = None,
        blacklist_regexp: Optional[str] = None,
        actions: Optional[Union[Action, List[Action]]] = None,
        respect_robots_txt: bool = False,
        main_content_only: bool = False,
        max_depth: Optional[int] = None,
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
            actions (Action or List[Action], optional): Actions to perform during crawling
            respect_robots_txt (bool): Whether to respect robots.txt file (default: False)
            main_content_only (bool): Whether to extract only main content (default: False)
            max_depth (int, optional): Maximum depth of crawl (0 for seed URL only, 1 for one level deep, etc.)

        Returns:
            CrawlResponse: Response containing the job ID

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        payload = {
            "url": url,
            "scrape_type": scrape_type,
            "items_limit": items_limit,
            "allow_subdomains": allow_subdomains,
            "respect_robots_txt": respect_robots_txt,
            "main_content_only": main_content_only,
        }

        if webhook_url:
            payload["webhook_url"] = webhook_url
        if whitelist_regexp:
            payload["whitelist_regexp"] = whitelist_regexp
        if blacklist_regexp:
            payload["blacklist_regexp"] = blacklist_regexp
        if max_depth is not None:
            payload["max_depth"] = max_depth
        if actions:
            # Convert single action to list if needed
            action_list = [actions] if not isinstance(actions, list) else actions
            # Convert dataclass objects to dictionaries
            payload["actions"] = [vars(action) for action in action_list]

        response = self.session.post(
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/crawl"), json=payload
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
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/job/{job_id}")
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
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/job/{job_id}/cancel")
        )
        response.raise_for_status()
        return cast(Dict[str, str], response.json())

    def crawl(
        self,
        url: str,
        scrape_type: str = "markdown",
        items_limit: int = 10,
        webhook_url: Optional[str] = None,
        allow_subdomains: bool = False,
        whitelist_regexp: Optional[str] = None,
        blacklist_regexp: Optional[str] = None,
        actions: Optional[Union[Action, List[Action]]] = None,
        respect_robots_txt: bool = False,
        main_content_only: bool = False,
        max_depth: Optional[int] = None,
        max_polls: int = 100,
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
            actions (Action or List[Action], optional): Actions to perform during crawling
            respect_robots_txt (bool): Whether to respect robots.txt file (default: False)
            main_content_only (bool): Whether to extract only main content (default: False)
            max_depth (int, optional): Maximum depth of crawl (0 for seed URL only, 1 for one level deep, etc.)
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
            blacklist_regexp=blacklist_regexp,
            actions=actions,
            respect_robots_txt=respect_robots_txt,
            main_content_only=main_content_only,
            max_depth=max_depth,
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
        url: str,
        output_format: str = "markdown",
        webhook_url: Optional[str] = None,
        clean_selectors: Optional[str] = None,
        prompt: Optional[str] = None,
        actions: Optional[Union[Action, List[Action]]] = None,
        respect_robots_txt: bool = False,
        main_content_only: bool = False,
    ) -> ScrapeId:
        """
        Start a new scraping job asynchronously.

        Args:
            url (str): The URL to scrape
            output_format (str): Output format (markdown, cleaned, html)
            webhook_url (str, optional): URL to receive a POST request when scraping is complete
            clean_selectors (str, optional): CSS selectors to clean from the content
            prompt (str, optional): Prompt to guide the AI response
            actions (Action or List[Action], optional): Actions to perform after scraping (for example S3 upload)
            respect_robots_txt (bool): Whether to respect robots.txt file (default: False)
            main_content_only (bool): Whether to extract only main content (default: False)

        Returns:
            ScrapeId: Response containing the scrape job ID

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        payload = {
            "url": url,
            "output_format": output_format,
            "respect_robots_txt": respect_robots_txt,
            "main_content_only": main_content_only,
        }

        if webhook_url:
            payload["webhook_url"] = webhook_url
        if clean_selectors:
            payload["clean_selectors"] = clean_selectors
        if prompt:
            payload["prompt"] = prompt
        if actions:
            # Convert single action to list if needed
            action_list = [actions] if not isinstance(actions, list) else actions
            # Convert dataclass objects to dictionaries
            payload["actions"] = [vars(action) for action in action_list]

        response = self.session.post(
            urljoin(self.base_url, f"/{SCRAPER_VERSION}/scrape?async=true"),
            json=payload,
        )

        if not response.ok:
            try:
                error_data = response.json()
                raise requests.exceptions.HTTPError(
                    f"{response.status_code} {response.reason}: {error_data.get('error', 'Unknown error')}"
                )
            except ValueError:
                # If response is not JSON, raise with status and text
                raise requests.exceptions.HTTPError(
                    f"{response.status_code} {response.reason}: {response.text}"
                )

        response.raise_for_status()
        return ScrapeId(id=response.json()["id"])

    def get_scrape(self, scrape_id: str) -> Union[ScrapeResponse, ScrapeResponseError]:
        """
        Get the status and result of a specific scrape job.

        Args:
            scrape_id (str): The unique identifier of the scrape job

        Returns:
            Union[ScrapeResponse, ScrapeResponseError]: The scrape result or error

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        response = self.session.get(
            urljoin(self.base_url, f"/{SCRAPER_VERSION}/scrape/{scrape_id}")
        )

        response.raise_for_status()
        response_data = response.json()

        status = response_data.get("status")

        if status == "done":
            return ScrapeResponse(
                success=response_data.get("success", True),
                status=status,
                markdown=response_data.get("markdown"),
                cleaned_content=response_data.get("cleaned_content"),
                raw_content=response_data.get("raw_content"),
                page_status_code=response_data.get("page_status_code", 0),
                page_title=response_data.get("page_title"),
                structured_data=response_data.get("structured_data"),
            )
        elif status == "error":
            return ScrapeResponseError(
                success=False,
                error_code=response_data.get("error_code", "unknown"),
                error_message=response_data.get("error_message", "Scraping failed"),
                status=status,
            )
        else:  # in_progress or any other status
            return ScrapeResponse(success=False, status=status)

    def scrape(
        self,
        url: str,
        output_format: str = "markdown",
        webhook_url: Optional[str] = None,
        clean_selectors: Optional[str] = None,
        prompt: Optional[str] = None,
        actions: Optional[Union[Action, List[Action]]] = None,
        respect_robots_txt: bool = False,
        main_content_only: bool = False,
        max_polls: int = 100,
    ) -> Union[ScrapeResponse, ScrapeResponseError]:
        """
        Scrape a single URL and wait for completion.

        This method will start a scraping job and continuously poll its status
        until it reaches a terminal state (done or error) or until
        the maximum number of polls is reached.

        Args:
            url (str): The URL to scrape
            output_format (str): Output format (markdown, cleaned, html)
            webhook_url (str, optional): URL to receive a POST request when scraping is complete
            clean_selectors (str, optional): CSS selectors to clean from the content
            prompt (str, optional): Prompt to guide the AI response
            actions (Action or List[Action], optional): Actions to perform during scraping
            respect_robots_txt (bool): Whether to respect robots.txt file (default: False)
            main_content_only (bool): Whether to extract only main content (default: False)
            max_polls (int): Maximum number of status checks before returning (default: 100)

        Returns:
            Union[ScrapeResponse, ScrapeResponseError]: The final scrape result

        Raises:
            requests.exceptions.RequestException: If any API request fails
        """
        # Start the scraping job
        response = self.scrape_async(
            url=url,
            output_format=output_format,
            webhook_url=webhook_url,
            clean_selectors=clean_selectors,
            prompt=prompt,
            actions=actions,
            respect_robots_txt=respect_robots_txt,
            main_content_only=main_content_only,
        )

        scrape_id = response.id
        polls = 0

        while polls < max_polls:
            result = self.get_scrape(scrape_id)

            # Return immediately if scrape is done
            if isinstance(result, ScrapeResponse) and result.status == "done":
                return result

            # Return immediately if there's an error
            if isinstance(result, ScrapeResponseError):
                return result

            # Continue polling if status is in_progress or any other non-terminal status
            # Wait before next poll
            time.sleep(self.DEFAULT_POLL_DELAY_SECONDS)
            polls += 1

        # Return the last known state if max_polls is reached
        return result
