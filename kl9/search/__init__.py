"""
9R-2.1 — Search Providers

Service provider pattern for search backends. Mirror of LLMProvider.
"""

from .tavily import TavilyProvider

__all__ = ["TavilyProvider"]
