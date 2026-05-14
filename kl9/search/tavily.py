"""
9R-2.1 — Tavily Search Provider

Tavily Search API: search + extract (full page content).
Optimized for academic/primary source retrieval.

API tiers:
  - search: returns snippets + URLs
  - extract: downloads full page content for given URLs

Configuration:
  api_key: Tavily API key
  search_depth: "basic" (fast) or "advanced" (deeper, more results)
  include_domains: list of domains to prioritize (e.g. arxiv.org, scholar.google.com)
  exclude_domains: list of domains to exclude (e.g. wikipedia.org secondary sources)
"""

from __future__ import annotations

from typing import Any

import aiohttp

from ..models import SearchProvider, SearchResult, SourceWeight

TAVILY_API_BASE = "https://api.tavily.com"


class TavilyProvider(SearchProvider):
    NAME = "tavily"
    BASE_URL = TAVILY_API_BASE

    def __init__(
        self,
        api_key: str = "",
        *,
        base_url: str | None = None,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
    ):
        super().__init__(api_key=api_key, base_url=base_url)
        self.include_domains = include_domains or []
        self.exclude_domains = exclude_domains or []
        self.include_answer = include_answer
        self.include_raw_content = include_raw_content

    async def search(self, query: str, depth: int = 3) -> list[SearchResult]:
        """Execute Tavily search with depth-based result count.

        Args:
            query: search query string
            depth: RouteLevel-driven result count (3=STANDARD, 5=DEEP)
        """
        # Auto-map depth to search params
        if depth <= 3:
            search_depth = "basic"
            max_results = 5
        else:
            search_depth = "advanced"
            max_results = 10

        payload: dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": self.include_answer,
            "include_raw_content": self.include_raw_content,
        }
        if self.include_domains:
            payload["include_domains"] = self.include_domains
        if self.exclude_domains:
            payload["exclude_domains"] = self.exclude_domains

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/search",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()

        return self._parse_results(data)

    async def extract(self, url: str) -> str:
        """Extract full page content from a URL."""
        payload: dict[str, Any] = {
            "api_key": self.api_key,
            "urls": [url],
            "extract_depth": "advanced",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/extract",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                data = await resp.json()

        results = data.get("results", [])
        if results:
            return results[0].get("raw_content", "") or results[0].get("content", "")
        failed = data.get("failed_results", [])
        if failed:
            return failed[0].get("content", "")
        return ""

    async def search_and_extract(
        self, query: str, depth: int = 3, extract_top: int = 3
    ) -> list[SearchResult]:
        """Search + extract top N results' full content."""
        results = await self.search(query, depth)

        # Extract full content for top results
        urls_to_extract = [r.url for r in results[:extract_top] if r.url]
        if urls_to_extract:
            payload: dict[str, Any] = {
                "api_key": self.api_key,
                "urls": urls_to_extract,
                "extract_depth": "advanced",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/extract",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    data = await resp.json()

            extracted = data.get("results", [])
            extract_map: dict[str, str] = {}
            for item in extracted:
                extract_map[item.get("url", "")] = (
                    item.get("raw_content", "") or item.get("content", "")
                )

            for r in results:
                if r.url in extract_map and extract_map[r.url]:
                    r.content = extract_map[r.url]

        return results

    def _parse_results(self, data: dict) -> list[SearchResult]:
        """Parse Tavily API response into SearchResult list."""
        results: list[SearchResult] = []

        for item in data.get("results", []):
            url = item.get("url", "")
            title = item.get("title", "")
            snippet = item.get("content", "")
            raw_content = item.get("raw_content", "")

            # Classify source type and weight
            source_type, weight = self._classify(url, title, raw_content or snippet)

            results.append(SearchResult(
                title=title,
                url=url,
                snippet=snippet,
                content=raw_content,
                source_type=source_type,
                weight=weight,
                relevance_score=item.get("score", 0.0),
            ))

        # Sort by weight descending, then score descending
        results.sort(key=lambda r: (-r.weight, -r.relevance_score))
        return results

    def _classify(self, url: str, title: str, content: str) -> tuple[str, float]:
        """Classify a search result by source type and assign weight.

        Weight hierarchy:
          1.0 = primary (arxiv, scholar, academic domains, original works)
          0.7 = academic secondary
          0.4 = general web
        """
        url_lower = url.lower()
        title_lower = title.lower()

        # Primary source indicators
        primary_domains = [
            "arxiv.org", "scholar.google.com", "doi.org", "pubmed.ncbi.nlm.nih.gov",
            "semanticscholar.org", "aclanthology.org", "jstor.org", "springer.com",
            "sciencedirect.com", "nature.com", "science.org", "cell.com",
            "plato.stanford.edu", "philpapers.org", "projecteuclid.org",
        ]
        primary_title_keywords = [
            "original article", "research article", "primary source",
            "manuscript", "dissertation", "thesis",
        ]

        # Academic secondary indicators
        academic_domains = [
            "wikipedia.org", "britannica.com", "scholarpedia.org",
            "researchgate.net", "academia.edu", ".edu",
        ]

        # Check primary
        for domain in primary_domains:
            if domain in url_lower:
                return ("paper", SourceWeight.PRIMARY)

        for kw in primary_title_keywords:
            if kw in title_lower:
                return ("paper", SourceWeight.PRIMARY)

        # Content-based heuristics
        content_indicators = content[:2000].lower()
        if any(w in content_indicators for w in ["abstract", "introduction", "methodology", "references", "citation"]):
            return ("paper", SourceWeight.PRIMARY)

        # Check academic
        for domain in academic_domains:
            if domain in url_lower:
                return ("article", SourceWeight.ACADEMIC)

        return ("web", SourceWeight.WEB_GENERAL)
