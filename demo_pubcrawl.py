#!/usr/bin/env python3

import json
import argparse
from pubcrawl.main import run_pubcrawl

def main():
    parser = argparse.ArgumentParser(description="Demo script for PubCrawl")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--minimal", action="store_true", help="Run minimal version")
    args = parser.parse_args()

    url = "https://example.com"
    url_pattern = ".*"

    if args.minimal:
        result = run_pubcrawl(
            url=url,
            url_pattern=url_pattern,
            debug=args.debug
        )
    else:
        result = run_pubcrawl(
            url=url,
            url_pattern=url_pattern,
            debug=args.debug,
            output_file="output.json",
            output_format="json",
            screen_size="1920x1080",
            timeout=30000,
            retries=2,
            wait_until="networkidle",
            content_limit=1000,
            include_headers=True,
            user_agent=None,
            proxy=None,
            include_binary=False,
            include_tls=False,
            post_response_wait=None,
            save_profile=None
        )

    if isinstance(result, dict) and 'error' in result:
        print(f"Error: {result['error']}")
    else:
        if args.minimal:
            print("Scraping completed successfully.")
            print(f"Number of responses captured: {len(result['responses'])}")
            print(f"Total bytes received: {result['metadata']['total_bytes_received']}")
            
            print("\nResponse summaries:")
            for response in result['responses']:
                print(f"URL: {response['matched_url']}")
                print(f"Status: {response['status']}")
                print(f"Content Length: {response['content_length']}")
                print("---")
        else:
            print(json.dumps(result, indent=2))

    if args.debug:
        input("Press Enter to close the browser...")

if __name__ == "__main__":
    main()
