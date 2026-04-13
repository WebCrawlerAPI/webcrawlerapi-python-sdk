# Crawling

## crawl()

Starts a crawling job and blocks until it completes (or `max_polls` is reached).

```python
from webcrawlerapi import WebCrawlerAPI

client = WebCrawlerAPI(api_key="your_api_key")

job = client.crawl(
    url="https://example.com",
    output_formats=["markdown"],
    items_limit=10,
    max_depth=2,
    max_polls=100,
)

print(f"Status: {job.status}")
print(f"Pages crawled: {len(job.job_items)}")

for item in job.job_items:
    if item.status == "done":
        print(f"{item.original_url} — {len(item.content or '')} chars")
```

## crawl_async()

Starts a crawl and returns immediately with a job ID. Poll manually or use a webhook.

```python
response = client.crawl_async(
    url="https://example.com",
    output_formats=["markdown"],
    items_limit=10,
    webhook_url="https://yourserver.com/webhook",
)

job_id = response.id
print(f"Job started: {job_id}")
```

## get_job()

Fetch the current status of a job by ID.

```python
job = client.get_job(job_id)
print(f"Status: {job.status}")
```

## cancel_job()

Cancel a running job. Items not yet started will not be charged.

```python
result = client.cancel_job(job_id)
print(result["message"])
```

## crawl_raw_markdown()

Crawl a site and return all pages combined into a single markdown string.

```python
markdown = client.crawl_raw_markdown(
    url="https://example.com",
    items_limit=10,
)
print(markdown)
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | str | required | Seed URL for the crawler |
| `output_formats` | list | `["markdown"]` | Formats to generate: `markdown`, `cleaned`, `html`, `links` |
| `items_limit` | int | `10` | Max pages to crawl |
| `max_depth` | int | None | Max link depth from seed (0 = seed only) |
| `whitelist_regexp` | str | None | Only crawl URLs matching this pattern |
| `blacklist_regexp` | str | None | Skip URLs matching this pattern |
| `webhook_url` | str | None | POST notification URL on job completion |
| `respect_robots_txt` | bool | `False` | Honor robots.txt |
| `main_content_only` | bool | `False` | Strip nav, ads, footers |
| `max_age` | int | None | Max cache age in seconds; `0` = always fresh |
| `keep_query_params` | bool | None | Keep query params when deduplicating URLs |
| `max_polls` | int | `100` | (`crawl()` only) Max status checks before returning |

## Job response fields

| Field | Type | Description |
|---|---|---|
| `id` | str | Job ID |
| `org_id` | str | Organization ID |
| `url` | str | Seed URL |
| `status` | str | `new`, `in_progress`, `done`, `error`, `cancelled` |
| `output_formats` | list | Formats requested |
| `items_limit` | int | Page limit |
| `max_depth` | int | Crawl depth limit |
| `created_at` | datetime | Creation time |
| `finished_at` | datetime | Completion time |
| `webhook_url` | str | Webhook URL |
| `webhook_status` | str | Webhook delivery status |
| `webhook_error` | str | Webhook error (if any) |
| `job_items` | list | List of `JobItem` objects |
| `recommended_pull_delay_ms` | int | Server-suggested polling interval |

## JobItem properties

| Property | Type | Description |
|---|---|---|
| `id` | str | Item ID |
| `job_id` | str | Parent job ID |
| `job` | Job | Reference to parent job |
| `original_url` | str | Page URL |
| `status` | str | `new`, `in_progress`, `done`, `error` |
| `title` | str | Page title |
| `page_status_code` | int | HTTP status code |
| `cost` | int | Cost in credits |
| `depth` | int | Link depth from seed |
| `referred_url` | str | URL that linked to this page |
| `last_error` | str | Error message (if failed) |
| `error_code` | str | Error code (if failed) |
| `links` | list[str] | URLs found on this page (requires `links` in `output_formats`) |
| `content` | str | Page content in the highest-priority format available (cached) |
| `raw_content_url` | str | URL to raw HTML |
| `cleaned_content_url` | str | URL to cleaned HTML |
| `markdown_content_url` | str | URL to markdown |

### Fetching content per format

```python
item.get_markdown()   # fetch markdown
item.get_cleaned()    # fetch cleaned HTML
item.get_html()       # fetch raw HTML
item.content          # fetch highest-priority format (cached)
```
