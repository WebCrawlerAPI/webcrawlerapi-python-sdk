# Advanced Usage

## Output formats

Both `scrape()` and `crawl()` accept `output_formats` — a list of one or more formats to generate in a single request.

Valid values: `markdown`, `cleaned`, `html`, `links`

```python
# Scrape — all 4 formats at once
result = client.scrape(
    url="https://example.com",
    output_formats=["markdown", "cleaned", "html", "links"],
)

print(result.markdown)         # markdown text
print(result.cleaned_content)  # cleaned HTML
print(result.raw_content)      # raw HTML
print(result.links)            # list of URLs found on the page

# Crawl — all 4 formats at once
job = client.crawl(
    url="https://example.com",
    output_formats=["markdown", "cleaned", "html", "links"],
    items_limit=5,
)

for item in job.job_items:
    if item.status == "done":
        print(item.get_markdown())
        print(item.get_cleaned())
        print(item.get_html())
        print(item.links)      # list of URLs found on this page
```

## AI extraction with prompt

Pass a `prompt` to extract or transform content using AI (additional cost applies).

```python
result = client.scrape(
    url="https://example.com/product",
    prompt="Extract the product name, price, and availability",
)

print(result.structured_data)  # dict with extracted fields
```

## Structured output (response_schema)

Combine `prompt` with `response_schema` to enforce a strict JSON shape on the AI response.
Follows the [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) format.

```python
schema = {
    "type": "object",
    "properties": {
        "name":          {"type": "string"},
        "price":         {"type": "number"},
        "in_stock":      {"type": "boolean"},
    },
    "required": ["name", "price", "in_stock"],
    "additionalProperties": False,
}

result = client.scrape(
    url="https://example.com/product",
    prompt="Extract product information",
    response_schema=schema,
)

print(result.structured_data)
# {"name": "Widget", "price": 29.99, "in_stock": True}
```

## Webhooks

Pass `webhook_url` to receive a POST notification when a job or scrape completes.
Useful with `crawl_async()` or `scrape_async()` so you don't need to poll.

```python
response = client.crawl_async(
    url="https://example.com",
    output_formats=["markdown"],
    items_limit=20,
    webhook_url="https://yourserver.com/webhooks/crawl",
)

print(f"Job {response.id} started — result will be POSTed to your webhook")
```

## S3 upload action

Use `UploadS3Action` to automatically upload crawled content to an S3-compatible bucket.

```python
from webcrawlerapi import WebCrawlerAPI, UploadS3Action

client = WebCrawlerAPI(api_key="your_api_key")

action = UploadS3Action(
    path="crawls/my-job",
    access_key_id="YOUR_ACCESS_KEY",
    secret_access_key="YOUR_SECRET_KEY",
    bucket="my-bucket",
    endpoint="https://s3.amazonaws.com",  # optional, for S3-compatible stores
)

job = client.crawl(
    url="https://example.com",
    output_formats=["markdown"],
    items_limit=10,
    actions=action,
)
```

## Filtering crawled URLs

```python
job = client.crawl(
    url="https://example.com",
    output_formats=["markdown"],
    items_limit=50,
    whitelist_regexp=".*blog.*",      # only crawl blog pages
    blacklist_regexp=".*tag.*",       # skip tag pages
    max_depth=3,
)
```

## Respecting robots.txt

```python
job = client.crawl(
    url="https://example.com",
    output_formats=["markdown"],
    respect_robots_txt=True,
)
```

## Main content only

Strip navigation, ads, sidebars, and footers — useful for articles and blog posts.

```python
result = client.scrape(
    url="https://example.com/article",
    output_formats=["markdown"],
    main_content_only=True,
)
```
