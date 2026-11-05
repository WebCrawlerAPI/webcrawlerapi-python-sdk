# Batch scrape

Scrape an explicit list of URLs in one async request. The API returns a batch `id`, scrapes the pages in the background, and you either wait for the result (the SDK polls for you) or poll/webhook yourself.

See also the [batch scrape guide](https://webcrawlerapi.com/docs/guides/batch-scrape) and the [API reference](https://webcrawlerapi.com/docs/api/batch-scrape).

## Quick example

```python
from webcrawlerapi import WebCrawlerAPI

client = WebCrawlerAPI(api_key="your_api_key")

batch = client.scrape(
    ["https://example.com/", "https://example.com/pricing", "https://example.com/docs"],
    output_formats=["markdown"],
    main_content_only=True,
    max_concurrency=5,
)

print(batch.status, batch.total, batch.completed, batch.failed)
for item in batch.data:
    if item.status == "done":
        print(item.url, item.markdown_url)
    else:
        print(item.url, item.error_code, item.error_message)
```

## Methods

| Method | Purpose |
| --- | --- |
| `scrape(urls: List[str], ...)` | Create a batch and wait until it finishes |
| `scrape_batch_async(urls, ...)` | Create a batch and return immediately |
| `get_batch(batch_id, limit=None, cursor=None)` | Get progress and one page of items |
| `get_batch_errors(batch_id)` | List failed URLs |
| `cancel_batch(batch_id)` | Cancel a running batch |

All methods raise `WebCrawlerApiError` when the API returns an error and `requests.exceptions.RequestException` when the HTTP request fails.

## scrape() with a list of URLs

```python
def scrape(
    url: List[str],
    *,
    output_formats: Optional[List[str]] = None,
    webhook_url: Optional[str] = None,
    clean_selectors: Optional[str] = None,
    main_content_only: bool = False,
    max_age: Optional[int] = None,
    respect_robots_txt: bool = False,
    max_concurrency: Optional[int] = None,
    ignore_invalid_urls: Optional[bool] = None,
    timeout_seconds: Optional[int] = None,
) -> BatchScrape
```

Passing a list (or tuple) as `url` creates a batch, polls `get_batch()` every 2 seconds until the status is `completed`, `failed` or `cancelled`, and returns a `BatchScrape` with the first page of items (up to 100). A single URL string still returns a single scrape result.

Parameters:

- `url` (required): list of URLs. Maximum is your plan's job items limit (100 during trial).
- `output_formats`: `markdown`, `cleaned`, `html`, `links`, `images`. Server default is `["markdown"]`.
- `main_content_only`: extract only the main content (default `False`).
- `clean_selectors`: CSS selectors to remove from the output.
- `max_concurrency`: max URLs scraped in parallel for this batch. `0` or `None` means no per-batch cap.
- `ignore_invalid_urls`: skip invalid URLs and report them (server default `True`). If `False`, any invalid URL fails the request.
- `webhook_url`: public http(s) URL called once when the batch finishes.
- `max_age`: cache duration in seconds. `0` bypasses the cache; the server default is 7 days.
- `respect_robots_txt`: respect each website's robots.txt (default `False`).
- `timeout_seconds`: max time to wait for the batch (default 3600).

Single-URL-only arguments (`output_format`, `prompt`, `response_schema`, `actions`, `keep_query_params`) are ignored for a batch; `prompt`, `response_schema` and `actions` are not supported in batch scrape.

Errors: if the batch is not finished after `timeout_seconds`, `WebCrawlerApiError` is raised with `error_code="timeout"`. The batch keeps running on the server; continue with `get_batch()` using the id (use `scrape_batch_async()` if you need the id up front).

Note that `scrape()` does not return the batch id before waiting and does not expose `invalid_urls`. Use `scrape_batch_async()` if you need them.

## scrape_batch_async()

```python
def scrape_batch_async(
    urls: List[str],
    output_formats: Optional[List[str]] = None,
    main_content_only: Optional[bool] = None,
    clean_selectors: Optional[str] = None,
    max_concurrency: Optional[int] = None,
    ignore_invalid_urls: Optional[bool] = None,
    webhook_url: Optional[str] = None,
    max_age: Optional[int] = None,
    respect_robots_txt: Optional[bool] = None,
) -> BatchScrapeId
```

Creates a batch and returns immediately. Parameters are the same as above (without `timeout_seconds`); options left as `None` are not sent, so server defaults apply.

Returns `BatchScrapeId`:

- `id`: batch id
- `status_url`: URL of the status endpoint
- `invalid_urls`: list of `BatchScrapeInvalidUrl` (`url`, `error_code`, `error_message`)

URLs are normalized and deduplicated. Duplicates, malformed URLs, non-public addresses, unresolvable domains and blocked domains are reported in `invalid_urls` when `ignore_invalid_urls` is true. A page accepted but with the same content as another page fails later as an item with `duplicate_item`; it appears in the batch items and errors, not in `invalid_urls`.

```python
created = client.scrape_batch_async(
    ["https://example.com/", "not a url"],
    webhook_url="https://your-server.com/webhook",
)
print(created.id)
for bad in created.invalid_urls:
    print(bad.url, bad.error_code, bad.error_message)
```

## get_batch()

```python
def get_batch(
    batch_id: str, limit: Optional[int] = None, cursor: Optional[str] = None
) -> BatchScrape
```

- `batch_id`: the batch id.
- `limit`: items per page, 1 to 500 (server default 100).
- `cursor`: the `next` value from the previous page.

Returns `BatchScrape`:

- `id`, `status` (`scraping`, `completed`, `failed` or `cancelled`)
- `total`, `completed`, `failed`, `canceled`: item counters
- `data`: list of `BatchScrapeItem` for this page
- `next`: cursor for the next page, empty string on the last page
- `is_terminal` (property): `True` when the status is `completed`, `failed`, `cancelled` or `canceled`

`BatchScrapeItem` fields: `url`, `status` (for example `done` or `error`), `page_status_code`, `title`, `markdown_url`, `cleaned_url`, `html_url` (present for finished items and only for requested formats), `from_cache`, `error_code`, `error_message` (set for failed items).

Manual polling:

```python
import time

created = client.scrape_batch_async(urls, output_formats=["markdown"])

batch = client.get_batch(created.id)
while not batch.is_terminal:
    time.sleep(2)
    batch = client.get_batch(created.id)
```

### Pagination

`scrape()` and a bare `get_batch()` return only the first page. Follow `next` until it is empty:

```python
items = []
cursor = None
while True:
    page = client.get_batch(created.id, limit=500, cursor=cursor)
    items.extend(page.data)
    if not page.next:
        break
    cursor = page.next
```

## get_batch_errors()

```python
def get_batch_errors(batch_id: str) -> BatchScrapeErrors
```

Lists URLs that failed. Returns `BatchScrapeErrors`:

- `errors`: list of `BatchScrapeError` (`url`, `error_code`, `error_message`). See the [error codes](https://webcrawlerapi.com/docs/errors).
- `robots_blocked`: list of URLs blocked by robots.txt (when `respect_robots_txt` is true)

```python
result = client.get_batch_errors(created.id)
for e in result.errors:
    print(e.url, e.error_code)
print(result.robots_blocked)
```

Failed URLs do not fail the batch. To retry them, submit them in a new batch.

## cancel_batch()

```python
def cancel_batch(batch_id: str) -> Dict[str, str]
```

Cancels a running batch and returns the API response, for example `{"status": "canceled"}`. Items that did not start are marked `canceled` and are not charged. Cancelling a batch that already finished raises `WebCrawlerApiError` (the API answers 400).

## Webhook vs polling

- Webhook: pass `webhook_url` to `scrape_batch_async()` (or `scrape()`). The API sends one `POST` when the batch finishes, with the same body as the status endpoint (first 100 items). For larger batches fetch the remaining pages with `get_batch(id, cursor=...)`. See [webhooks](https://webcrawlerapi.com/docs/async-requests).
- Polling: `scrape()` polls for you; with `scrape_batch_async()` call `get_batch()` yourself, every few seconds and not faster.
