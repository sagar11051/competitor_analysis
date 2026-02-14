"""Tavily Search tool for competitor discovery and market research.

Wraps tavily-python to provide a simple search interface used by the
Research Orchestrator's research_agent node.
"""

from typing import Optional

from tavily import TavilyClient

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TavilySearchTool:
    """Search the web for competitor and market intelligence using Tavily."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.tavily_api_key
        self._client: Optional[TavilyClient] = None

    @property
    def client(self) -> TavilyClient:
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "Tavily API key not configured. Set TAVILY_API_KEY in .env"
                )
            self._client = TavilyClient(api_key=self.api_key)
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
    ) -> list[dict]:
        """Run a Tavily search and return results.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.
            search_depth: "basic" or "advanced".
            include_domains: Only include results from these domains.
            exclude_domains: Exclude results from these domains.

        Returns:
            List of result dicts with keys: title, url, content, score.
        """
        logger.info(f"Tavily search: '{query}' (max_results={max_results})")

        kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains
        if exclude_domains:
            kwargs["exclude_domains"] = exclude_domains

        try:
            response = self.client.search(**kwargs)
            results = response.get("results", [])
            logger.info(f"Tavily returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            raise

    def search_competitors(self, company_name: str, industry: str = "") -> list[dict]:
        """Convenience method to find competitors for a company.

        Args:
            company_name: Name of the company to find competitors for.
            industry: Optional industry context for better results.

        Returns:
            List of search result dicts.
        """
        query = f"{company_name} competitors alternatives"
        if industry:
            query += f" in {industry}"
        return self.search(query, max_results=10, search_depth="advanced")

    def search_company_info(self, company_url: str) -> list[dict]:
        """Search for general information about a company by URL.

        Args:
            company_url: URL of the company's website.

        Returns:
            List of search result dicts.
        """
        query = f"site:{company_url} company overview products pricing"
        return self.search(query, max_results=5, include_domains=[company_url])
