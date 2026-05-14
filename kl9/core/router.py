"""
9R-2.1 — AdaptiveRouter v3 (LLM-only)

Single-tier LLM-as-Router. No keyword fallback. No concept dictionary.
The system prompt (~250 tokens) is static and fully cacheable — prefix caching
eliminates nearly all routing latency and cost after the first call.

Cost: < $0.0005 per route (cached), < $0.001 uncached.
Latency: ~200ms cached, ~800ms uncached.
"""

from __future__ import annotations

from ..models import (
    AcademicComplexityScore,
    LLMProvider,
    RouteDecision,
    RouteLevel,
)

# ── LLM Router Prompt (static, fully cacheable) ──

LLM_ROUTER_PROMPT = """ classify the cognitive complexity of this query. output exactly one word: QUICK or STANDARD or DEEP.

QUICK: simple factual lookup, greeting, casual chat, single-concept question
STANDARD: multi-step analysis, comparison, moderate theoretical depth
DEEP: requires holding multiple irreconcilable perspectives, deep theoretical tension, multi-layered conceptual architecture

examples:
"你好" → QUICK
"比较韩炳哲和福柯对社会控制的不同分析" → STANDARD
"分析规训社会向倦怠社会的范式转移中，主体性如何从外部规训翻转为自我剥削，这一翻转是否构成了某种不可逆的历史断裂——还是只是权力技术的表面修辞变换？" → DEEP

query: {query}

output:"""


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
            system_prompt="You are a query complexity classifier. Output exactly one word.",
            user_prompt=prompt,
            temperature=0.0,
            max_tokens=10,
            timeout=8.0,
        )
        raw = response.content.strip().upper()

        if "DEEP" in raw:
            level, budget = RouteLevel.DEEP, self._budget(query)
        elif "STANDARD" in raw:
            level, budget = RouteLevel.STANDARD, 2
        else:
            level, budget = RouteLevel.QUICK, 0

        return RouteDecision(
            level=level,
            score=AcademicComplexityScore(total=90 if level == RouteLevel.DEEP else (50 if level == RouteLevel.STANDARD else 10), confidence=0.85),
            max_fold_depth=budget,
            reason=f"llm_router: {raw}",
        )

    @staticmethod
    def _budget(query: str) -> int:
        n = min(9, max(3, len(query) // 50))
        if query.count("？") + query.count("?") + query.count("——") >= 3:
            n = min(9, n + 2)
        return n
