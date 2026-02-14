"""Tests for src.tools — Tavily search and Crawl4AI web scraper."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.tavily_search import TavilySearchTool
from src.tools.web_scraper import WebScraperTool, chunk_content


# ── TavilySearchTool ─────────────────────────────────────────────────


def test_tavily_is_configured_with_key():
    tool = TavilySearchTool(api_key="test-key")
    assert tool.is_configured() is True


@patch("src.tools.tavily_search.settings")
def test_tavily_is_not_configured_without_key(mock_settings):
    mock_settings.tavily_api_key = ""
    tool = TavilySearchTool(api_key="")
    assert tool.is_configured() is False


@patch("src.tools.tavily_search.settings")
def test_tavily_client_raises_without_key(mock_settings):
    mock_settings.tavily_api_key = ""
    tool = TavilySearchTool(api_key="")
    with pytest.raises(ValueError, match="Tavily API key not configured"):
        _ = tool.client


def test_tavily_search_calls_client():
    tool = TavilySearchTool(api_key="test-key")
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {"title": "Result 1", "url": "https://example.com", "content": "test", "score": 0.9}
        ]
    }
    tool._client = mock_client

    results = tool.search("test query", max_results=3)
    assert len(results) == 1
    assert results[0]["title"] == "Result 1"
    mock_client.search.assert_called_once_with(
        query="test query", max_results=3, search_depth="basic"
    )


def test_tavily_search_competitors_builds_query():
    tool = TavilySearchTool(api_key="test-key")
    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}
    tool._client = mock_client

    tool.search_competitors("Acme Corp", industry="SaaS")
    call_args = mock_client.search.call_args
    assert "Acme Corp competitors alternatives" in call_args.kwargs.get("query", call_args[1].get("query", ""))


def test_tavily_search_with_domain_filters():
    tool = TavilySearchTool(api_key="test-key")
    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}
    tool._client = mock_client

    tool.search("test", include_domains=["example.com"], exclude_domains=["spam.com"])
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["include_domains"] == ["example.com"]
    assert call_kwargs["exclude_domains"] == ["spam.com"]


# ── WebScraperTool ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scraper_scrape_url_success():
    scraper = WebScraperTool()
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.markdown_v2.raw_markdown = "# Hello World"
    mock_result.metadata = {"title": "Test Page"}

    mock_crawler_instance = AsyncMock()
    mock_crawler_instance.arun.return_value = mock_result
    mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
    mock_crawler_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("src.tools.web_scraper.AsyncWebCrawler", return_value=mock_crawler_instance):
        result = await scraper.scrape_url("https://example.com")

    assert result["success"] is True
    assert result["markdown"] == "# Hello World"
    assert result["title"] == "Test Page"


@pytest.mark.asyncio
async def test_scraper_scrape_url_failure():
    scraper = WebScraperTool()
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.error_message = "Connection refused"

    mock_crawler_instance = AsyncMock()
    mock_crawler_instance.arun.return_value = mock_result
    mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
    mock_crawler_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("src.tools.web_scraper.AsyncWebCrawler", return_value=mock_crawler_instance):
        result = await scraper.scrape_url("https://fail.com")

    assert result["success"] is False
    assert result["markdown"] == ""


# ── chunk_content ────────────────────────────────────────────────────


def test_chunk_small_content_returns_single_chunk():
    text = "Short text"
    chunks = chunk_content(text, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_large_content_creates_multiple_chunks():
    text = "A" * 100
    chunks = chunk_content(text, chunk_size=30, overlap=10)
    assert len(chunks) > 1
    # Each chunk should be at most chunk_size
    for c in chunks:
        assert len(c) <= 30


def test_chunk_overlap_preserves_content():
    text = "ABCDEFGHIJ" * 5  # 50 chars
    chunks = chunk_content(text, chunk_size=20, overlap=5)
    # Reconstruct: verify no content is lost
    # The end of chunk[i] should overlap with start of chunk[i+1]
    for i in range(len(chunks) - 1):
        overlap_from_current = chunks[i][-5:]
        overlap_from_next = chunks[i + 1][:5]
        assert overlap_from_current == overlap_from_next


def test_chunk_empty_string():
    chunks = chunk_content("", chunk_size=100, overlap=10)
    assert chunks == [""]
