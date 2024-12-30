# WebCrawler API Python SDK

A Python SDK for interacting with the WebCrawler API.

## Installation

```bash
pip install webcrawlerapi
```

## Usage

```python
from webcrawlerapi import WebCrawlerAPI

# Initialize the client
crawler = WebCrawlerAPI(api_key="your_api_key")

# Start a crawling job
response = crawler.crawl(
    url="https://example.com",
    scrape_type="markdown",
    items_limit=10,
    webhook_url="https://yourserver.com/webhook",
    allow_subdomains=False
)

# Get the job ID from the response
job_id = response["job_id"]
print(f"Crawling job started with ID: {job_id}")

# Check job status and get results
job = crawler.get_job(job_id)
print(f"Job status: {job.status}")

# Access job details
print(f"Crawled URL: {job.url}")
print(f"Created at: {job.created_at}")
print(f"Number of items: {len(job.job_items)}")

# Access individual crawled items
for item in job.job_items:
    print(f"Page title: {item.title}")
    print(f"Original URL: {item.original_url}")
    print(f"Content URL: {item.markdown_content_url}")

# Cancel a running job if needed
cancel_response = crawler.cancel_job(job_id)
print(f"Cancellation response: {cancel_response['message']}")
```

## API Methods

### crawl()
Starts a new crawling job with the specified parameters.

### get_job()
Retrieves the current status and details of a specific job.

### cancel_job()
Cancels a running job. Any items that are not in progress or already completed will be marked as canceled and will not be charged.

## Parameters

### Crawl Method
- `url` (required): The seed URL where the crawler starts. Can be any valid URL.
- `scrape_type` (default: "html"): The type of scraping you want to perform. Can be "html", "cleaned", or "markdown".
- `items_limit` (default: 10): Crawler will stop when it reaches this limit of pages for this job.
- `webhook_url` (optional): The URL where the server will send a POST request once the task is completed.
- `allow_subdomains` (default: False): If True, the crawler will also crawl subdomains.
- `whitelist_regexp` (optional): A regular expression to whitelist URLs. Only URLs that match the pattern will be crawled.
- `blacklist_regexp` (optional): A regular expression to blacklist URLs. URLs that match the pattern will be skipped.

### Job Response

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

### JobItem Properties

Each JobItem object represents a crawled page and contains:

- `id`: The unique identifier of the item
- `job_id`: The parent job identifier
- `original_url`: The URL of the page
- `page_status_code`: The HTTP status code of the page request
- `status`: The status of the item (new, in_progress, done, error)
- `title`: The page title
- `created_at`: The date when the item was created
- `cost`: The cost of the item in $
- `referred_url`: The URL where the page was referred from
- `last_error`: Any error message if the item failed
- `raw_content_url`: URL to the raw content (if available)
- `cleaned_content_url`: URL to the cleaned content (if scrape_type is "cleaned")
- `markdown_content_url`: URL to the markdown content (if scrape_type is "markdown")

## Requirements

- Python 3.6+
- requests>=2.25.0

## License

MIT License 