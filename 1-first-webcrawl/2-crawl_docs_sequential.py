import asyncio
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.models import CrawlResult
import requests
from xml.etree import ElementTree

def get_pydantic_ai_docs_urls():
    sitemap_url = "https://ai.pydantic.dev/sitemap.xml"
    try:
        resp = requests.get(sitemap_url)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        return [loc.text for loc in root.findall('.//ns:loc', ns)]
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

async def crawl_with_batch(urls: List[str]):
    print("\n=== Batch Crawling with Uniform Config ===")

    # The BrowserConfig object is still used for browser settings.
    browser_config = BrowserConfig(
        headless=True,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )

    # To work around the TypeError, we explicitly create the strategy object
    # with the browser_config and pass the completed strategy to the crawler.
    # This avoids the bug in the AsyncWebCrawler constructor.
    strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_config)
    async with AsyncWebCrawler(crawler_strategy=strategy) as crawler:
        # The `arun_many` method in this version of the library returns an
        # async generator. We iterate over it with `async for` to process
        # results as they become available. This is also more memory-efficient.
        async for result in crawler.arun_many(
            urls=urls,
            markdown_generator=DefaultMarkdownGenerator(),
            cache_mode="bypass",  # CacheMode enum is replaced by string literals
        ):
            # The type of `result` in each iteration is `CrawlResult`.
            if result.success:
                # The .markdown attribute is an object; we access .raw_markdown for the text
                print(f"[OK] {result.url} — Markdown length: {len(result.markdown.raw_markdown)}")
            else:
                print(f"[FAIL] {result.url} — Error: {result.error_message}")

async def main():
    urls = get_pydantic_ai_docs_urls()
    if not urls:
        print("No URLs found to crawl")
        return
    print(f"Found {len(urls)} URLs to crawl")
    await crawl_with_batch(urls)

if __name__ == "__main__":
    asyncio.run(main())
