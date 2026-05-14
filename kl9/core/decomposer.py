"""
9R-2.1 — TaskDecomposer

Decomposes query into A/B dual perspectives via single LLM call.
Output feeds into the recursive fold engine.

v2.2: Accepts SourceContext for source-grounded decomposition.
v2.3: Translation intent detection → translation decomposition prompt.
"""

from __future__ import annotations

from ..models import LLMProvider, Perspective, SourceContext
from .dna import CONSTITUTIONAL_SYSTEM_PROMPT

FROM_SOURCES_CONSTRAINT = """
信源约束 (P10):
- 所有论证必须可追溯到上述信源中的原文
- 引用原文时必须标注 [原文] 和来源
- 无法从信源验证的推论必须标注 [推论]
- 内部知识权重 0.1，仅作补充，不得作为主要论证依据
"""

DECOMPOSER_PROMPT = """将以下查询分解为两个不可调和的理论视角。必须标注张力类型。

查询: {query}
{source_context}

输出格式（严格按此结构）:

[视角A]
视角名称: <概念命名，如"程序正义视角">
核心论证: <200-400字，建立视角A的最强论证>
理论资源: <理论家1, 理论家2>
关键概念: <概念1, 概念2>
[张力标记A]: <与视角B不可调和的第一个点>
[张力标记A]: <与视角B不可调和的第二个点>

[视角B]
视角名称: <概念命名，与视角A形成结构对立>
核心论证: <200-400字，建立视角B的最强论证>
理论资源: <理论家1, 理论家2>
关键概念: <概念1, 概念2>
[张力标记B]: <与视角A不可调和的第一个点>
[张力标记B]: <与视角A不可调和的第二个点>

约束:
- 视角A和B必须是结构性的对立，不是修辞性的
- 每个视角必须引用至少2位理论家
- [张力标记]必须是真正不可调和的点，不是观点差异
- 不使用第一人称
- 不缝合、不调和
{source_constraint}
"""

TRANSLATION_DECOMPOSE_PROMPT = """这是一个翻译任务。将以下原文分解为两个不可调和的翻译视角。

查询: {query}

原文:
{source_context}

输出格式（严格按此结构）:

[视角A]
视角名称: 异化翻译视角
核心论证: <从异化翻译哲学出发（Venuti/Schleiermacher），200-400字论证为何应保留原文句法/术语的异质性>
理论资源: Venuti, Schleiermacher, Benjamin
关键概念: 异化, 可见译者, 概念保真, 抵抗式翻译
[张力标记A]: <与归化视角不可调和的第一点>
[张力标记A]: <与归化视角不可调和的第二点>

[视角B]
视角名称: 归化翻译视角
核心论证: <从归化翻译哲学出发（Nida/严复），200-400字论证为何应以译入语习惯优先>
理论资源: Nida, 严复, 钱锺书
关键概念: 归化, 透明译者, 动态对等, 语流优先
[张力标记B]: <与异化视角不可调和的第一点>
[张力标记B]: <与异化视角不可调和的第二点>

约束:
- 视角A和B必须是翻译哲学层面的结构性对立
- [张力标记]必须是真正不可调和的翻译抉择点，如"术语准确 vs 语流顺畅"
- 不缝合、不调和
"""

TRANSLATION_SIGNALS = ["翻译", "中译", "英译", "译文", "译法", "术语翻译", "译名", "如何翻译",
                       "翻成", "翻译成", "翻译一下", "帮我翻", "译一下"]

import re

def _is_translation_intent(query: str) -> bool:
    return any(s in query for s in TRANSLATION_SIGNALS)

def _extract_source_text(query: str) -> str:
    return re.sub(r'^(请|帮我|麻烦你|能不能|能否)?\s*(翻译|译|翻)(一下|成(中文|英文|日语))?[：:：\s]*', '', query).strip()


class TaskDecomposer:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def decompose(
        self,
        query: str,
        source_ctx: SourceContext | None = None,
    ) -> tuple[Perspective, Perspective, list[str]]:
        """Decompose query into A/B perspectives with tension markers.

        Args:
            query: the user query
            source_ctx: optional retrieved source context

        Returns: (perspective_a, perspective_b, tension_markers)
        """
        source_text = ""
        constraint_text = ""

        # ── 翻译意图分支 ──
        if _is_translation_intent(query):
            src = _extract_source_text(query)
            if source_ctx and source_ctx.results:
                src += "\n\n" + source_ctx.format_for_prompt()
            prompt = TRANSLATION_DECOMPOSE_PROMPT.format(
                query=query, source_context=src
            )
            max_tok = 8192 if source_ctx and source_ctx.results else 4096
            response = await self.llm.complete(
                system_prompt=CONSTITUTIONAL_SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.7,
                max_tokens=max_tok,
            )
            return self._parse(response.content)

        # ── 默认分解路径 ──
        if source_ctx and source_ctx.results:
            source_text = "\n\n" + source_ctx.format_for_prompt()
            constraint_text = FROM_SOURCES_CONSTRAINT

        prompt = DECOMPOSER_PROMPT.format(
            query=query,
            source_context=source_text,
            source_constraint=constraint_text,
        )

        max_tok = 8192 if source_ctx and source_ctx.results else 4096
        response = await self.llm.complete(
            system_prompt=CONSTITUTIONAL_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.7,
            max_tokens=max_tok,
        )

        return self._parse(response.content)

    def _parse(self, content: str) -> tuple[Perspective, Perspective, list[str]]:
        """Parse LLM decomposition output into structured perspectives."""
        pa = Perspective(name="Perspective A", content="")
        pb = Perspective(name="Perspective B", content="")
        tensions: list[str] = []
        current_section: str | None = None

        for line in content.split("\n"):
            ls = line.strip()
            if not ls:
                continue

            if "[视角A]" in ls or ls.startswith("[视角A]"):
                current_section = "A"
                ls = ls.replace("[视角A]", "").strip()
            elif "[视角B]" in ls or ls.startswith("[视角B]"):
                current_section = "B"
                ls = ls.replace("[视角B]", "").strip()

            if current_section == "A":
                if ls.startswith("视角名称:"):
                    pa.name = ls.replace("视角名称:", "").strip()
                elif ls.startswith("核心论证:"):
                    pa.content += ls.replace("核心论证:", "").strip() + "\n"
                elif ls.startswith("理论资源:"):
                    pa.theorists_cited = [t.strip() for t in ls.replace("理论资源:", "").split(",")]
                elif ls.startswith("关键概念:"):
                    pa.concepts_used = [c.strip() for c in ls.replace("关键概念:", "").split(",")]
                elif "[张力标记A]:" in ls:
                    t = ls.split("]:", 1)[-1].strip()
                    pa.tension_points.append(t)
                    tensions.append(f"[硬张力](A->B): {t}")
                else:
                    pa.content += ls + "\n"

            elif current_section == "B":
                if ls.startswith("视角名称:"):
                    pb.name = ls.replace("视角名称:", "").strip()
                elif ls.startswith("核心论证:"):
                    pb.content += ls.replace("核心论证:", "").strip() + "\n"
                elif ls.startswith("理论资源:"):
                    pb.theorists_cited = [t.strip() for t in ls.replace("理论资源:", "").split(",")]
                elif ls.startswith("关键概念:"):
                    pb.concepts_used = [c.strip() for c in ls.replace("关键概念:", "").split(",")]
                elif "[张力标记B]:" in ls:
                    t = ls.split("]:", 1)[-1].strip()
                    pb.tension_points.append(t)
                    tensions.append(f"[硬张力](B->A): {t}")
                else:
                    pb.content += ls + "\n"

        return pa, pb, tensions
