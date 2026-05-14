"""
9R-2.1 — Recursive Fold Engine

The core cognitive loop. Replaces kl9_v3.1's Swarm 3-wave 6-role.
Depth-first recursive folding: each step deepens the previous tension.

v2.2: Accepts SourceContext, removed hard 2000-char truncation.
       LLM manages its own context window. max_tokens bumped to 8192.

Flow:
    Fold 0: A/B tension initialization (from Decomposer)
    Fold N: A_deepened → collision → B_deepened → collision → new tensions
    Gate:  [TENSION:]/[UMKEHR:] increment > 0 → continue
    Stop:  budget exhausted OR no new markers

Maps to Recurrent-Depth Transformer pattern:
    - Shared-weight fold block applied iteratively
    - Dynamic depth based on intrinsic sequential complexity
    - Adaptive stopping via marker increment detection
"""

from __future__ import annotations

import time
from typing import Optional

from ..models import (
    FoldChain,
    FoldResult,
    LLMProvider,
    Perspective,
    SourceContext,
    TensionGateResult,
)
from .dna import (
    CONSTITUTIONAL_SYSTEM_PROMPT,
    extract_tensions,
    extract_umkehrs,
    normalize_tension,
    dedup_markers,
)
from ..utils.tension_bus import TensionBus

FOLD_DEEPEN_PROMPT = """你正在执行认知折叠的第 {fold_num} 步。

信源参考:
{source_context}

前一步产生的张力:
{prior_tensions}

当前视角A的论证（需要深化）:
{perspective_a}

当前视角B的论证（需要深化）:
{perspective_b}

任务: 在每个视角上折叠一层——不是补充论据，而是在已有张力的基础上向深处推进。
    - A视角深化: 在A的论证中找到前一步未触及的隐含前提，展开
    - B视角深化: 在B的论证中找到前一步未触及的隐含前提，展开
    - 碰撞: 将A和B深化后的结果对撞，产生新的[硬张力]标记

输出格式:
[视角A深化]
<在A的论证基础上向深处推进300-500字>

[视角B深化]
<在B的论证基础上向深处推进300-500字>

[碰撞]
<将新A和新B对撞，必须产生至少一个新[硬张力] >
[硬张力]: <新张力的具体内容>
[硬张力]: <另一个新张力的具体内容>

约束:
- 深化不是反对前一步，而是发现前一步未触达的层次
- [硬张力]必须是结构性不可调和的，不是修辞差异
- 如果发现概念反转，标注[UMKEHR]
- 禁止缝合式收束
- 所有断言必须可追溯到信源中的原文
"""

# ── 翻译折叠专用 ──
FOLD_TRANSLATE_PROMPT = """你正在执行翻译折叠的第 {fold_num} 步。

前一步产生的翻译张力:
{prior_tensions}

当前视角A的翻译方案:
{perspective_a}

当前视角B的翻译方案:
{perspective_b}

任务: 在每个翻译视角上折叠一层——不是深化，而是从该翻译哲学出发生成译文。
    - A视角翻译: 严格以异化视角翻译原文段落（保留句法骨架、术语异质性）
    - B视角翻译: 严格以归化视角翻译同一段落（汉语语流优先、透明）
    - 碰撞: 对比两个译文，识别新的翻译张力点

输出格式:
[视角A译文]
<异化翻译的全文段落>

[视角B译文]
<归化翻译的全文段落>

[碰撞]
<对比两个译文，识别出具体的翻译抉择点>
[硬张力]: <不可调和的翻译抉择，如"术语X: 原词根保真 vs 汉语通顺">
[硬张力]: <另一个翻译张力点>

约束:
- 每个视角的翻译必须严格保持其翻译哲学的一致性
- [硬张力]必须是具体的词汇/句式层面的不可调和选择
- 不缝合、不收束、不提供中间态
"""


TRANSLATION_PERSPECTIVE_MARKERS = ["异化翻译视角", "归化翻译视角"]


