"""
9R-2.1 - AdaptiveRouter v3 (LLM-only)

Single-tier LLM-as-Router. No keyword fallback. No concept dictionary.
The system prompt (~250 tokens) is static and fully cacheable - prefix caching
eliminates nearly all routing latency and cost after the first call.

Cost: < $0.0005 per route (cached), < $0.001 uncached.
Latency: ~200ms cached, ~800ms uncached.
"""

from __future__ import annotations

import logging

from ..models import (
    AcademicComplexityScore,
    LLMProvider,
    RouteDecision,
    RouteLevel,
)

logger_router = logging.getLogger("kl9.router")

LLM_ROUTER_PROMPT = """Classify this query. Reply with ONE WORD only: QUICK, STANDARD, or DEEP.

QUICK: simple questions, greetings, facts, translations, command-like, how-to, any non-academic query
STANDARD: analysis, comparison, explanation, how things work, moderate depth - this is the DEFAULT for most substantive questions
DEEP (RARE - only when ALL of these are true):
  1. Social science / humanities / philosophy / critical theory domain
  2. Requires holding irreconcilable perspectives in tension
  3. Asks for critique, deconstruction, or paradigm-level analysis
  4. Has explicit academic framing (theorists, -isms, structural analysis)

Examples:
"What time is it?" -> QUICK
"Compare Foucault and Han on social control" -> STANDARD
"Analyze the structural homology between Foucault's disciplinary power and algorithmic governance, questioning whether this constitutes a paradigm rupture or mere rhetorical shift" -> DEEP

Query: {query}

Classification:"""


class AdaptiveRouter:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def route(
        self,
        query: str,
        forced: str | None = None,
    ) -> RouteDecision:
        if forced:
            level = {"deep": RouteLevel.DEEP, "standard": RouteLevel.STANDARD, "quick": RouteLevel.QUICK}.get(forced.lower())
            if level:
                budget = 9 if level == RouteLevel.DEEP else (2 if level == RouteLevel.STANDARD else 0)
                return RouteDecision(level=level, score=AcademicComplexityScore(total=100 if level == RouteLevel.DEEP else 50),
                                     max_fold_depth=budget, reason=f"forced {forced}")

        return await self._llm_route(query)

    async def _llm_route(self, query: str) -> RouteDecision:
        prompt = LLM_ROUTER_PROMPT.format(query=query[:500])
        response = await self.llm.complete(
            system_prompt="You are a query complexity classifier. Reply with EXACTLY ONE WORD: QUICK, STANDARD, or DEEP. No other text.",
            user_prompt=prompt,
            temperature=0.0,
            max_tokens=10,
            timeout=30.0,
        )
        raw = response.content.strip().upper()

        deep_words = {"DEEP", "COMPLEX", "HARD", "DIFFICULT", "HIGH", "ADVANCED"}
        standard_words = {"STANDARD", "MEDIUM", "MODERATE", "NORMAL", "REGULAR", "MID"}
        quick_words = {"QUICK", "SIMPLE", "EASY", "LOW", "BASIC", "TRIVIAL", "OKAY", "OK", "YES", "NO", "FINE"}

        first_word = raw.split()[0] if raw.split() else raw

        if first_word in deep_words:
            level, budget = RouteLevel.DEEP, self._budget(query)
        elif first_word in standard_words:
            level, budget = RouteLevel.STANDARD, 2
        elif first_word in quick_words:
            h_level, h_budget = self._heuristic_route(query)
            if h_level != RouteLevel.QUICK:
                level, budget = h_level, h_budget
                raw = f"{raw} (LLM->QUICK but heuristic->{level.name})"
            else:
                level, budget = RouteLevel.QUICK, 0
        else:
            level, budget = self._heuristic_route(query)
            raw = f"{raw} (heuristic->{level.name})"

        return RouteDecision(
            level=level,
            score=AcademicComplexityScore(total=90 if level == RouteLevel.DEEP else (50 if level == RouteLevel.STANDARD else 10), confidence=0.85),
            max_fold_depth=budget,
            reason=f"llm_router: {raw[:120]}",
        )

    @staticmethod
    def _heuristic_route(query: str) -> tuple:
        """Heuristic fallback with high DEEP threshold.
        
        DEEP requires: length + deep academic vocab + critical inquiry.
        A book-review question scores ~5-8 -> STANDARD.
        A genuine critical-theory question scores ~14+ -> DEEP.
        """
        q_len = len(query)
        q_marks = query.count("？") + query.count("?")
        
        deep_vocab = {
            "theory", "paradigm", "homology", "rupture", "dialectic",
            "deconstruction", "subjectivity", "alienation", "reification",
            "epistemology", "ontology", "metaphysics", "transcendental",
            "negation", "critique", "disciplinary", "genealogy",
            "structural", "hegemony", "biopolitics", "governmentality",
        }
        std_vocab = {
            "analysis", "compare", "evaluate", "discuss", "review",
            "criticism", "argument", "perspective", "framework",
            "impact", "significance", "history", "politics", "economy",
            "society", "revolution", "strike", "consciousness",
        }
        
        dl = query.lower()
        deep_count = sum(1 for w in deep_vocab if w in dl)
        std_count = sum(1 for w in std_vocab if w in dl)
        quotes = query.count('"') + query.count("'")
        
        score = q_len // 50 + q_marks * 3 + deep_count * 8 + std_count + quotes * 2

        if score >= 14:
            return RouteLevel.DEEP, min(9, max(3, score // 3))
        elif score >= 5:
            return RouteLevel.STANDARD, 2
        else:
            return RouteLevel.QUICK, 0

    @staticmethod
    def _budget(query: str) -> int:
        n = min(9, max(3, len(query) // 50))
        if query.count("？") + query.count("?") + query.count("-") >= 3:
            n = min(9, n + 2)
        return n
