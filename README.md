# WebCrawler API Python SDK

A Python SDK for interacting with the WebCrawlerAPI.

## In order to us API you have to get an API key from [WebCrawlerAPI](https://dash.webcrawlerapi.com/access)

## Installation

```bash
pip install webcrawlerapi
```

## Usage

### Crawling

```python
from webcrawlerapi import WebCrawlerAPI

# Initialize the client
crawler = WebCrawlerAPI(api_key="your_api_key")

# Synchronous crawling (blocks until completion)
job = crawler.crawl(
    url="https://example.com",
    scrape_type="markdown",
    items_limit=10,
    webhook_url="https://yourserver.com/webhook",
    allow_subdomains=False,
    max_polls=100  # Optional: maximum number of status checks. Use higher for bigger websites
)
print(f"Job completed with status: {job.status}")

# Access job items and their content
for item in job.job_items:
    print(f"Page title: {item.title}")
    print(f"Original URL: {item.original_url}")
    print(f"Item status: {item.status}")
    
    # Get the content based on job's scrape_type
    # Returns None if item is not in "done" status
    content = item.content
    if content:
        print(f"Content length: {len(content)}")
        print(f"Content preview: {content[:200]}...")
    else:
        print("Content not available or item not done")

# Access job items and their parent job
for item in job.job_items:
    print(f"Item URL: {item.original_url}")
    print(f"Parent job status: {item.job.status}")
    print(f"Parent job URL: {item.job.url}")

# Or use asynchronous crawling
response = crawler.crawl_async(
    url="https://example.com",
    scrape_type="markdown",
    items_limit=10,
    webhook_url="https://yourserver.com/webhook",
    allow_subdomains=False
)

# Get the job ID from the response
job_id = response.id
print(f"Crawling job started with ID: {job_id}")

# Check job status and get results
job = crawler.get_job(job_id)
print(f"Job status: {job.status}")

# Access job details
print(f"Crawled URL: {job.url}")
print(f"Created at: {job.created_at}")
print(f"Number of items: {len(job.job_items)}")

# Cancel a running job if needed
cancel_response = crawler.cancel_job(job_id)
print(f"Cancellation response: {cancel_response['message']}")
```

### Scraping

Find the list of available scrapers [here](https://webcrawlerapi.com/scrapers).

```python
# Returns structured data directly
structured_data = crawler.scrape(
    crawler_id="webcrawler/url-to-md",  # ID of the scraper
    input_data={
        "url": "https://example.com"  # Scraper-specific input parameters. Check scraper description
    },
    webhook_url="https://yourserver.com/webhook",  # Optional webhook
    max_polls=20  # Optional: maximum number of status checks
)
print(structured_data)  # Direct access to scraped data
```

## API Methods

### crawl()
Starts a new crawling job and waits for its completion. This method will continuously poll the job status until:
- The job reaches a terminal state (done, error, or cancelled)
- The maximum number of polls is reached (default: 100)
- The polling interval is determined by the server's `recommended_pull_delay_ms` or defaults to 5 seconds

### crawl_async()
Starts a new crawling job and returns immediately with a job ID. Use this when you want to handle polling and status checks yourself, or when using webhooks.

### get_job()
Retrieves the current status and details of a specific job.

### cancel_job()
Cancels a running job. Any items that are not in progress or already completed will be marked as canceled and will not be charged.

### scrape()
Starts a new scraping job and waits for its completion. Returns the structured data directly when the scraping is done. This method will continuously poll the status until:
- The scraping is completed (status: "done")
- The scraping fails (status: "error")
- The maximum number of polls is reached (default: 100)

### get_scrape()
Retrieves the current status, metadata and results of a specific scraping job. Returns a `ScrapeResult` object containing both status information and structured data.

## Parameters

### Crawl Methods (crawl and crawl_async)
- `url` (required): The seed URL where the crawler starts. Can be any valid URL.
- `scrape_type` (default: "html"): The type of scraping you want to perform. Can be "html", "cleaned", or "markdown".
- `items_limit` (default: 10): Crawler will stop when it reaches this limit of pages for this job.
- `webhook_url` (optional): The URL where the server will send a POST request once the task is completed.
- `allow_subdomains` (default: False): If True, the crawler will also crawl subdomains.
- `whitelist_regexp` (optional): A regular expression to whitelist URLs. Only URLs that match the pattern will be crawled.
- `blacklist_regexp` (optional): A regular expression to blacklist URLs. URLs that match the pattern will be skipped.
- `max_polls` (optional, crawl only): Maximum number of status checks before returning (default: 100)

### Scrape Methods (scrape and scrape_async)
- `crawler_id` (required): The ID of the custom scraper.
- `input_data` (required): The input data for the scraper.
- `webhook_url` (optional): The URL where the server will send a POST request once the task is completed.
- `max_polls` (optional, scrape only): Maximum number of status checks before returning (default: 100)

### Responses

#### CrawlAsync Response
The `crawl_async()` method returns a `CrawlResponse` object with:
- `id`: The unique identifier of the created job

#### Job Response
The Job object contains detailed information about the crawling job:

- `id`: The unique identifier of the job
- `org_id`: Your organization identifier
- `url`: The seed URL where the crawler started
- `status`: The status of the job (new, in_progress, done, error)
- `scrape_type`: The type of scraping performed
- `created_at`: The date when the job was created
- `finished_at`: The date when the job was finished (if completed)
- `webhook_url`: The webhook URL for notifications
- `webhook_status`: The status of the webhook request
- `webhook_error`: Any error message if the webhook request failed
- `job_items`: List of JobItem objects representing crawled pages
- `recommended_pull_delay_ms`: Server-recommended delay between status checks

### JobItem Properties

Each JobItem object represents a crawled page and contains:

- `id`: The unique identifier of the item
- `job_id`: The parent job identifier
- `job`: Reference to the parent Job object
- `original_url`: The URL of the page
- `page_status_code`: The HTTP status code of the page request
- `status`: The status of the item (new, in_progress, done, error)
- `title`: The page title
- `created_at`: The date when the item was created
- `cost`: The cost of the item in $
- `referred_url`: The URL where the page was referred from
- `last_error`: Any error message if the item failed
- `content`: The page content based on the job's scrape_type (html, cleaned, or markdown). Returns None if the item's status is not "done" or if content is not available. Content is automatically fetched and cached when accessed.
- `raw_content_url`: URL to the raw content (if available)
- `cleaned_content_url`: URL to the cleaned content (if scrape_type is "cleaned")
- `markdown_content_url`: URL to the markdown content (if scrape_type is "markdown")

## Requirements

- Python 3.6+
- requests>=2.25.0

## License

MIT License 