# PubCrawl

A one-shot CLI tool to scrape a public URL that depends on JavaScript.

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

## Usage

```
usage: pubcrawl.py [-h] [--user-agent USER_AGENT] [--screen-size SCREEN_SIZE]
                   [--proxy PROXY] [--timeout TIMEOUT] [--retries RETRIES]
                   [--wait-until WAIT_UNTIL] [--post-response-wait POST_RESPONSE_WAIT]
                   [--content-limit CONTENT_LIMIT] [--include-binary]
                   [--output-file OUTPUT_FILE] [--output-format {json,csv}]
                   [--include-headers] [--include-tls] [--debug]
                   [--profile PROFILE] [--save-profile SAVE_PROFILE]
                   [url] [url_pattern]

PubCrawl: A CLI tool for scraping public websites using Playwright

positional arguments:
  url                   Entry URL to scrape
  url_pattern           Pattern to match in URLs for capturing responses

options:
  -h, --help            show this help message and exit

Browser Configuration:
  --user-agent USER_AGENT
                        User agent string (default uses bundled browser default)
  --screen-size SCREEN_SIZE
                        Screen size (default: 1440x900)
  --proxy PROXY         Proxy server to use (e.g., socks5://127.0.0.1:9150)

Scraping Behavior:
  --timeout TIMEOUT     Timeout for page load in milliseconds (default: 20000)
  --retries RETRIES     Number of retries for failed requests (default: 3)
  --wait-until WAIT_UNTIL
                        Comma-separated list of wait until options: domcontentloaded, load, networkidle, commit. (default: networkidle)
  --post-response-wait POST_RESPONSE_WAIT
                        Wait time after page load in seconds (default: 0.7-1.3 seconds)
  --content-limit CONTENT_LIMIT
                        Maximum number of bytes to include for any content type. Use 0 for full content. (default: 256)
  --include-binary      Include binary content (images, fonts, etc.) in the output

Output Options:
  --output-file OUTPUT_FILE
                        Path to output file
  --output-format {json,csv}
                        Output format (json or csv)
  --include-headers     Include HTTP response headers in the output
  --include-tls         Include TLS data in the output

Miscellaneous:
  --debug               Enable debug mode
  --profile PROFILE     Path to the profile YAML file
  --save-profile SAVE_PROFILE
                        Save current configuration as a named profile

Example url-patterns:
  "api/v1"                 - Matches any URL containing this substring
  "\.json$"                - Matches URLs ending with .json
  "^https://api\."         - Matches URLs starting with https://api.
  "api/(v1|v2)/data"       - Matches api/v1/data or api/v2/data
  "users/\d+"              - Matches 'users' followed by one or more digits
  "data\?format=json"      - Matches 'data' endpoint with json format

Example usage:
  pubcrawl.py https://example.com "api/v1" --debug
  pubcrawl.py https://example.com "\.json$" --screen-size 1920x1080
  pubcrawl.py https://api.example.com "users/\d+" --user-agent "Custom User Agent"
  pubcrawl.py https://example.com ".*" --include-binary --content-limit 50000
  pubcrawl.py --profile myprofile.yaml
  pubcrawl.py https://example.com "api/v1" --output-file data.json --output-format json
  pubcrawl.py https://example.com "api/v1" --proxy socks5://127.0.0.1:9150
  pubcrawl.py https://example.com "api/v1" --output-file data.csv --output-format csv --timeout 60000 --retries 5 --proxy socks5://127.0.0.1:9150 --include-headers --save-profile my_complex_scrape
  pubcrawl.py https://example.com ".*" | jq -c '.responses[] | {url: .matched_url, status: .status, ip: .server_ip}'
  pubcrawl.py https://example.com ".*" | jq -c '.responses[] | {url: .matched_url, status: .status, ip: .server_ip}' | grep -vFf approved_ips.txt
```

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install playwright pyyaml requests
   ```
3. Install Playwright browsers:
   ```
   playwright install
   ```

## Running PubCrawl

Run PubCrawl using the syntax shown in the usage section above. For example:

```
python3 pubcrawl.py https://example.com "api/v1" --output-file output.json
```

## Output

The tool generates output in JSON format (default) or CSV format. The JSON output includes:

- Metadata about the scraping session (URL, user agent, screen size, etc.)
- Captured responses matching the specified URL pattern
- Error summary (Cloudflare protection encounters, missing content errors, other errors)

## Questions?  Bug reports?

Open an Issue with details.
