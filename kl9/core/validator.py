"""
9R-2.1 — QualityValidator

LLM-as-judge final quality check. Runs ONCE after fold chain completes.
5-dimension scoring: theoretical framework, citations, argumentative depth,
stylistic quality, originality.

Also checks constitutional violations.
"""

from __future__ import annotations

from ..models import LLMProvider, QualityScore
from .dna import CONSTITUTIONAL_SYSTEM_PROMPT

VALIDATOR_PROMPT = """你是9R-2.1的质量审查官。对以下分析进行五维度评分（每项0-1）。

分析内容:
{content}

评分维度:
1. 理论框架 (权重0.20): 理论资源是否充分？概念是否被语境化改造而非空引？
2. 引用标准 (权重0.20): 引用密度是否足够？是否精确到作者/概念而非泛泛提及？
3. 信源忠实 (权重0.20): 断言是否可追溯到提供的检索信源？有无未经信源支撑的编造？
4. 论证深度 (权重0.20): 是否有不是X而是Y的区分性论证？是否避免了廉价缝合？
5. 文体质量 (权重0.10): 是否禁止第一人称/AI套话？长短句交替？结尾是否反诘/开放？
6. 原创性 (权重0.10): 是否产生了超出二手综述的洞见？是否有概念反转？

宪法违例检查:
- [硬张力]标记是否被缝合掉？结尾是否有"综上所述"?
- 是否使用了第一人称"我""笔者认为"?
- 引用是否只是名称堆砌而非语境改造?

输出格式 (严格JSON):
{{
  "theoretical_framework": <0-1>,
  "citation_standards": <0-1>,
  "source_fidelity": <0-1>,
  "argumentative_depth": <0-1>,
  "stylistic_quality": <0-1>,
  "originality": <0-1>,
  "constitutional_violations": ["violation1", "violation2"],
  "grade": "A/B/C/D",
  "summary": "一句话评估（不超过30字）"
}}
"""


class QualityValidator:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def validate(self, content: str) -> QualityScore:
        """Run final LLM-as-judge quality validation."""
        prompt = VALIDATOR_PROMPT.format(content=content[:8000])

        response = await self.llm.complete(
            system_prompt=CONSTITUTIONAL_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.2,
            max_tokens=1024,
        )

        return self._parse(response.content)

    def _parse(self, content: str) -> QualityScore:
        import json
        # Robust JSON extraction: scan backwards from every '{' using
        # json.JSONDecoder.raw_decode, which correctly handles nesting.
        try:
            for start in range(content.rfind("{"), -1, -1):
                if content[start] != "{":
                    continue
                try:
                    obj, _ = json.JSONDecoder().raw_decode(content, start)
                    if isinstance(obj, dict):
                        score = QualityScore(
                            theoretical_framework=float(obj.get("theoretical_framework", 0)),
                            citation_standards=float(obj.get("citation_standards", 0)),
                            source_fidelity=float(obj.get("source_fidelity", 0)),
                            argumentative_depth=float(obj.get("argumentative_depth", 0)),
                            stylistic_quality=float(obj.get("stylistic_quality", 0)),
                            originality=float(obj.get("originality", 0)),
                            constitutional_violations=obj.get("constitutional_violations", []),
                            grade=obj.get("grade", "D"),
                        )
                        score.assign_grade()
                        return score
                except json.JSONDecodeError:
                    continue
        except (KeyError, ValueError):
            pass
        return QualityScore()
