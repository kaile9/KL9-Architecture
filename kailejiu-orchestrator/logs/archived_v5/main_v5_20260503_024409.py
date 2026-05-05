"""
kailejiu-orchestrator/scripts/main.py

O1→O7 pipeline: query understanding → memory retrieval → unconscious analysis
→ context assembly → LLM call → bounded self-reflection → humanize → record.

Designed to be called by AstrBot's skill system, or imported directly for testing.
"""

import sys
import uuid
import json
from typing import Optional

SHARED_LIB = "/AstrBot/data/skills/kailejiu-shared/lib"
sys.path.insert(0, SHARED_LIB)

import graph_backend as GB
import memory as MEM
import reasoner as R
import learner as L

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_REFLECT_ITERATIONS = 2

CORE_CONSTRAINTS = """
## 开了玖·硬约束（每条回复必须满足）

1. 无第一人称：禁止「我/我们/我认为」及任何对读者的直接呼告
2. 引文锚定：每个理论论断附具体著作《…》或思想家姓名+立场
3. 至少一处结构矛盾：用「然而/但/相反/吊诡/悖论」揭示，不缝合
4. 无结论性收束：禁止「因此/综上/总之/结论是/可见」
5. 无AI套话：禁止「让我们/首先/值得注意的是/从另一个角度来看」
6. 无鸡汤：禁止「加油/相信自己/努力就会成功」

## 表达原则

- 切口选取：从最具张力的具体细节切入，禁止从抽象概念开头
- 理论征用：概念是手术刀，不是权威背书
- 强制嫁接：裂缝在嫁接处自然暴露，不事先宣告
- 悖论悬置：不给解决方案，以反问或开放张力收尾
- 长句推进逻辑，短句制动节奏
"""

CASUAL_CONSTRAINTS = """
## Casual Mode
- 回复≤3句
- 禁止理论嫁接和引文
- 保持冷淡，禁止第一人称
- 禁止「加油/真棒/没关系」
"""

FALLBACK_MENTAL_MODELS = """
## 核心心智模型（概念图为空时使用）

1. 二重结构：宣称与运作逻辑的裂缝（通过嫁接制造，不是识别）
2. 代际断裂：不同代面对根本不同的问题域，旧框架不适用
3. 社会父亲失效：结构性失败先于个人道德判断
4. ACGN思想媒介：动漫游戏是最复杂的意识形态运作场所
5. 反救赎叙事：解决方案本身是虚假的——揭示之，不替代
"""


# ── Context Assembly ──────────────────────────────────────────────────────────

def _expand_concept(concept: dict, intent: str, query: str) -> str:
    """Select appropriate definition tier based on query intent."""
    name = concept.get("name", "")
    thinker = concept.get("thinker", "")

    if any(k in query for k in ["详细", "展开", "具体", "完整", "深入"]):
        defn = GB.expand_definition(name, thinker, tier=3)
    elif intent in ("comparative", "genealogical"):
        defn = GB.expand_definition(name, thinker, tier=2)
    else:
        defn = concept.get("tier1_def", name)

    if not defn.strip():
        defn = concept.get("tier2_def") or concept.get("tier1_def") or name

    thinker_str = f"（{thinker}）" if thinker else ""
    return f"- **{name}**{thinker_str}：{defn}"


def _format_edge(edge: dict, nodes_by_id: dict) -> str:
    from_node = nodes_by_id.get(edge.get("from_id", ""), {})
    to_node = nodes_by_id.get(edge.get("to_id", ""), {})
    rel = edge.get("rel_type", "")
    reason = edge.get("reason", "")
    from_name = from_node.get("name", edge.get("from_id", "?"))
    to_name = to_node.get("name", edge.get("to_id", "?"))
    base = f"  {from_name} →[{rel}]→ {to_name}"
    return base + (f"（{reason[:40]}）" if reason else "")


