"""
9R-2.2 — KL9System

Main orchestrator: Router → Source Retrieval → Decomposer → Fold Loop → Validate → Aggregate.

v2.2: Source-first pipeline. Retrieves primary/academic sources before decomposition.
      Degrades to STANDARD when high-quality sources are unavailable.
      Supports force_optimize for skillbook / big-document mode.

Integration point for AstrBot. Single entry: process(query) → output.
"""

from __future__ import annotations

import time
from typing import Optional

from .models import (
    AggregatedOutput,
    LLMProvider,
    RouteDecision,
    RouteLevel,
    SourceContext,
)
from .core.dna import CONSTITUTIONAL_SYSTEM_PROMPT
from .core.router import AdaptiveRouter
from .core.decomposer import TaskDecomposer
from .core.fold import FoldEngine
from .core.gate import QualityGate
from .core.validator import QualityValidator
from .core.aggregator import TensionPreservingAggregator
from .core.retriever import SourceRetriever
from .utils.tension_bus import TensionBus


class KL9System:
    """9R-2.2 main cognitive pipeline.

    Usage:
        provider = DeepSeekV4Provider(api_key="...")
        retriever = SourceRetriever(search_provider=tavily, embed_provider=provider)
        kl9 = KL9System(provider, retriever=retriever)
        result = await kl9.process("分析福柯的权力理论")
    """

    def __init__(
        self,
        llm: LLMProvider,
        *,
        retriever: SourceRetriever | None = None,
        bus: TensionBus | None = None,
        router_llm: LLMProvider | None = None,
        decomposer_llm: LLMProvider | None = None,
        validator_llm: LLMProvider | None = None,
    ):
        self.llm = llm  # fold LLM (also used for STANDARD path single-call)
        self.retriever = retriever
        self.bus = bus or TensionBus()
        self.router = AdaptiveRouter(llm=router_llm or llm)
        self.decomposer = TaskDecomposer(decomposer_llm or llm)
        self.fold_engine = FoldEngine(llm, self.bus, retriever=retriever)
        self.gate = QualityGate()
        self.validator = QualityValidator(validator_llm or llm)
        self.aggregator = TensionPreservingAggregator()

    async def process(
        self,
        query: str,
        session_id: str = "",
        force_depth: str | None = None,
        *,
        force_optimize: bool = False,
    ) -> AggregatedOutput:
        """Process query through full cognitive pipeline.

        Stages:
            1. Route → complexity score + fold budget
            2. Retrieve → source gathering (adaptive optimization)
            3. Decompose → A/B perspectives + initial tensions (LLM call)
            4. Fold → recursive deepening loop (LLM calls × N)
            5. Validate → final LLM-as-judge quality check (LLM call)
            6. Aggregate → tension-preserving output assembly

        Args:
            force_optimize: if True, forces heavy-mode retrieval (skillbook / big doc mode)
        """
        t0 = time.perf_counter()

        # ── Stage 1: Routing ──
        route = await self.router.route(query, forced=force_depth)

        if route.level == RouteLevel.QUICK:
            return AggregatedOutput(
                content=self._quick_reply(query),
                fold_depth=0,
            )

        # ── Stage 2: Source Retrieval (adaptive optimization) ──
        source_ctx = SourceContext(query=query)
        if self.retriever and route.level != RouteLevel.QUICK:
            depth = 5 if route.level == RouteLevel.DEEP else 2
            source_ctx = await self.retriever.retrieve(
                query,
                depth=depth,
                force_optimize=force_optimize,
            )

            # Degrade check: no high-quality sources → drop to STANDARD
            if route.level == RouteLevel.DEEP and source_ctx.should_degrade:
                route = RouteDecision(
                    level=RouteLevel.STANDARD,
                    score=route.score,
                    max_fold_depth=1,
                    reason=f"degraded: {source_ctx.missing_notice}",
                    degrade_from=RouteLevel.DEEP,
                )

        # ── Stage 3: Decompose (DEEP only) ──
        pa, pb, tensions = await self.decomposer.decompose(
            query,
            source_ctx=source_ctx if source_ctx.results else None,
        )

        if route.level == RouteLevel.STANDARD:
            # STANDARD fast-path: skip decompose, single LLM call with sources
            source_text = (
                "\n\n" + source_ctx.format_for_prompt()
                if source_ctx and source_ctx.results
                else ""
            )
            response = await self.llm.complete(
                system_prompt=CONSTITUTIONAL_SYSTEM_PROMPT,
                user_prompt=(
                    f"分析以下问题，给出有深度的回答:\n\n{query}"
                    f"{source_text}"
                ),
                temperature=0.5,
                max_tokens=8192 if source_ctx and source_ctx.results else 4096,
            )
            suffix = ""
            if route.is_degraded and source_ctx.missing_notice:
                suffix = f"\n\n[信源说明] {source_ctx.missing_notice}。分析基于可用信源。"

            return AggregatedOutput(
                content=response.content + suffix,
                fold_depth=1,
                token_used=response.usage.total_tokens,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )

        # ── Stage 4: Recursive Fold (LLM calls #2 to #N+1) ──
        chain = await self.fold_engine.fold(
            pa, pb, tensions, route.max_fold_depth,
            source_ctx=source_ctx,
        )

        # ── Stage 5: Quality Validation (LLM call #N+2) ──
        last_content = chain.folds[-1].raw_content if chain.folds else ""
        quality = await self.validator.validate(last_content)

        # ── Stage 6: Aggregate ──
        result = self.aggregator.aggregate(chain, quality)

        # Append source degradation note if applicable
        if route.is_degraded and source_ctx.missing_notice:
            result.content += f"\n\n[信源说明] {source_ctx.missing_notice}。分析基于可用信源与内部知识（权重0.1）。"

        result.latency_ms = (time.perf_counter() - t0) * 1000
        return result

    def _quick_reply(self, query: str) -> str:
        """Quick path: no LLM, direct template response."""
        if len(query) < 10:
            return "收到。请使用 /deep 前缀进行深入分析。"
        return "这是一个低复杂度查询。如需深入分析，请使用 /deep 前缀。"
