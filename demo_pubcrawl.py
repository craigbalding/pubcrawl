#!/usr/bin/env python3

from pubcrawl.main import run_pubcrawl

def main():
    # Example usage of pubcrawl as a module
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
        print("Scraping completed successfully.")
        print(f"Number of responses captured: {len(result['responses'])}")
        print(f"Total bytes received: {result['metadata']['total_bytes_received']}")

if __name__ == "__main__":
    main()