def _is_translation_fold(perspective_a: Perspective, perspective_b: Perspective) -> bool:
    """根据视角名称检测是否为翻译折叠。"""
    a_name = perspective_a.name if perspective_a else ""
    b_name = perspective_b.name if perspective_b else ""
    return any(m in a_name or m in b_name for m in TRANSLATION_PERSPECTIVE_MARKERS)


class FoldEngine:
    """Recursive fold execution engine.

    Implements depth-first cognitive folding:
    Fold 0 (Decomposer output) → Fold 1 → Fold 2 → ... → Fold N → stop
    """

    def __init__(self, llm: LLMProvider, bus: TensionBus | None = None,
                 *, retriever=None):
        self.llm = llm
        self.bus = bus or TensionBus()
        self.retriever = retriever  # Opt-2: secondary source refresh during deep folds

    async def fold(
        self,
        perspective_a: Perspective,
        perspective_b: Perspective,
        initial_tensions: list[str],
        max_fold_depth: int,
        source_ctx: SourceContext | None = None,
    ) -> FoldChain:
        """Execute recursive folding.

        Args:
            perspective_a: Initial perspective A from Decomposer
            perspective_b: Initial perspective B from Decomposer
            initial_tensions: Initial tension markers from Decomposer
            max_fold_depth: Maximum number of fold steps [2, 9]
            source_ctx: Optional source context for grounding

        Returns:
            FoldChain with all completed folds and stop reason
        """
        chain = FoldChain(query="", folds=[], total_tokens=0, total_latency_ms=0.0)

        # Fold 0: the initial decomposition
        fold0 = FoldResult(
            fold_number=0,
            perspective_a=perspective_a,
            perspective_b=perspective_b,
            raw_content=f"{perspective_a.content}\n{perspective_b.content}",
            tension_markers=list(initial_tensions),
            umkehr_markers=[],
        )
        chain.folds.append(fold0)

        prior_tensions = list(initial_tensions)
        pa_content = perspective_a.content
        pb_content = perspective_b.content

        # Prepare source context for fold prompt (once, static for all folds)
        source_text = source_ctx.format_for_fold() if source_ctx else ""

        for fold_num in range(1, max_fold_depth + 1):
            t0 = time.perf_counter()

            # Build fold prompt — choose translation or deepen variant
            tensions_text = "\n".join(f"- {t}" for t in prior_tensions[-6:])
            if _is_translation_fold(perspective_a, perspective_b):
                prompt = FOLD_TRANSLATE_PROMPT.format(
                    fold_num=fold_num,
                    prior_tensions=tensions_text,
                    perspective_a=pa_content,
                    perspective_b=pb_content,
                )
            else:
                prompt = FOLD_DEEPEN_PROMPT.format(
                    fold_num=fold_num,
                    source_context=source_text,
                    prior_tensions=tensions_text,
                    perspective_a=pa_content,
                    perspective_b=pb_content,
                )

            try:
                response = await self.llm.complete(
                    system_prompt=CONSTITUTIONAL_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    temperature=0.7,
                    max_tokens=8192,
                )
            except Exception:
                # Preserve already-accumulated chain rather than losing all N folds.
                chain.stopped_reason = "error"
                break

            latency = (time.perf_counter() - t0) * 1000

            # Parse fold output
            pa_new, pb_new, new_tensions, new_umkehrs = self._parse_fold(response.content)

            fold_result = FoldResult(
                fold_number=fold_num,
                perspective_a=Perspective(name=perspective_a.name, content=pa_new),
                perspective_b=Perspective(name=perspective_b.name, content=pb_new),
                raw_content=response.content,
                tension_markers=new_tensions,
                umkehr_markers=new_umkehrs,
                tokens_used=response.usage.total_tokens,
                latency_ms=latency,
            )
            chain.folds.append(fold_result)
            chain.total_tokens += response.usage.total_tokens
            chain.total_latency_ms += latency

            # Gate check: any new tensions or umkehrs after canonical dedup?
            # Bug-4 fix: use normalize_tension so decomposer's "(A->B):" prefix
            # and fold output's bare "[硬张力]:" are recognized as identical.
            prior_keys = {normalize_tension(t) for t in prior_tensions}
            new_keys = {normalize_tension(t) for t in new_tensions} - prior_keys
            has_insight = len(new_keys) > 0 or len(new_umkehrs) > 0

            if not has_insight:
                chain.stopped_reason = "tension_saturated"
                break

            # Opt-2: every 2 steps, refresh sources with emerged concepts
            if self.retriever and fold_num % 2 == 0:
                concepts = self._extract_key_concepts(response.content, max_concepts=3)
                if concepts:
                    try:
                        fresh = await self.retriever.retrieve(
                            " ".join(concepts), depth=2, auto_optimize=False,
                        )
                        if fresh and fresh.results:
                            source_text = fresh.format_for_fold()
                    except Exception:
                        pass  # Silent fail — keep existing sources

            # Update for next iteration
            prior_tensions.extend(new_tensions)
            pa_content = pa_new
            pb_content = pb_new

        else:
            chain.stopped_reason = "budget_exhausted"

        return chain


    @staticmethod
    def _extract_key_concepts(text: str, max_concepts: int = 3) -> list[str]:
        """Extract key novel concepts from fold output for secondary search.

        Opt-2: when the fold deepens, new theoretical terms typically emerge
        as concept names, book titles, or quoted authors.  We extract 2-3
        candidate terms to refresh the source pool.
        """
        import re as _re
        candidates: list[str] = []
        # Pattern: 「...」, 《...》, or quoted names
        for p in [r"「(.{2,20})」", r"《(.{2,30})》", r'"(.{2,20})"']:
            for m in _re.finditer(p, text):
                candidates.append(m.group(1))
        # Dedup + cap
        seen: set[str] = set()
        out: list[str] = []
        for c in candidates:
            if c not in seen and len(c) >= 2:
                seen.add(c)
                out.append(c)
            if len(out) >= max_concepts:
                break
        return out

    def _parse_fold(self, content: str) -> tuple[str, str, list[str], list[str]]:
        """Parse LLM fold output into components."""
        pa_section = ""
        pb_section = ""
        tensions: list[str] = []
        umkehrs: list[str] = []
        current = None

        for line in content.split("\n"):
            ls = line.strip()
            if not ls:
                continue

            if "[视角A深化]" in ls:
                current = "A"
                continue
            elif "[视角B深化]" in ls:
                current = "B"
                continue
            elif "[碰撞]" in ls:
                current = "collision"
                continue

            if current == "A":
                pa_section += ls + "\n"
            elif current == "B":
                pb_section += ls + "\n"
            elif current == "collision":
                if "[硬张力]" in ls or "[软张力]" in ls:
                    tensions.append(ls.strip())
                if "[UMKEHR]" in ls:
                    umkehrs.append(ls.strip())

        # Also extract from full content (catches markers outside [碰撞] block)
        tensions.extend(extract_tensions(content))
        umkehrs.extend(extract_umkehrs(content))

        # Bug-5 fix: parser walks markers twice (line-scan + regex extract),
        # causing every marker to appear 2-3x. Dedup by canonical key.
        tensions = dedup_markers(tensions)
        umkehrs = dedup_markers(umkehrs)

        return pa_section.strip(), pb_section.strip(), tensions, umkehrs

    async def gate_check(
        self, fold_result: FoldResult, prior_tensions: list[str]
    ) -> TensionGateResult:
        """Check if folding should continue."""
        prior_count = len(set(prior_tensions))
        new_tensions = set(fold_result.tension_markers)
        new_count = len(new_tensions - set(prior_tensions))

        prior_umkehr = 0  # Would need tracking across folds
        new_umkehr = len(fold_result.umkehr_markers)

        should_continue = (new_count > 0) or (new_umkehr > 0)

        return TensionGateResult(
            should_continue=should_continue,
            reason="new_tensions" if new_count > 0 else ("new_umkehr" if new_umkehr > 0 else "saturated"),
            prior_tension_count=prior_count,
            new_tension_count=new_count,
            prior_umkehr_count=prior_umkehr,
            new_umkehr_count=new_umkehr,
        )
