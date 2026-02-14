"""Web scraper tool using Crawl4AI for deep website scraping.

Used by the Research Orchestrator to scrape competitor pages —
pricing, features, about, blog — and return clean markdown content.
"""

import asyncio
from typing import Optional
from urllib.parse import urljoin, urlparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default subpages to scrape per domain (per PRD §6.2)
DEFAULT_SUBPAGES = ["/", "/about", "/pricing", "/product", "/products", "/blog"]

# Content chunking constants (per PRD §3.2)
CHUNK_SIZE = 15_000  # 15KB per chunk
CHUNK_OVERLAP = 2_000  # 2KB overlap


class WebScraperTool:
    """Scrape websites using Crawl4AI and return clean markdown content."""

    async def scrape_url(self, url: str) -> dict:
        """Scrape a single URL and return its content.

        Args:
            url: The URL to scrape.

        Returns:
            Dict with keys: url, markdown, title, success.
        """
        logger.info(f"Scraping: {url}")
        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(
                    word_count_threshold=50,
                    excluded_tags=["nav", "footer", "header"],
                    exclude_external_links=True,
                )
                result = await crawler.arun(url=url, config=config)

            if result.success:
                logger.info(
                    f"Scraped {url}: {len(result.markdown_v2.raw_markdown)} chars"
                )
                return {
                    "url": url,
                    "markdown": result.markdown_v2.raw_markdown,
                    "title": result.metadata.get("title", "") if result.metadata else "",
                    "success": True,
                }
            else:
                logger.warning(f"Scrape failed for {url}: {result.error_message}")
                return {
                    "url": url,
                    "markdown": "",
                    "title": "",
                    "success": False,
                }
        except Exception as e:
            logger.error(f"Scrape error for {url}: {e}")
            return {
                "url": url,
                "markdown": "",
                "title": "",
                "success": False,
            }

    async def scrape_domain(
        self,
        base_url: str,
        subpages: Optional[list[str]] = None,
    ) -> list[dict]:
        """Scrape multiple subpages of a domain.

        Args:
            base_url: Base URL of the website (e.g. "https://example.com").
            subpages: List of paths to scrape. Defaults to DEFAULT_SUBPAGES.

        Returns:
            List of scrape result dicts (only successful ones).
        """
        if subpages is None:
            subpages = DEFAULT_SUBPAGES

        # Normalize base_url
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        urls = [urljoin(base, page) for page in subpages]
        # Deduplicate while preserving order
        urls = list(dict.fromkeys(urls))

        logger.info(f"Scraping domain {base}: {len(urls)} pages")

        results = []
        for url in urls:
            result = await self.scrape_url(url)
            if result["success"]:
                results.append(result)

        logger.info(f"Successfully scraped {len(results)}/{len(urls)} pages")
        return results

    def scrape_url_sync(self, url: str) -> dict:
        """Synchronous wrapper for scrape_url."""
        return asyncio.run(self.scrape_url(url))

    def scrape_domain_sync(
        self,
        base_url: str,
        subpages: Optional[list[str]] = None,
    ) -> list[dict]:
        """Synchronous wrapper for scrape_domain."""
        return asyncio.run(self.scrape_domain(base_url, subpages))


def chunk_content(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split large text into overlapping chunks for LLM processing.

    Args:
        text: The text to chunk.
        chunk_size: Maximum characters per chunk.
        overlap: Character overlap between consecutive chunks.

    Returns:
        List of text chunks.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks
