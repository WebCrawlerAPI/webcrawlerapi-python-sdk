# Testing Guide for WebCrawlerAPI Python SDK

This guide explains how to run tests for the WebCrawlerAPI Python SDK. The test suite uses pytest, the most popular Python testing framework, with comprehensive coverage of all client methods and models.

## Prerequisites

Make sure you have Python 3.6+ installed and the SDK dependencies are available.

## Installation

1. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Install the SDK in development mode:**
   ```bash
   pip install -e .
   ```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Tests with Verbose Output
```bash
pytest -v
```

### Run Specific Test Files
```bash
# Test only client functionality
pytest tests/test_client.py

# Test only models
pytest tests/test_models.py
```

### Run Specific Test Classes or Methods
```bash
# Run specific test class
pytest tests/test_client.py::TestWebCrawlerAPI

# Run specific test method
pytest tests/test_client.py::TestWebCrawlerAPI::test_crawl_async_success
```

### Run Tests with Coverage Report
```bash
pip install pytest-cov
pytest --cov=webcrawlerapi --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

## Test Structure

### Test Files
- `tests/test_client.py` - Tests for the main WebCrawlerAPI client class
- `tests/test_models.py` - Tests for data models (Job, JobItem, ScrapeResponse, etc.)

### Test Categories

#### Client Tests (`test_client.py`)
- **Initialization**: Testing client setup with API keys and base URLs
- **Async Methods**: Testing `crawl_async()` and `scrape_async()` methods
- **Synchronous Methods**: Testing `crawl()` and `scrape()` with polling logic
- **Job Management**: Testing `get_job()` and `cancel_job()` methods
- **Error Handling**: Testing HTTP errors and API error responses
- **Actions**: Testing S3 upload actions and other integrations

#### Model Tests (`test_models.py`)
- **Datetime Parsing**: Testing various datetime formats from API responses
- **Dataclass Models**: Testing simple response models
- **Job Model**: Testing job creation, status tracking, and terminal states
- **JobItem Model**: Testing item properties and lazy content loading
- **Content Fetching**: Testing content retrieval based on scrape type

## Test Features

### Mocking
The tests use the `responses` library to mock HTTP requests, ensuring tests run quickly and don't depend on external services.

### Fixtures
Pytest fixtures provide reusable test data and mock objects:
- `client`: Pre-configured WebCrawlerAPI client
- `mock_job_data`: Sample job data for testing
- `job_item_data`: Sample job item data

### Coverage Areas
- ✅ All public methods of `WebCrawlerAPI` class
- ✅ All model classes and their properties
- ✅ Error handling and edge cases
- ✅ Polling logic and timeouts
- ✅ Content lazy loading
- ✅ Datetime parsing utilities
- ✅ Action system (S3 uploads, etc.)

## Best Practices

### Running Tests During Development
```bash
# Run tests in watch mode (requires pytest-watch)
pip install pytest-watch
ptw
```

### Testing Specific Functionality
```bash
# Test only crawling functionality
pytest -k "crawl"

# Test only scraping functionality  
pytest -k "scrape"

# Test only error cases
pytest -k "error"
```

### Performance Testing
```bash
# Run tests with timing information
pytest --durations=10
```

## Continuous Integration

The test suite is designed to run in CI environments. All tests use mocked HTTP requests and don't require external dependencies or API keys.

Example CI configuration:
```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install -r requirements-dev.txt

- name: Run tests
  run: pytest --cov=webcrawlerapi --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v1
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure to install the package in development mode with `pip install -e .`

2. **Missing Dependencies**: Install test dependencies with `pip install -r requirements-dev.txt`

3. **Path Issues**: Run tests from the project root directory

### Debug Mode
```bash
# Run with Python debugger on failures
pytest --pdb

# Run with detailed output
pytest -s -v
```

## Adding New Tests

When adding new functionality to the SDK, please add corresponding tests:

1. **Client Methods**: Add tests to `test_client.py`
2. **Models**: Add tests to `test_models.py`
3. **Use Fixtures**: Reuse existing fixtures when possible
4. **Mock HTTP**: Use `responses` library for HTTP mocking
5. **Test Edge Cases**: Include error conditions and edge cases

Example test structure:
```python
@responses.activate
def test_new_method(self, client):
    """Test description."""
    # Mock API response
    responses.add(
        responses.POST,
        "https://api.test.com/v1/endpoint",
        json={"result": "success"},
        status=200
    )
    
    # Call method
    result = client.new_method()
    
    # Assert results
    assert result.status == "success"
```