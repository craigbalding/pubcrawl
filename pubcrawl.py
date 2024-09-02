#!/usr/bin/env python3
import argparse
import json
import sys
import random
import re
import requests
import signal
import yaml
from playwright.sync_api import sync_playwright, TimeoutError, Error as PlaywrightError
import csv
import time
import os
import logging
import datetime

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
error_counts = {
    "cloudflare": 0,
    "content_missing": 0,
    "other": 0
}

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="PubCrawl: A CLI tool for scraping public websites using Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
Example url-patterns:
  "api/v1"                 - Matches any URL containing this substring
  "\.json$"                - Matches URLs ending with .json
  "^https://api\."         - Matches URLs starting with https://api.
  "api/(v1|v2)/data"       - Matches api/v1/data or api/v2/data
  "users/\d+"              - Matches 'users' followed by one or more digits
  "data\?format=json"      - Matches 'data' endpoint with json format

Example usage:
  %(prog)s https://example.com "api/v1" --debug
  %(prog)s https://example.com "\.json$" --screen-size 1920x1080
  %(prog)s https://api.example.com "users/\d+" --user-agent "Custom User Agent"
  %(prog)s https://example.com ".*" --include-binary --content-limit 50000
  %(prog)s --profile myprofile.yaml
  %(prog)s https://example.com "api/v1" --output-file data.json --output-format json
  %(prog)s https://example.com "api/v1" --proxy socks5://127.0.0.1:9150
  %(prog)s https://example.com "api/v1" --output-file data.csv --output-format csv --timeout 60000 --retries 5 --proxy socks5://127.0.0.1:9150 --include-headers --save-profile my_complex_scrape
  %(prog)s https://example.com ".*" | jq -c '.responses[] | {url: .matched_url, status: .status, ip: .server_ip}'
  %(prog)s https://example.com ".*" | jq -c '.responses[] | {url: .matched_url, status: .status, ip: .server_ip}' | grep -vFf approved_ips.txt
        """
    )
    parser.add_argument("url", nargs="?", help="Entry URL to scrape")
    parser.add_argument("url_pattern", nargs="?", help="Pattern to match in URLs for capturing responses")

    # Browser configuration
    browser_group = parser.add_argument_group('Browser Configuration')
    browser_group.add_argument("--user-agent", help="User agent string (default uses bundled browser default)")
    browser_group.add_argument("--screen-size", help="Screen size (default: 1440x900)")
    browser_group.add_argument("--proxy", help="Proxy server to use (e.g., socks5://127.0.0.1:9150)")

    # Scraping behavior
    scraping_group = parser.add_argument_group('Scraping Behavior')
    scraping_group.add_argument("--timeout", type=int, default=20000, help="Timeout for page load in milliseconds")
    scraping_group.add_argument("--retries", type=int, default=3, help="Number of retries for failed requests")
    scraping_group.add_argument("--wait-until", default="networkidle", 
                        help="Comma-separated list of wait until options: "
                             "domcontentloaded, load, networkidle, commit. "
                             "(default: networkidle)")
    scraping_group.add_argument("--post-response-wait", type=float, 
                        help="Wait time after page load in seconds (default: 0.7-1.3 seconds)")
    scraping_group.add_argument("--content-limit", type=int, default=256, 
                        help="Maximum number of bytes to include for any content type. Use 0 for full content. (default: 256)")
    scraping_group.add_argument("--include-binary", action="store_true",
                        help="Include binary content (images, fonts, etc.) in the output")

    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument("--output-file", help="Path to output file")
    output_group.add_argument("--output-format", choices=['json', 'csv'], default='json', help="Output format (json or csv)")
    output_group.add_argument("--include-headers", action="store_true", help="Include HTTP response headers in the output")
    output_group.add_argument("--include-tls", action="store_true", help="Include TLS data in the output")

    # Misc options
    misc_group = parser.add_argument_group('Miscellaneous')
    misc_group.add_argument("--debug", action="store_true", help="Enable debug mode")
    misc_group.add_argument("--profile", help="Path to the profile YAML file")
    misc_group.add_argument("--save-profile", help="Save current configuration as a named profile")

    return parser

def load_profile(profile_path):
    try:
        with open(profile_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading profile: {str(e)}", file=sys.stderr)
        sys.exit(1)

def save_profile(args, profile_name):
    profile_dir = os.path.expanduser("~/.pubcrawl_profiles")
    os.makedirs(profile_dir, exist_ok=True)
    profile_path = os.path.join(profile_dir, f"{profile_name}.yaml")
    
    profile_data = {k: v for k, v in vars(args).items() if v is not None}
    profile_data.pop('save_profile', None)
    
    try:
        with open(profile_path, 'w') as file:
            yaml.dump(profile_data, file)
        print(f"Profile saved as {profile_path}")
    except Exception as e:
        print(f"Error saving profile: {str(e)}", file=sys.stderr)
        sys.exit(1)

def merge_args_with_profile(args, profile):
    merged = vars(args).copy()
    for key, value in profile.items():
        if merged.get(key) is None:
            merged[key] = value
    return argparse.Namespace(**merged)

def write_output(data, output_file, output_format):
    if output_file:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if output_format == 'json':
                json.dump(data, f, indent=2)
            elif output_format == 'csv':
                writer = csv.writer(f)
                writer.writerow(['url', 'content'])
                for response in data['responses']:
                    writer.writerow([response['matched_url'], json.dumps(response['content'])])
    else:
        print(json.dumps(data, indent=2))

def signal_handler(signum, frame):
    raise KeyboardInterrupt

def read_content_in_chunks(response, chunk_size=8192):
    body = response.body()
    for i in range(0, len(body), chunk_size):
        yield body[i:i+chunk_size]

def truncate_content(response, content_limit):
    content = b''
    for chunk in read_content_in_chunks(response):
        content += chunk
        if len(content) >= content_limit:
            return content[:content_limit] + b'...'
    return content

def extract_content(response, content_limit):
    content_type = str(response.header_value("content-type")).lower()
    
    if content_limit > 0:
        content = truncate_content(response, content_limit)
    else:
        content = response.body()

    if 'json' in content_type:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content.decode('utf-8', errors='replace')
    elif any(t in content_type for t in ['text', 'javascript', 'css', 'html', 'xml', 'plain', 'xhtml', 'svg']):
        return content.decode('utf-8', errors='replace')
    else:
        return content.hex()

def create_response_data(response, content, include_headers, include_tls):
    server_addr = response.server_addr()
    data = {
        "matched_url": response.url,
        "content_type": str(response.header_value("content-type")),
        "content_length": len(response.body()),
        "content": content,
        "status": response.status,
        "status_text": response.status_text,
        "server_ip": server_addr["ipAddress"] if server_addr else None,
        "server_port": server_addr["port"] if server_addr else None
    }
    if include_headers:
        data["headers"] = response.headers
    if include_tls:
        data["security_details"] = response.security_details()
    return data

def handle_response(response, url_pattern, content_limit, include_binary, include_headers, include_tls):
    if not url_pattern.search(response.url):
        return None
    
    content_type = str(response.header_value("content-type")).lower()
    is_binary = not any(t in content_type for t in ['text', 'json', 'javascript', 'css', 'html', 'xml', 'plain', 'xhtml', 'svg'])
    
    if is_binary and not include_binary:
        return None
    
    try:
        content = extract_content(response, content_limit)
        if content is None:
            return None
        response_data = create_response_data(response, content, include_headers, include_tls)
        return response_data, len(response.body())  # Return actual content length
    except PlaywrightError as e:
        handle_playwright_error(e, response.url)
    except Exception as e:
        handle_general_error(e, response.url)
    return None

def handle_playwright_error(error, url):
    error_message = str(error)
    if "Cloudflare" in error_message:
        logging.warning(f"Cloudflare protection detected for {url}")
        error_counts["cloudflare"] += 1
    elif "Missing content of resource" in error_message:
        logging.warning(f"Unable to access response body for {url}. Content may be dynamic or protected.")
        error_counts["content_missing"] += 1
    else:
        logging.error(f"Playwright error processing response from {url}: {error_message}")
        error_counts["other"] += 1

def handle_general_error(error, url):
    logging.error(f"Error processing response from {url}: {str(error)}")
    error_counts["other"] += 1

def setup_browser(args):
    playwright = sync_playwright().start()
    browser_type = playwright.webkit  # Using WebKit for M1 Mac optimization

    browser_args = {
        "headless": not args.debug
    }

    if args.debug:
        browser_args["slow_mo"] = 100
        browser_args["devtools"] = True

    if args.proxy:
        browser_args["proxy"] = {"server": args.proxy}

    browser = browser_type.launch(**browser_args)

    screen_size = args.screen_size or "1440x900"
    width, height = map(int, screen_size.split('x'))

    context_options = {
        "viewport": {"width": width, "height": height}
    }

    if args.user_agent:
        context_options["user_agent"] = args.user_agent

    context = browser.new_context(**context_options)
    page = context.new_page()
    actual_user_agent = page.evaluate("() => navigator.userAgent")

    return browser, page, actual_user_agent, playwright

def navigate_with_retry(page, url, timeout, retries, wait_until, post_response_wait, metadata):
    for attempt in range(retries):
        try:
            metadata["requests_sent"] += 1
            page.goto(url, timeout=timeout, wait_until=wait_until)

            # Only a bot would close the browser immediately...
            time.sleep(post_response_wait)

            return True
        except TimeoutError:
            if attempt < retries - 1:
                print(f"Timeout occurred. Retrying... (Attempt {attempt + 1}/{retries})", file=sys.stderr)
                wait_time = random.uniform(1.3, 3.1)
                print(f"Waiting for {wait_time:.2f} seconds before retrying...", file=sys.stderr)
                time.sleep(wait_time)
            else:
                print(f"Error: Max retries reached. Unable to load the page.", file=sys.stderr)
                return False

def main(args):
    browser = None
    playwright = None
    try:
        signal.signal(signal.SIGINT, signal_handler)
  
        if args.profile:
            profile = load_profile(args.profile)
            args = merge_args_with_profile(args, profile)
        
        if args.save_profile:
            save_profile(args, args.save_profile)
            print("Profile saved. Exiting.")
            return
        
        if not args.url or not args.url_pattern:
            print("Error: URL and URL pattern are required. Use --help for usage information.", file=sys.stderr)
            return

        browser, page, actual_user_agent, playwright = setup_browser(args)

        start_time = time.time()
        start_time_iso = datetime.datetime.fromtimestamp(start_time).isoformat()
        metadata = {
            "url": args.url,
            "url_pattern": args.url_pattern,
            "user_agent": actual_user_agent,
            "screen_size": args.screen_size or "1440x900",
            "debug_mode": args.debug,
            "proxy": args.proxy,
            "first_request_time": {
                "unix": start_time,
                "iso": start_time_iso
            },
            "requests_sent": 0,
            "total_bytes_received": 0,
            "error_summary": {
                "cloudflare_protection": 0,
                "missing_content": 0,
                "other_errors": 0
            }
        }

        url_pattern = re.compile(args.url_pattern)

        all_responses = []
        responses_processed = 0
        total_responses = 0

        def response_handler(response):
            nonlocal responses_processed, total_responses
            total_responses += 1
            try:
                result = handle_response(response, url_pattern, args.content_limit, args.include_binary, args.include_headers, args.include_tls)
                if result:
                    response_data, actual_content_length = result
                    all_responses.append(response_data)
                    metadata["total_bytes_received"] += actual_content_length
            except Exception as e:
                logging.error(f"Error in response_handler: {str(e)}")
            finally:
                responses_processed += 1

        page.on("response", response_handler)

        # Set default wait_until option to 'networkidle'
        default_wait_until = 'networkidle'

        # Check if the user provided the --wait_until option
        if args.wait_until:
            # Parse wait_until options provided by the user
            wait_until_options = [option.strip() for option in args.wait_until.split(',')]
            valid_options = {'domcontentloaded', 'load', 'networkidle', 'commit'}
            wait_until_options = [option for option in wait_until_options if option in valid_options]

            if not wait_until_options:
                print("Warning: No valid wait_until options provided. Using default 'networkidle'.")
                wait_until_options = default_wait_until
            elif len(wait_until_options) == 1:
                # Convert the list with one valid option to a single string
                wait_until_options = wait_until_options[0]
        else:
            # If no --wait_until is provided, use the default
            wait_until_options = default_wait_until

        post_response_wait = args.post_response_wait or random.uniform(0.7, 1.3)
        
        if not navigate_with_retry(page, args.url, args.timeout, args.retries, wait_until_options, post_response_wait, metadata):
            return

        navigation_complete_time = time.time()
        processing_complete = False

        # Wait for all responses to be processed
        timeout = time.time() + 60  # 60 seconds timeout
        while not processing_complete:
            if time.time() > timeout:
                logging.warning("Timeout waiting for all responses to be processed")
                break
            if responses_processed >= total_responses and time.time() - navigation_complete_time > 5:
                processing_complete = True
            time.sleep(0.1)

        logging.info(f"Processed {responses_processed} out of {total_responses} responses")

        if args.debug:
            input("Press Enter to close the browser...")

        output = {
            "metadata": metadata,
            "responses": all_responses
        }

        # Update error summary in metadata
        output["metadata"]["error_summary"]["cloudflare_protection"] = error_counts["cloudflare"]
        output["metadata"]["error_summary"]["missing_content"] = error_counts["content_missing"]
        output["metadata"]["error_summary"]["other_errors"] = error_counts["other"]
    
        write_output(output, args.output_file, args.output_format)

        # Print error summary to stderr
        print("\nError Summary:", file=sys.stderr)
        print(f"Cloudflare protection encounters: {error_counts['cloudflare']}", file=sys.stderr)
        print(f"Missing content errors: {error_counts['content_missing']}", file=sys.stderr)
        print(f"Other errors: {error_counts['other']}", file=sys.stderr)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Cleaning up...", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {str(e)}", file=sys.stderr)
    finally:
        if processing_complete:
            logging.info("All responses processed. Closing browser and stopping Playwright")
        else:
            logging.warning("Closing browser before all responses were processed")
        
        if browser:
            try:
                browser.close()
            except Exception as e:
                print(f"Error closing browser: {str(e)}", file=sys.stderr)
        if playwright:
            try:
                playwright.stop()
            except Exception as e:
                print(f"Error stopping Playwright: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    parser = parse_arguments()
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    main(args)