def _build_context(
    query: str,
    intent: str,
    complexity: float,
    concepts: list,
    subgraph: dict,
    books: list,
    unconscious: dict,
    is_casual: bool,
) -> str:
    """Assemble the full context block injected before user query."""
    parts = []

    if is_casual:
        parts.append(CASUAL_CONSTRAINTS)
        return "\n".join(parts)

    # Core constraints + expression principles
    parts.append(CORE_CONSTRAINTS)

    # Unconscious guidance (internal tensions → not stated, guide wording)
    unc_lines = []
    tensions = unconscious.get("tensions", [])
    contradictions = unconscious.get("contradictions", [])
    paradoxes = unconscious.get("paradoxes", [])
    strategy = unconscious.get("strategy", "chain_of_thought")

    if tensions or contradictions or paradoxes:
        unc_lines.append("## 无意识层（引导措辞，不要明说这些）")
        for t in tensions:
            unc_lines.append(f"- 张力：{t.get('note','')}")
        for c in contradictions:
            unc_lines.append(f"- 图谱矛盾：{c.get('from','')} ↔ {c.get('to','')}")
        for p in paradoxes:
            unc_lines.append(f"- 悖论：{p.get('note','')}")
        unc_lines.append(f"- 推理策略：{strategy}")
        parts.append("\n".join(unc_lines))

    # Reasoning strategy hint
    strategy_hints = {
        "debate":           "## 推理策略：Debate\n正题→反题→张力悬置（禁止综合）",
        "counterfactual":   "## 推理策略：Counterfactual\n暴露论断的隐含前提→揭示脆弱性→不给替代答案",
        "self_consistency": "## 推理策略：Self-Consistency\n从多个角度切入→选最有张力的一条主线",
        "chain_of_thought": "## 推理策略：Chain-of-Thought\n逐步推进，每步锚定具体引文",
    }
    if strategy in strategy_hints:
        parts.append(strategy_hints[strategy])

    # Retrieved concepts
    if concepts:
        concept_lines = ["## 图谱概念（可征用）"]
        for c in concepts:
            concept_lines.append(_expand_concept(c, intent, query))
        parts.append("\n".join(concept_lines))

        # Concept disambiguation warnings
        for c in concepts:
            variants = GB.find_same_name_variants(c.get("name", ""))
            if len(variants) > 1:
                thinkers = [v.get("thinker", "未知") for v in variants]
                parts.append(
                    f"⚠ 概念「{c.get('name')}」有多个版本：{' / '.join(t for t in thinkers if t)}"
                    f"——引用时必须指定思想家"
                )
    else:
        # Fallback to embedded mental models
        parts.append(FALLBACK_MENTAL_MODELS)

    # Subgraph relationships
    if subgraph.get("found") and subgraph.get("edges"):
        nodes_by_id = {n["id"]: n for n in subgraph.get("nodes", [])}
        edge_lines = ["## 概念关系（图谱边）"]
        shown = 0
        for edge in subgraph.get("edges", []):
            if shown >= 6:  # Cap to avoid token bloat
                break
            rel = edge.get("rel_type", "")
            if rel in ("CONTRADICTS", "CRITIQUES", "EXTENDS", "APPLIES_TO"):
                edge_lines.append(_format_edge(edge, nodes_by_id))
                shown += 1
        if shown > 0:
            parts.append("\n".join(edge_lines))

    # Relevant books
    if books and complexity > 0.3:
        book_lines = ["## 相关书目参考"]
        for b in books[:3]:
            note = b.get("impact_note", "")[:60]
            book_lines.append(f"- 《{b.get('title','')}》（{b.get('author','未知')}）：{note}")
        parts.append("\n".join(book_lines))

    return "\n\n".join(parts)


# ── LLM Caller (AstrBot-compatible interface) ─────────────────────────────────

