# WebCrawler API Python SDK

A Python SDK for interacting with the [WebCrawlerAPI](https://webcrawlerapi.com).

Get your API key at [dash.webcrawlerapi.com/access](https://dash.webcrawlerapi.com/access).

## Installation

```bash
pip install webcrawlerapi
```

## Crawling

```python
from webcrawlerapi import WebCrawlerAPI

client = WebCrawlerAPI(api_key="your_api_key")

job = client.crawl(
    url="https://example.com",
    output_formats=["markdown"],
    items_limit=10,
)

for item in job.job_items:
    if item.status == "done":
        print(item.original_url)
        print(item.content)
```

## Scraping

```python
from webcrawlerapi import WebCrawlerAPI

client = WebCrawlerAPI(api_key="your_api_key")

result = client.scrape(
    url="https://example.com",
    output_formats=["markdown"],
)

if result.success:
    print(result.markdown)
else:
    print(f"Error: {result.error_code} — {result.error_message}")
```

## Batch scrape

```python
batch = client.scrape(
    ["https://example.com/", "https://example.com/pricing"],
    output_formats=["markdown"],
    max_concurrency=5,
)

print(batch.status, batch.completed, batch.failed)
for item in batch.data:
    print(item.url, item.status, item.markdown_url)
```

Passing a list to `scrape()` creates a batch and polls until it finishes (a single URL string still returns a
single result). Batch-only options: `max_concurrency`, `ignore_invalid_urls`, `timeout_seconds`. For manual
control use `scrape_batch_async()`, `get_batch(id, limit=, cursor=)`, `get_batch_errors(id)` and `cancel_batch(id)`.

## Documentation

- [Crawling — parameters, async, job/item responses, cancellation](docs/crawling.md)
- [Scraping — parameters, async, response fields](docs/scraping.md)
- [Batch scrape — full batch reference, pagination, errors, cancel](docs/batch-scrape.md)
- [Advanced — output formats, structured outputs, webhooks, S3 actions](docs/advanced.md)

## Requirements

- Python 3.6+
- requests >= 2.25.0

## License

MIT License
