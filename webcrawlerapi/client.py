import time
from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import urljoin

import requests

from .models import (
    Action,
    AgentRun,
    CrawlResponse,
    Job,
    JobMarkdownResponse,
    MarkdownResponse,
    ScrapeId,
    ScrapeResponse,
    ScrapeResponseError,
    WebCrawlerApiError,
)

CRAWLER_VERSION = "v1"
SCRAPER_VERSION = "v2"
AGENT_TERMINAL_STATUSES = {"done", "error", "canceled"}


class WebCrawlerAPI:
    """Python SDK for WebCrawler API."""

    DEFAULT_POLL_DELAY_SECONDS = 5

    def __init__(self, api_key: str, base_url: str = "https://api.webcrawlerapi.com"):
        """
        Initialize the WebCrawler API client.

        Args:
            api_key (str): Your API key for authentication
            base_url (str): The base URL of the API (optional)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )

    def _raise_for_error(self, response: requests.Response) -> None:
        """Parse API error response and raise WebCrawlerApiError."""
        try:
            error_data = response.json()
            error_code = error_data.get("error_code") or "unknown_error"
            error_message = (
                error_data.get("error_message")
                or error_data.get("error")
                or f"Request failed with status {response.status_code}"
            )
            raise WebCrawlerApiError(error_code, error_message, response.status_code)
        except (ValueError, KeyError):
            raise WebCrawlerApiError(
                "unknown_error",
                f"Request failed with status {response.status_code} {response.reason}",
                response.status_code,
            )

    def crawl_async(
        self,
        url: str,
        output_formats: Optional[List[str]] = None,
        scrape_type: Optional[str] = None,
        items_limit: int = 10,
        webhook_url: Optional[str] = None,
        whitelist_regexp: Optional[str] = None,
        blacklist_regexp: Optional[str] = None,
        respect_robots_txt: bool = False,
        main_content_only: bool = False,
        max_depth: Optional[int] = None,
        max_age: Optional[int] = None,
        keep_query_params: Optional[bool] = None,
    ) -> CrawlResponse:
        """
        Start a new crawling job asynchronously.

        Args:
            url (str): The seed URL where the crawler starts
            output_formats (list, optional): Output formats to request, e.g. ['markdown', 'html'].
                Defaults to ['markdown'] if neither output_formats nor scrape_type is provided.
            scrape_type (str, optional): Deprecated. Use output_formats instead.
            items_limit (int): Maximum number of pages to crawl
            webhook_url (str, optional): URL for webhook notifications
            whitelist_regexp (str, optional): Regex pattern for URL whitelist
            blacklist_regexp (str, optional): Regex pattern for URL blacklist
            respect_robots_txt (bool): Whether to respect robots.txt (default: False)
            main_content_only (bool): Whether to extract only main content (default: False)
            max_depth (int, optional): Maximum crawl depth (0 = seed only, 1 = seed + direct links)
            max_age (int, optional): Max age in seconds for cached content. 0 = always fresh.
            keep_query_params (bool, optional): Keep URL query params when deduplicating links.
                When False, example.com?a=1 and example.com?a=2 are treated as the same URL (default: True).

        Returns:
            CrawlResponse: Response containing the job ID

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        payload: Dict[str, Any] = {
            "url": url,
            "items_limit": items_limit,
        }

        # output_formats takes priority; fall back to scrape_type; default to ['markdown']
        if output_formats is not None:
            payload["output_formats"] = output_formats
        elif scrape_type is not None:
            payload["scrape_type"] = scrape_type
        else:
            payload["output_formats"] = ["markdown"]

        if webhook_url:
            payload["webhook_url"] = webhook_url
        if whitelist_regexp:
            payload["whitelist_regexp"] = whitelist_regexp
        if blacklist_regexp:
            payload["blacklist_regexp"] = blacklist_regexp
        if max_depth is not None:
            payload["max_depth"] = max_depth
        if max_age is not None:
            payload["max_age"] = max_age
        if respect_robots_txt:
            payload["respect_robots_txt"] = respect_robots_txt
        if main_content_only:
            payload["main_content_only"] = main_content_only
        if keep_query_params is not None:
            payload["keep_query_params"] = keep_query_params

        response = self.session.post(
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/crawl"), json=payload
        )
        if not response.ok:
            self._raise_for_error(response)
        return CrawlResponse(id=response.json()["id"])

    def get_job(self, job_id: str) -> Job:
        """
        Get the status and details of a specific job.

        Args:
            job_id (str): The unique identifier of the job

        Returns:
            Job: A Job object containing all job details and items

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        response = self.session.get(
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/job/{job_id}")
        )
        if not response.ok:
            self._raise_for_error(response)
        return Job(response.json())

    def get_job_markdown(self, job_id: str) -> JobMarkdownResponse:
        """
        Get the URL to the combined markdown file for a completed markdown job.

        Args:
            job_id (str): The unique identifier of the job

        Returns:
            JobMarkdownResponse: Response containing the content_url to the markdown file

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        response = self.session.get(
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/job/{job_id}/markdown")
        )
        if not response.ok:
            self._raise_for_error(response)
        data = response.json()
        return JobMarkdownResponse(content_url=data["content_url"])

    def get_job_markdown_content(self, job_id: str) -> str:
        """
        Download the combined markdown content for a completed markdown job.

        Args:
            job_id (str): The unique identifier of the job

        Returns:
            str: Combined markdown content as plain text

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        response = self.session.get(
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/job/{job_id}/markdown/content")
        )
        if not response.ok:
            self._raise_for_error(response)
        return response.text

    def markdown(self, url: str) -> MarkdownResponse:
        """
        Extract cleaned article markdown (main content only) from a webpage.

        Args:
            url (str): The URL of the webpage to extract the article markdown from

        Returns:
            MarkdownResponse: Response containing the extracted markdown

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        response = self.session.post(
            urljoin(self.base_url, "/markdown"),
            json={"url": url},
        )
        if not response.ok:
            self._raise_for_error(response)
        data = response.json()
        return MarkdownResponse(
            success=data.get("success", True), markdown=data.get("markdown")
        )

    def cancel_job(self, job_id: str) -> Dict[str, str]:
        """
        Cancel a running job. All items that are not in progress and not done
        will be marked as canceled and will not be charged.

        Args:
            job_id (str): The unique identifier of the job to cancel

        Returns:
            dict: Response containing confirmation message

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        response = self.session.put(
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/job/{job_id}/cancel")
        )
        if not response.ok:
            self._raise_for_error(response)
        return cast(Dict[str, str], response.json())

    def crawl(
        self,
        url: str,
        output_formats: Optional[List[str]] = None,
        scrape_type: Optional[str] = None,
        items_limit: int = 10,
        webhook_url: Optional[str] = None,
        whitelist_regexp: Optional[str] = None,
        blacklist_regexp: Optional[str] = None,
        respect_robots_txt: bool = False,
        main_content_only: bool = False,
        max_depth: Optional[int] = None,
        max_age: Optional[int] = None,
        keep_query_params: Optional[bool] = None,
        max_polls: int = 100,
    ) -> Job:
        """
        Start a new crawling job and wait for its completion.

        Args:
            url (str): The seed URL where the crawler starts
            output_formats (list, optional): Output formats, e.g. ['markdown']. Defaults to ['markdown'].
            scrape_type (str, optional): Deprecated. Use output_formats instead.
            items_limit (int): Maximum number of pages to crawl
            webhook_url (str, optional): URL for webhook notifications
            whitelist_regexp (str, optional): Regex pattern for URL whitelist
            blacklist_regexp (str, optional): Regex pattern for URL blacklist
            respect_robots_txt (bool): Whether to respect robots.txt (default: False)
            main_content_only (bool): Whether to extract only main content (default: False)
            max_depth (int, optional): Maximum crawl depth
            max_age (int, optional): Max age in seconds for cached content. 0 = always fresh.
            keep_query_params (bool, optional): Keep URL query params when deduplicating links (default: True).
            max_polls (int): Maximum number of status checks before returning (default: 100)

        Returns:
            Job: The final job state after completion or max polls

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If any API request fails
        """
        response = self.crawl_async(
            url=url,
            output_formats=output_formats,
            scrape_type=scrape_type,
            items_limit=items_limit,
            webhook_url=webhook_url,
            whitelist_regexp=whitelist_regexp,
            blacklist_regexp=blacklist_regexp,
            respect_robots_txt=respect_robots_txt,
            main_content_only=main_content_only,
            max_depth=max_depth,
            max_age=max_age,
            keep_query_params=keep_query_params,
        )

        job_id = response.id
        polls = 0
        job = self.get_job(job_id)

        while polls < max_polls:
            if job.is_terminal:
                return job

            delay_seconds = (
                job.recommended_pull_delay_ms / 1000
                if job.recommended_pull_delay_ms
                else self.DEFAULT_POLL_DELAY_SECONDS
            )

            time.sleep(delay_seconds)
            polls += 1
            job = self.get_job(job_id)

        return job

    def crawl_raw_markdown(
        self,
        url: str,
        scrape_type: str = "markdown",
        items_limit: int = 10,
        webhook_url: Optional[str] = None,
        whitelist_regexp: Optional[str] = None,
        blacklist_regexp: Optional[str] = None,
        respect_robots_txt: bool = False,
        main_content_only: bool = False,
        max_depth: Optional[int] = None,
        max_age: Optional[int] = None,
        keep_query_params: Optional[bool] = None,
        max_polls: int = 100,
    ) -> str:
        """
        Run a crawl job with markdown output and return the combined markdown content when finished.

        Args:
            scrape_type (str): Deprecated. Always uses markdown output.

        Raises:
            WebCrawlerApiError: If the API returns an error or the job doesn't complete successfully
            requests.exceptions.RequestException: If any API request fails
        """
        job = self.crawl(
            url=url,
            output_formats=["markdown"],
            items_limit=items_limit,
            webhook_url=webhook_url,
            whitelist_regexp=whitelist_regexp,
            blacklist_regexp=blacklist_regexp,
            respect_robots_txt=respect_robots_txt,
            main_content_only=main_content_only,
            max_depth=max_depth,
            max_age=max_age,
            keep_query_params=keep_query_params,
            max_polls=max_polls,
        )

        if job.status != "done":
            raise WebCrawlerApiError(
                "job_not_done",
                f"Job finished with status {job.status}",
            )

        return self.get_job_markdown_content(job.id)

    def run_agent_async(
        self,
        prompt: str,
        max_spend_usd: float,
        urls: Optional[List[str]] = None,
        seed_urls_only: Optional[bool] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> AgentRun:
        """
        Start a new agent run asynchronously.

        Args:
            prompt (str): Natural-language task for the agent to complete
            max_spend_usd (float): Maximum spend for this run in USD
            urls (list, optional): Optional seed URLs the agent can use while running the task
            seed_urls_only (bool, optional): If True, the agent only uses the provided seed URLs
            output_schema (dict, optional): Optional JSON schema for structured agent output
            model (str, optional): Model to use for the run. Omit to use the API default.

        Returns:
            AgentRun: The created agent run

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        payload: Dict[str, Any] = {"prompt": prompt, "max_spend_usd": max_spend_usd}

        if urls is not None:
            payload["urls"] = urls
        if seed_urls_only is not None:
            payload["seed_urls_only"] = seed_urls_only
        if output_schema is not None:
            payload["output_schema"] = output_schema
        if model is not None:
            payload["model"] = model

        response = self.session.post(
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/agent"), json=payload
        )
        if not response.ok:
            self._raise_for_error(response)
        return AgentRun(response.json())

    def get_agent_job(self, job_id: str) -> AgentRun:
        """
        Get the status and result of a specific agent run.

        Args:
            job_id (str): The unique identifier of the agent run

        Returns:
            AgentRun: The agent run status and result

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        response = self.session.get(
            urljoin(self.base_url, f"/{CRAWLER_VERSION}/agent/job/{job_id}"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )
        if not response.ok:
            self._raise_for_error(response)
        return AgentRun(response.json())

    def run_agent(
        self,
        prompt: str,
        max_spend_usd: float,
        urls: Optional[List[str]] = None,
        seed_urls_only: Optional[bool] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        max_polls: int = 100,
    ) -> AgentRun:
        """
        Start a new agent run and wait for its completion.

        Args:
            prompt (str): Natural-language task for the agent to complete
            max_spend_usd (float): Maximum spend for this run in USD
            urls (list, optional): Optional seed URLs the agent can use while running the task
            seed_urls_only (bool, optional): If True, the agent only uses the provided seed URLs
            output_schema (dict, optional): Optional JSON schema for structured agent output
            model (str, optional): Model to use for the run. Omit to use the API default.
            max_polls (int): Maximum number of status checks before raising a timeout (default: 100)

        Returns:
            AgentRun: The final agent run state after completion

        Raises:
            WebCrawlerApiError: If the API returns an error response or the run times out
            requests.exceptions.RequestException: If any API request fails
        """
        run = self.run_agent_async(
            prompt=prompt,
            max_spend_usd=max_spend_usd,
            urls=urls,
            seed_urls_only=seed_urls_only,
            output_schema=output_schema,
            model=model,
        )

        if not run.id:
            raise WebCrawlerApiError(
                "invalid_response", "Failed to fetch agent job status"
            )

        if run.status in AGENT_TERMINAL_STATUSES:
            return run

        for _ in range(max_polls):
            time.sleep(2)
            agent_job = self.get_agent_job(run.id)
            if agent_job.status in AGENT_TERMINAL_STATUSES:
                return agent_job

        raise WebCrawlerApiError(
            "timeout",
            "Agent run took too long, please retry or increase the number of polling retries",
        )

    def scrape_async(
        self,
        url: str,
        output_formats: Optional[List[str]] = None,
        output_format: Optional[str] = None,
        webhook_url: Optional[str] = None,
        clean_selectors: Optional[str] = None,
        prompt: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        actions: Optional[Union[Action, List[Action]]] = None,
        main_content_only: bool = False,
        max_age: Optional[int] = None,
        respect_robots_txt: bool = False,
        keep_query_params: Optional[bool] = None,
    ) -> ScrapeId:
        """
        Start a new scraping job asynchronously.

        Args:
            url (str): The URL to scrape
            output_formats (list, optional): Output formats, e.g. ['markdown', 'html'].
            output_format (str, optional): Deprecated. Use output_formats instead.
            webhook_url (str, optional): URL to receive a POST request when scraping is complete
            clean_selectors (str, optional): CSS selectors to remove from the output
            prompt (str, optional): AI prompt to extract or transform content (extra cost)
            response_schema (dict, optional): JSON Schema for structured AI output (use with prompt)
            actions (Action or List[Action], optional): Actions to perform after scraping
            main_content_only (bool): Strip navigation, ads, footers (default: False)
            max_age (int, optional): Max age in seconds for cached content. 0 = always fresh.
            respect_robots_txt (bool): Respect robots.txt and return error if URL is disallowed (default: False).
            keep_query_params (bool, optional): Keep URL query params when storing the URL (default: True).

        Returns:
            ScrapeId: Response containing the scrape job ID

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        payload: Dict[str, Any] = {"url": url}

        # output_formats takes priority over deprecated output_format
        if output_formats is not None:
            payload["output_formats"] = output_formats
        elif output_format is not None:
            payload["output_format"] = output_format

        if webhook_url:
            payload["webhook_url"] = webhook_url
        if clean_selectors:
            payload["clean_selectors"] = clean_selectors
        if prompt:
            payload["prompt"] = prompt
        if response_schema is not None:
            payload["response_schema"] = response_schema
        if max_age is not None:
            payload["max_age"] = max_age
        if main_content_only:
            payload["main_content_only"] = main_content_only
        if respect_robots_txt:
            payload["respect_robots_txt"] = respect_robots_txt
        if keep_query_params is not None:
            payload["keep_query_params"] = keep_query_params
        if actions:
            action_list = [actions] if not isinstance(actions, list) else actions
            payload["actions"] = [vars(action) for action in action_list]

        response = self.session.post(
            urljoin(self.base_url, f"/{SCRAPER_VERSION}/scrape?async=true"),
            json=payload,
        )

        if not response.ok:
            self._raise_for_error(response)

        return ScrapeId(id=response.json()["id"])

    def get_scrape(self, scrape_id: str) -> Union[ScrapeResponse, ScrapeResponseError]:
        """
        Get the status and result of a specific scrape job.

        Args:
            scrape_id (str): The unique identifier of the scrape job

        Returns:
            Union[ScrapeResponse, ScrapeResponseError]: The scrape result or error

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        response = self.session.get(
            urljoin(self.base_url, f"/{SCRAPER_VERSION}/scrape/{scrape_id}")
        )

        if not response.ok:
            self._raise_for_error(response)

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
                links=response_data.get("links"),
            )
        elif status == "error":
            return ScrapeResponseError(
                success=False,
                error_code=response_data.get("error_code", "unknown"),
                error_message=response_data.get("error_message", "Scraping failed"),
                status=status,
            )
        else:  # in_progress or any other status
            return ScrapeResponse(success=False, status=status, page_status_code=0)

    def scrape(
        self,
        url: str,
        output_formats: Optional[List[str]] = None,
        output_format: Optional[str] = None,
        webhook_url: Optional[str] = None,
        clean_selectors: Optional[str] = None,
        prompt: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        actions: Optional[Union[Action, List[Action]]] = None,
        main_content_only: bool = False,
        max_age: Optional[int] = None,
        respect_robots_txt: bool = False,
        keep_query_params: Optional[bool] = None,
    ) -> Union[ScrapeResponse, ScrapeResponseError]:
        """
        Scrape a single URL synchronously and return the result.

        Calls the synchronous scrape endpoint which blocks until the scrape is complete.
        For fire-and-poll behaviour use scrape_async() + get_scrape() instead.

        Args:
            url (str): The URL to scrape
            output_formats (list, optional): Output formats, e.g. ['markdown', 'html'].
            output_format (str, optional): Deprecated. Use output_formats instead.
            webhook_url (str, optional): URL to receive a POST request when scraping is complete
            clean_selectors (str, optional): CSS selectors to remove from the output
            prompt (str, optional): AI prompt to extract or transform content (extra cost)
            response_schema (dict, optional): JSON Schema for structured AI output (use with prompt)
            actions (Action or List[Action], optional): Actions to perform during scraping
            main_content_only (bool): Strip navigation, ads, footers (default: False)
            max_age (int, optional): Max age in seconds for cached content. 0 = always fresh.
            respect_robots_txt (bool): Respect robots.txt and return error if URL is disallowed (default: False).
            keep_query_params (bool, optional): Keep URL query params when storing the URL (default: True).

        Returns:
            Union[ScrapeResponse, ScrapeResponseError]: The scrape result

        Raises:
            WebCrawlerApiError: If the API returns an error response
            requests.exceptions.RequestException: If the HTTP request fails
        """
        payload: Dict[str, Any] = {"url": url}

        if output_formats is not None:
            payload["output_formats"] = output_formats
        elif output_format is not None:
            payload["output_format"] = output_format

        if webhook_url:
            payload["webhook_url"] = webhook_url
        if clean_selectors:
            payload["clean_selectors"] = clean_selectors
        if prompt:
            payload["prompt"] = prompt
        if response_schema is not None:
            payload["response_schema"] = response_schema
        if max_age is not None:
            payload["max_age"] = max_age
        if main_content_only:
            payload["main_content_only"] = main_content_only
        if respect_robots_txt:
            payload["respect_robots_txt"] = respect_robots_txt
        if keep_query_params is not None:
            payload["keep_query_params"] = keep_query_params
        if actions:
            action_list = [actions] if not isinstance(actions, list) else actions
            payload["actions"] = [vars(action) for action in action_list]

        response = self.session.post(
            urljoin(self.base_url, f"/{SCRAPER_VERSION}/scrape"),
            json=payload,
        )

        if not response.ok:
            self._raise_for_error(response)

        response_data = response.json()
        status = response_data.get("status")

        if status == "error":
            return ScrapeResponseError(
                success=False,
                error_code=response_data.get("error_code", "unknown"),
                error_message=response_data.get("error_message", "Scraping failed"),
                status=status,
            )

        return ScrapeResponse(
            success=response_data.get("success", True),
            status=status,
            markdown=response_data.get("markdown"),
            cleaned_content=response_data.get("cleaned_content"),
            raw_content=response_data.get("raw_content"),
            page_status_code=response_data.get("page_status_code", 0),
            page_title=response_data.get("page_title"),
            structured_data=response_data.get("structured_data"),
            links=response_data.get("links"),
        )
