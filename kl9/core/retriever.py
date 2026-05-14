"""
9R-2.2 — SourceRetriever (Adaptive Optimization)

Orchestrates multi-source retrieval with automatic performance optimization:
  Light mode (default): Tavily → URL dedup → weight sort
  Heavy mode (auto):    Tavily → URL dedup → embedding dedup → rerank → weight sort

Auto-detects heavy load by result volume / total chars / avg content length.
Heavy mode triggers embedding + rerank when available.

Supports:
  - AstrBot: RerankProvider via provider_manager
  - Standalone: embedding-only dedup (cosine similarity)
  - Hermas/OpenClaw/Pi: same interface, different backends
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Optional

from ..models import (
    LLMProvider,
    SearchProvider,
    SearchResult,
    SourceContext,
    SourceWeight,
)


class SourceRetriever:
    """Multi-source retrieval orchestrator with adaptive optimization.

    Usage:
        retriever = SourceRetriever(
            search_provider=tavily,
            embed_provider=deepseek,       # optional
            rerank_provider=rerank_prov,   # optional
        )
        # Auto mode: detects heavy load, enables embed+rerank when needed
        ctx = await retriever.retrieve(query, depth=5)

        # Force heavy mode (e.g. skillbook generation)
        ctx = await retriever.retrieve(query, depth=5, force_optimize=True)

        # Force light mode (fast path)
        ctx = await retriever.retrieve(query, depth=3, auto_optimize=False)
    """

    # Thresholds for auto-detecting heavy load
    HEAVY_THRESHOLDS = {
        "total_chars": 50_000,      # 50K chars → likely deep academic content
        "result_count": 10,          # 10+ results → needs rerank
        "avg_content_length": 5_000, # avg 5K per result → needs dedup
        "max_single_length": 20_000, # any single result > 20K → needs dedup
    }

    def __init__(
        self,
        search_provider: SearchProvider | None = None,
        *,
        embed_provider: LLMProvider | None = None,
        rerank_provider=None,
        local_doc_paths: list[str] | None = None,
        dedup_threshold: float = 0.92,
    ):
        self.search_provider = search_provider
        self.embed_provider = embed_provider
        self.rerank_provider = rerank_provider
        self.local_doc_paths = local_doc_paths or []
        self.dedup_threshold = dedup_threshold

    # ── Public API ──

    async def retrieve(
        self,
        query: str,
        depth: int = 3,
        *,
        extract_top: int = 3,
        auto_optimize: bool = True,
        force_optimize: bool = False,
    ) -> SourceContext:
        """Execute full retrieval pipeline with adaptive optimization.

        Args:
            query: search query
            depth: RouteLevel-driven result count (3=STANDARD, 5=DEEP)
            extract_top: how many top results to extract full content
            auto_optimize: if True, auto-detect heavy load and enable embed+rerank
            force_optimize: if True, always enable embed+rerank (skillbook mode)

        Returns:
            SourceContext with merged/deduped/reranked results
        """
        ctx = SourceContext(query=query)

        # ── Phase 1: Multi-source search (parallel) ──
        tasks = []

        if self.search_provider:
            tasks.append(self._search_web(query, depth, extract_top))

        if self.local_doc_paths:
            tasks.append(self._search_local(query, depth))

        if not tasks:
            ctx.missing_notice = "未配置任何搜索服务"
            return ctx

        all_results_batches = await asyncio.gather(*tasks, return_exceptions=True)

        all_results: list[SearchResult] = []
        for batch in all_results_batches:
            if isinstance(batch, Exception):
                continue
            all_results.extend(batch)

        if not all_results:
            ctx.missing_notice = "搜索未返回结果"
            return ctx

        # ── Phase 2: Detect heavy load ──
        is_heavy = force_optimize or (
            auto_optimize and self._detect_heavy_load(all_results)
        )

        # ── Phase 3: Deduplication ──
        if is_heavy and self.embed_provider:
            all_results = await self._deduplicate(all_results, force_semantic=True)
        else:
            all_results = await self._deduplicate(all_results, force_semantic=False)

        # ── Phase 4: Rerank ──
        if is_heavy and self.rerank_provider and len(all_results) > 1:
            try:
                all_results = await self._rerank(query, all_results)
            except Exception:
                pass  # Rerank failure → keep original order

        # ── Phase 5: Assign priority + sort ──
        for i, r in enumerate(all_results):
            r.priority = i
        all_results.sort(key=lambda r: (-r.weight, r.priority))

        # ── Phase 6: Assess quality ──
        ctx.results = all_results
        ctx.total_found = len(all_results)
        ctx.has_primary = any(r.is_primary for r in all_results)
        ctx.has_academic = any(r.is_academic for r in all_results)

        missing = []
        if not ctx.has_primary:
            missing.append("一手原文（论文/原著）")
        if not ctx.has_academic:
            missing.append("高质量学术二手资料")
        if missing:
            ctx.missing_notice = "未检索到: " + "、".join(missing)

        return ctx

    # ── Internal: Heavy Load Detection ──

    def _detect_heavy_load(self, results: list[SearchResult]) -> bool:
        """Auto-detect if results warrant heavy-mode optimization."""
        if len(results) >= self.HEAVY_THRESHOLDS["result_count"]:
            return True

        total_chars = sum(len(r.content or r.snippet) for r in results)
        if total_chars >= self.HEAVY_THRESHOLDS["total_chars"]:
            return True

        if results:
            avg_len = total_chars / len(results)
            if avg_len >= self.HEAVY_THRESHOLDS["avg_content_length"]:
                return True

        max_len = max(len(r.content or r.snippet) for r in results)
        if max_len >= self.HEAVY_THRESHOLDS["max_single_length"]:
            return True

        return False

    # ── Internal: Web Search ──

    async def _search_web(
        self,
        query: str,
        depth: int,
        extract_top: int,
    ) -> list[SearchResult]:
        """Tavily search + extract."""
        results = await self.search_provider.search(query, depth)

        # Extract top N full content (in bulk)
        if extract_top > 0:
            urls = [r.url for r in results[:extract_top] if r.url]
            if urls:
                try:
                    extract_tasks = [self.search_provider.extract(url) for url in urls]
                    extracts = await asyncio.gather(*extract_tasks, return_exceptions=True)
                    for r, ext in zip(results, extracts):
                        if isinstance(ext, str) and ext:
                            r.content = ext
                except Exception:
                    pass  # Partial extraction is fine

        return results

    # ── Internal: Local Search ──

    async def _search_local(self, query: str, depth: int) -> list[SearchResult]:
        """Search local document paths using embedding similarity."""
        results: list[SearchResult] = []

        if not self.embed_provider:
            return results

        # Gather document texts
        docs: list[tuple[str, str]] = []
        for path in self.local_doc_paths:
            try:
                import os
                if os.path.isfile(path):
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read()
                    docs.append((path, text[:20000]))
            except Exception:
                continue

        if not docs:
            return results

        # Embed query + documents
        try:
            texts = [query] + [d[1] for d in docs]
            embeddings = await self.embed_provider.embed(texts)

            if not embeddings or len(embeddings) < 2:
                return results

            query_emb = embeddings[0]
            doc_embs = embeddings[1:]

            for i, (path, text) in enumerate(docs):
                sim = self._cosine_similarity(query_emb, doc_embs[i])
                if sim > 0.3:  # minimum relevance threshold
                    results.append(SearchResult(
                        title=os.path.basename(path),
                        url=f"file://{path}",
                        snippet=text[:500],
                        content=text,
                        source_type="paper",
                        weight=SourceWeight.PRIMARY,
                        relevance_score=sim,
                    ))
        except Exception:
            pass

        results.sort(key=lambda r: -r.relevance_score)
        return results[:depth]

    # ── Internal: Dedup ──

    async def _deduplicate(
        self,
        results: list[SearchResult],
        force_semantic: bool = False,
    ) -> list[SearchResult]:
        """Two-phase dedup: URL exact → embedding semantic (conditional)."""
        if len(results) <= 1:
            return results

        # Phase A: URL-based exact dedup (always runs, zero cost)
        seen_urls: set[str] = set()
        url_deduped: list[SearchResult] = []
        for r in results:
            url_hash = (
                hashlib.md5(r.url.encode()).hexdigest()
                if r.url
                else hashlib.md5(r.title.encode()).hexdigest()
            )
            if url_hash not in seen_urls:
                seen_urls.add(url_hash)
                url_deduped.append(r)

        if len(url_deduped) <= 1:
            return url_deduped

        # Phase B: Embedding-based semantic dedup (conditional)
        if not force_semantic or not self.embed_provider:
            return url_deduped

        try:
            texts = [r.snippet or r.title for r in url_deduped]
            embeddings = await self.embed_provider.embed(texts)

            if not embeddings or len(embeddings) < 2:
                return url_deduped

            keep: list[SearchResult] = []
            for i, r in enumerate(url_deduped):
                is_dup = False
                for j in range(i):
                    sim = self._cosine_similarity(embeddings[i], embeddings[j])
                    if sim > self.dedup_threshold:
                        is_dup = True
                        # Keep the higher-weight result
                        if r.weight > url_deduped[j].weight:
                            keep[j] = r
                        break
                if not is_dup:
                    keep.append(r)

            return keep
        except Exception:
            return url_deduped

    # ── Internal: Rerank ──

    async def _rerank(self, query: str, results: list[SearchResult]) -> list[SearchResult]:
        """Rerank using local rerank provider (AstrBot RerankProvider)."""
        if not self.rerank_provider or len(results) <= 1:
            return results

        documents = [r.content[:3000] or r.snippet for r in results]
        try:
            reranked = await self.rerank_provider.rerank(query, documents)
            if reranked:
                new_results = []
                for item in reranked:
                    idx = getattr(item, "index", 0)
                    if 0 <= idx < len(results):
                        new_results.append(results[idx])
                if new_results:
                    return new_results
        except Exception:
            pass

        return results

    # ── Helpers ──

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b) or len(a) == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = (sum(x * x for x in a)) ** 0.5
        norm_b = (sum(y * y for y in b)) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
