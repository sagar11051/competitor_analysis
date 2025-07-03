import os
from firecrawl import FirecrawlApp, ScrapeOptions
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()


class FirecrawlService:
    def __init__(self):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("Missing FIRECRAWL_API_KEY environment variable")
        self.app = FirecrawlApp(api_key=api_key)

    def scrape_company_website(self, url: str) -> Optional[str]:
        """
        Scrape the main pages of a company website (homepage, about, products, blog) and return combined markdown content.
        """
        pages = [url, f"{url.rstrip('/')}/about", f"{url.rstrip('/')}/products", f"{url.rstrip('/')}/blog"]
        combined_content = ""
        for page_url in pages:
            try:
                result = self.app.scrape_url(page_url, formats=["markdown"])
                if result and hasattr(result, "markdown"):
                    combined_content += result.markdown + "\n\n"
            except Exception:
                continue
        return combined_content if combined_content else None

    def search_competitors(self, company_profile: dict, num_results: int = 10) -> List[dict]:
        """
        Search for potential competitors using company profile fields (business model, target market, key services).
        Returns a list of search result dicts.
        """
        query_parts = []
        if company_profile.get("business_model"):
            query_parts.append(company_profile["business_model"])
        if company_profile.get("target_market"):
            query_parts.append(company_profile["target_market"])
        if company_profile.get("key_services"):
            query_parts.extend(company_profile["key_services"])
        query = " ".join(query_parts) + " competitor names and website links"
        try:
            result = self.app.search(
                query=query,
                limit=num_results,
                scrape_options=ScrapeOptions(formats=["markdown"])
            )
            return result.data if hasattr(result, "data") else []
        except Exception as e:
            print(e)
            return []

    def scrape_competitor_website(self, url: str) -> Optional[str]:
        """
        Scrape main pages of a competitor (homepage, product, pricing, about, blog, etc.) and return combined markdown content.
        """
        pages = [url, f"{url.rstrip('/')}/product", f"{url.rstrip('/')}/pricing", f"{url.rstrip('/')}/about", f"{url.rstrip('/')}/blog"]
        combined_content = ""
        for page_url in pages:
            try:
                result = self.app.scrape_url(page_url, formats=["markdown"])
                if result and hasattr(result, "markdown"):
                    combined_content += result.markdown + "\n\n"
            except Exception:
                continue
        return combined_content if combined_content else None

    def search_companies(self, query: str, num_results: int = 5):
        try:
            result = self.app.search(
                query=f"{query} company pricing",
                limit=num_results,
                scrape_options=ScrapeOptions(
                    formats=["markdown"]
                )
            )
            return result
        except Exception as e:
            print(e)
            return []

    def scrape_company_pages(self, url: str):
        try:
            result = self.app.scrape_url(
                url,
                formats=["markdown"]
            )
            return result
        except Exception as e:
            print(e)
            return None