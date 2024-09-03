# PubCrawl

A one-shot CLI tool and importable Python package to scrape a public URL that depends on JavaScript.

## Features

- Scrapes JavaScript-dependent websites using Playwright
- Configurable URL pattern matching for targeted data extraction
- Customizable user agent and screen size
- Debug mode for troubleshooting
- Profile support for saving and loading configurations
- Adjustable timeout and retry settings
- Output in JSON or CSV format
- Proxy support
- Error handling and reporting
- Can be used as a CLI tool or imported as a Python package

## Installation

1. Clone this repository
2. Install the package in editable mode:
   ```
   pip install -e /path/to/pubcrawl
   ```
3. Install Playwright browsers:
   ```
   playwright install
   ```

## Usage

### As a CLI tool

Run PubCrawl using the following syntax:

```
pubcrawl [options] url url_pattern
```

For example:

```
pubcrawl https://example.com "api/v1" --output-file output.json
```

For a full list of options, run:

```
pubcrawl --help
```

### As an importable package

You can also use PubCrawl as an importable package in your Python scripts:

```python
from pubcrawl import run_pubcrawl

result = run_pubcrawl(
    url="https://example.com",
    url_pattern=".*",
    debug=True,
    output_file="output.json",
    output_format="json",
    screen_size="1920x1080",
    timeout=30000,
    retries=2,
    wait_until="networkidle",
    content_limit=1000,
    include_headers=True
)

print(f"Number of responses captured: {len(result['responses'])}")
print(f"Total bytes received: {result['metadata']['total_bytes_received']}")
```

For a complete example, see the `demo_pubcrawl.py` script in the repository.

## Output

The tool generates output in JSON format (default) or CSV format. The JSON output includes:

- Metadata about the scraping session (URL, user agent, screen size, etc.)
- Captured responses matching the specified URL pattern
- Error summary (Cloudflare protection encounters, missing content errors, other errors)

## Questions?  Bug reports?

Open an Issue with details.
