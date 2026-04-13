# Scraping

## scrape()

Scrape a single URL synchronously and return the result.

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

### Multiple formats in one request

```python
result = client.scrape(
    url="https://example.com",
    output_formats=["markdown", "cleaned", "html", "links"],
)

print(result.markdown)
print(result.cleaned_content)
print(result.raw_content)
print(result.links)   # list of URLs found on the page
```

## scrape_async()

Start a scrape and return immediately with a job ID.

```python
scrape_id = client.scrape_async(
    url="https://example.com",
    output_formats=["markdown"],
    webhook_url="https://yourserver.com/webhook",
)

print(f"Scrape started: {scrape_id.id}")
```

## get_scrape()

Poll for the result of an async scrape.

```python
result = client.get_scrape(scrape_id.id)

if result.status == "done" and result.success:
    print(result.markdown)
elif result.status == "in_progress":
    print("Still processing...")
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | str | required | URL to scrape |
| `output_formats` | list | None | Formats: `markdown`, `cleaned`, `html`, `links` |
| `webhook_url` | str | None | POST notification URL on completion |
| `clean_selectors` | str | None | CSS selectors to strip from output |
| `prompt` | str | None | AI prompt to extract or transform content (extra cost) |
| `response_schema` | dict | None | JSON Schema for structured AI output (use with `prompt`) |
| `main_content_only` | bool | `False` | Strip nav, ads, footers |
| `max_age` | int | None | Max cache age in seconds; `0` = always fresh |
| `respect_robots_txt` | bool | `False` | Return error if URL is disallowed by robots.txt |
| `keep_query_params` | bool | None | Keep query params when storing the URL |

## ScrapeResponse fields

| Field | Type | Description |
|---|---|---|
| `success` | bool | Whether the scrape succeeded |
| `status` | str | `done`, `error`, `in_progress` |
| `markdown` | str | Markdown content (if `markdown` in `output_formats`) |
| `cleaned_content` | str | Cleaned HTML (if `cleaned` in `output_formats`) |
| `raw_content` | str | Raw HTML (if `html` in `output_formats`) |
| `links` | list[str] | URLs found on the page (if `links` in `output_formats`) |
| `page_status_code` | int | HTTP status code of the scraped page |
| `page_title` | str | Page title |
| `structured_data` | dict | AI-extracted structured data (if `prompt` was provided) |

## ScrapeResponseError fields

| Field | Type | Description |
|---|---|---|
| `success` | bool | Always `False` |
| `status` | str | `error` |
| `error_code` | str | Machine-readable error code |
| `error_message` | str | Human-readable error message |
