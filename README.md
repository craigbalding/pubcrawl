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

### Demo Script Usage

The `demo_pubcrawl.py` script provides a convenient way to test PubCrawl with various options:

```
python demo_pubcrawl.py [options]
```

Options:
- `--debug`: Enable debug mode (opens browser for inspection)
- `--minimal`: Run minimal version with summarized output

Examples:

1. Full output:
   ```
   python demo_pubcrawl.py
   ```

2. Minimal output:
   ```
   python demo_pubcrawl.py --minimal
   ```

3. Debug mode with full output:
   ```
   python demo_pubcrawl.py --debug
   ```

4. Debug mode with minimal output:
   ```
   python demo_pubcrawl.py --minimal --debug
   ```

## Output

The tool generates output in JSON format (default) or CSV format. The JSON output includes:

- Metadata about the scraping session (URL, user agent, screen size, etc.)
- Captured responses matching the specified URL pattern
- Error summary (Cloudflare protection encounters, missing content errors, other errors)

In minimal mode, the output is a summary including:
- Number of responses captured
- Total bytes received
- A brief summary of each response (URL, status, content length)

## Advanced Usage

### Filtering responses by IP

You can chain PubCrawl with `jq` and `grep` to identify responses from host IPs that are not in your scope:

```bash
pubcrawl https://example.com ".*" | \
jq -c '.responses[] | {url: .matched_url, status: .status, ip: .server_ip}' | \
grep -vFf scope.ips
```

This command will:
1. Run PubCrawl on https://example.com, capturing all URLs
2. Use `jq` to extract the URL, status, and server IP for each response
3. Use `grep` to filter out any responses with IPs listed in the `scope.ips` file

Make sure to create a `scope.ips` file with one IP address per line for the hosts that are in scope.

## Questions? Bug reports?

Open an Issue with details.
