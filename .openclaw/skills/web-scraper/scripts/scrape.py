#!/usr/bin/env python3
"""nodriver scraper for Todd. Runs headless Chromium inside Docker.

Usage:
    python3 scrape.py <url>                         # get page text
    python3 scrape.py <url> --html                  # get raw HTML
    python3 scrape.py <url> --selector "div.content" # extract specific elements
    python3 scrape.py <url> --screenshot out.png    # take screenshot
    python3 scrape.py <url> --wait 5                # wait N seconds before capture
    python3 scrape.py <url> --js "document.title"   # run JS and return result
"""

import argparse
import asyncio
import json
import sys

import nodriver as uc


async def main():
    parser = argparse.ArgumentParser(description="Scrape a webpage with nodriver")
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument("--html", action="store_true", help="Return raw HTML instead of text")
    parser.add_argument("--selector", help="CSS selector to extract specific elements")
    parser.add_argument("--screenshot", help="Save screenshot to this path")
    parser.add_argument("--wait", type=int, default=3, help="Seconds to wait for page load (default: 3)")
    parser.add_argument("--js", help="JavaScript expression to evaluate and return")
    args = parser.parse_args()

    browser = await uc.start(
        headless=True,
        no_sandbox=True,
        browser_args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    )

    try:
        page = await browser.get(args.url)
        await page.sleep(args.wait)

        if args.screenshot:
            await page.save_screenshot(args.screenshot)
            print(json.dumps({"screenshot": args.screenshot}))
            return

        if args.js:
            result = await page.evaluate(args.js)
            print(json.dumps({"result": result}))
            return

        if args.selector:
            elements = await page.select_all(args.selector)
            texts = []
            for el in elements:
                if args.html:
                    t = await el.get_html()
                else:
                    t = el.text
                if t and t.strip():
                    texts.append(t.strip())
            print(json.dumps({"count": len(texts), "items": texts}))
            return

        if args.html:
            html = await page.get_content()
            print(html)
        else:
            text = await page.get_content()
            # strip tags for plain text
            import re
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            print(text[:50000])  # cap output to avoid flooding
    finally:
        browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
