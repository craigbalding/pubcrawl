#!/usr/bin/env python3

from pubcrawl import run_pubcrawl

def main():
    # Example usage of pubcrawl as a module with minimal arguments
    result = run_pubcrawl(
        url="https://example.com",
        url_pattern=".*"
    )

    if isinstance(result, dict) and 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("Scraping completed successfully.")
        print(f"Number of responses captured: {len(result['responses'])}")
        print(f"Total bytes received: {result['metadata']['total_bytes_received']}")

    # You can also override defaults if needed:
    # result = run_pubcrawl(
    #     url="https://example.com",
    #     url_pattern=".*",
    #     debug=True,
    #     content_limit=1000
    # )

if __name__ == "__main__":
    main()
