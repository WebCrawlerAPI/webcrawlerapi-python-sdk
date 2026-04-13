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

## Documentation

- [Crawling — parameters, async, job/item responses, cancellation](docs/crawling.md)
- [Scraping — parameters, async, response fields](docs/scraping.md)
- [Advanced — output formats, structured outputs, webhooks, S3 actions](docs/advanced.md)

## Requirements

- Python 3.6+
- requests >= 2.25.0

## License

MIT License