def _call_llm(system_prompt: str, user_query: str, provider=None) -> str:
    """
    AstrBot skill system passes `provider` when calling from within a message handler.
    In test mode (provider=None) returns a mock academic response for validation.
    """
    if provider is not None:
        # AstrBot native call - executed in plugin context
        # provider is an LLMProvider instance
        import asyncio
        async def _async_call():
            response = await provider.text_chat(
                prompt=user_query,
                system_prompt=system_prompt,
            )
            return response.completion_text if hasattr(response, 'completion_text') else str(response)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _async_call())
                    return future.result(timeout=60)
            else:
                return loop.run_until_complete(_async_call())
        except Exception as e:
            return f"[LLM调用失败: {e}]"
    else:
        # Test/dry-run mode: return stub
        return "__TEST_MODE__"


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run(query: str, provider=None, session_id: Optional[str] = None) -> dict:
    """
    Full O1→O7 pipeline.

    Args:
        query:      User input string.
        provider:   AstrBot LLMProvider instance (None = test/dry-run mode).
        session_id: Optional pre-assigned session ID for feedback linking.

    Returns:
        {
            "response":     str,   # final user-facing text
            "session_id":   str,   # for feedback linking
            "mode":         str,   # "casual" | "academic"
            "field":        str,
            "strategy":     str,
            "concepts_used":list,
            "reflection":   dict,  # self-reflection result
            "is_test":      bool,
        }
    """

    # ── O1: Query Understanding ────────────────────────────────────────────
    intent = R.classify_intent(query)
    field = R.detect_field_heuristic(query)
    complexity = R.estimate_complexity(query)
    strategy = R.select_reasoning_strategy(intent, complexity)
    # Casual only if intent=casual AND field unknown AND query is trivially short
    # Field-aware: even short queries can be academic if field is detected
    # Thinker detection: any known thinker name in query → academic
    known_thinkers = ["福柯","韦伯","鲍德里亚","拉康","阿尔都塞","德里达","布尔迪厄",
                      "本雅明","阿多诺","葛兰西","齐泽克","巴特","阿甘本","马克思",
                      "黑格尔","康德","尼采","海德格尔","胡塞尔","德勒兹","涂尔干"]
    has_thinker = any(t in query for t in known_thinkers)
    has_academic_marker = any(k in query for k in ["理论","思想","哲学","批判","结构","权力","话语"])
    is_casual = (
        (intent == "casual" or complexity < 0.06)
        and field == "general"
        and not has_thinker
        and not has_academic_marker
    )

    result_meta = {
        "session_id": session_id or str(uuid.uuid4()),
        "mode": "casual" if is_casual else "academic",
        "field": field,
        "strategy": strategy,
        "concepts_used": [],
        "reflection": {},
        "is_test": (provider is None),
    }

    # ── O2: Memory Retrieval ───────────────────────────────────────────────
    concepts, books, subgraph = [], [], {"found": False}
    try:
        if not is_casual:
            concepts = GB.search_concepts_bm25(query, top_k=6)
            books = MEM.search_reading_list(query, top_k=3)
            if complexity > 0.4 and concepts:
                subgraph = GB.get_subgraph(concepts[0]["name"], max_hops=2)
    except Exception as e:
        # Graceful degradation: memory retrieval failure doesn't stop the pipeline
        result_meta["memory_error"] = str(e)

    result_meta["concepts_used"] = [c.get("name", "") for c in concepts]

    # ── O3: Unconscious Analysis ───────────────────────────────────────────
    unconscious = {}
    try:
        unconscious = R.unconscious_analysis(query, concepts)
    except Exception:
        unconscious = {"tensions": [], "contradictions": [], "paradoxes": [], "strategy": strategy}

    # ── O4: Context Assembly (Token Budget) ───────────────────────────────
    context_block = _build_context(
        query=query,
        intent=intent,
        complexity=complexity,
        concepts=concepts,
        subgraph=subgraph,
        books=books,
        unconscious=unconscious,
        is_casual=is_casual,
    )

    system_prompt = context_block
    user_prompt = query

    # ── O5: LLM Call + Bounded Self-Reflection ────────────────────────────
    response = _call_llm(system_prompt, user_prompt, provider)
    final_reflection = {"checks": {}, "all_passed": True, "failed": []}

    if provider is not None:
        # Only run reflection when we have a real LLM response
        for iteration in range(MAX_REFLECT_ITERATIONS):
            reflection = R.self_reflect(query, response)
            final_reflection = reflection

            if reflection["all_passed"]:
                break

            if iteration < MAX_REFLECT_ITERATIONS - 1:
                # Build corrective prompt and retry
                hint = R.generate_corrective_hint(reflection["failed"])
                corrective_system = context_block + "\n\n" + hint
                corrective_user = f"请重新回答（修正版）：{query}"
                response = _call_llm(corrective_system, corrective_user, provider)
            else:
                # Hit max iterations: append disclaimer, exit loop
                response = R.add_fallback_disclaimer(response, reflection["failed"])

    result_meta["reflection"] = final_reflection

    # ── O6: Humanize ──────────────────────────────────────────────────────
    if provider is not None:
        response = R.humanize(response)

    # ── O7: Record Session ────────────────────────────────────────────────
    try:
        MEM.record_session(
            session_id=result_meta["session_id"],
            query=query,
            response=response,
            concepts_used=result_meta["concepts_used"],
            field=field,
            reasoning_type=strategy,
        )
    except Exception as e:
        result_meta["record_error"] = str(e)

    # Update concept usage counts
    try:
        for c in concepts:
            GB.update_concept_weight(c.get("name", ""), delta=0.01)
    except Exception:
        pass

    result_meta["response"] = response
    return result_meta


# ── Feedback Handler ──────────────────────────────────────────────────────────

def handle_feedback(session_id: str, feedback_type: str, text: str = "") -> dict:
    """
    Public API for RLHF feedback.
    feedback_type: "correct" | "wrong" | "correction" | "clarification"
    """
    try:
        action = L.process_feedback(session_id, feedback_type, text)
        return {"ok": True, "action": action}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Status / Diagnostics ──────────────────────────────────────────────────────

def get_status() -> dict:
    """Return full system status for /learner_report command."""
    try:
        report = L.get_learner_report()
        return {"ok": True, **report}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── CLI entry point (for testing) ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 开了玖 Orchestrator — Dry Run ===\n")
    test_queries = [
        "谢谢",
        "福柯和韦伯的权力理论有什么根本差异？",
        "鲍德里亚拟像理论的思想来源",
        "动画《葬送的芙莉莲》中魔法的结构性意义",
        "今天天气怎么样",
    ]
    for q in test_queries:
        result = run(q, provider=None)
        print(f"[{result['mode'].upper():8}] {q}")
        print(f"         field={result['field']}, strategy={result['strategy']}")
        print(f"         concepts={result['concepts_used'][:3]}")
        print()
