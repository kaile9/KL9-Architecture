"""
KL9-RHIZOME V1.5 Coordinator — 新入口。
替代 run.py (v5.0 O1-O7 流水线)。
"""

import sys, time, uuid
from typing import Optional

SHARED_LIB = "/AstrBot/data/skills/kailejiu-shared/lib"
sys.path.insert(0, SHARED_LIB)
    SKILLS_ROOT = "/AstrBot/data/skills"
    if SKILLS_ROOT not in sys.path:
        sys.path.insert(0, SKILLS_ROOT)

from tension_bus import (
    bus as TensionBus,
    QueryEvent, InitialStateEvent, TensionEmittedEvent,
    ConceptBatchEvent, SoulParamsEvent, ResearchFindingsEvent,
    FoldCompleteEvent, TensionSubscription
)
from core_structures import DualState, Tension, Perspective, load_perspective, SuspensionAssessment
from perspective_types import PERSPECTIVE_TYPES, TENSION_TYPES, RECOMMENDED_DUALITIES, EMERGENT_STYLE_MAP
from emergent_style import emergent_style, emergent_style_prompt
from fold_depth_policy import determine_max_fold_depth
from suspension_evaluator import evaluate_suspension
from constitutional_dna import build_constitutional_prompt, constitutional_critique
from dual_fold import dual_fold, transform_from_perspective, structural_tension

# ── 加载后端模块 ──────────────────────────────────────────────────
import graph_backend as GB
import memory as MEM
import learner as L
import routing as ROUTE

# ── 灵魂模块 ──────────────────────────────────────────────────────
SOUL_SCRIPTS = "/AstrBot/data/skills/kailejiu-soul/scripts"
if SOUL_SCRIPTS not in sys.path:
    sys.path.insert(0, SOUL_SCRIPTS)
import soul_core as SOUL

# ── 加载 TensionBus subscriber（自注册设计）──────────────────────────────────────
# ── subscriber 显式加载 ──────────────────────────────────────
from kailejiu_graph.scripts import subscriber as graph_subscriber
from kailejiu_learner.scripts import subscriber as learner_subscriber



def coordinate(query: str, provider=None, session_id: Optional[str] = None) -> dict:
    """
    KL9-RHIZOME V1.5 协调器入口。
    替代 v5.0 的 run(query)。
    """
    session_id = session_id or str(uuid.uuid4())[:8]
    
    # Phase 0: 发射 query 到 TensionBus
    TensionBus.emit(QueryEvent(query=query, session_id=session_id))
    
    # Phase 1: 路由层 — 深度评估 + 二重性检测
    depth_assessment = ROUTE.route_query(query)
    
    # QUICK 模式：短问短答，不激活任何技能
    if depth_assessment.depth.name == "QUICK":
        response = _casual_respond(query)
        return {
            "response": response, "session_id": session_id,
            "mode": "casual", "fold_depth": 0,
            "tension_type": None, "suspension_quality": "N/A"
        }
    
    # Phase 1.5: 二重性检测 → 匹配视角对
    has_dual, _, _ = ROUTE.detect_dual_nature(query)
    dual_result = detect_dual_nature(query)  # 内部使用 RECOMMENDED_DUALITIES
    
    if dual_result is None and not has_dual:
        # 路由判断 STANDARD/DEEP 但无具体二重性 → 降级
        response = _casual_respond(query)
        return {
            "response": response, "session_id": session_id,
            "mode": "degraded", "fold_depth": 0,
            "tension_type": None, "suspension_quality": "N/A"
        }
    
    # 使用路由层的深度评估（非 detect_dual_nature 的 depth）
    if dual_result is None:
        # has_dual=True 但 RECOMMENDED_DUALITIES 无匹配 → 使用默认视角
        perspective_A_key, perspective_B_key, tension_type = (
            "temporal", "existential", "eternal_vs_finite"
        )
        max_fold = depth_assessment.max_fold_depth
    else:
        perspective_A_key, perspective_B_key, tension_type, _ = dual_result
        max_fold = depth_assessment.max_fold_depth  # 以路由层为准
    perspective_A = load_perspective(perspective_A_key)
    perspective_B = load_perspective(perspective_B_key)
    
    # Phase 2: 对话式激活（从 graph 检索理论）
    concepts = _retrieve_concepts(query, tension_type, perspective_A, perspective_B)
    activated_dialogue = _activate_dialogues(query, concepts, perspective_A, perspective_B)
    
    # Phase 3: 组装 DualState
    state = DualState(
        query=query, perspective_A=perspective_A, perspective_B=perspective_B,
        activated_dialogue=activated_dialogue, tension=None,
        tension_type=tension_type, suspended=False, forced=False,
        fold_depth=0, max_fold_depth=max_fold,
        source_skill="kailejiu-orchestrator"
    )
    
    # Phase 4: 递归 dual_fold
    state = dual_fold(state, depth=0, max_depth=state.max_fold_depth, provider=provider)
    
    # Phase 5: emergent_style + Constitutional DNA + Soul Guidance
    _ttype = state.tension.tension_type if state.tension else tension_type
    style = emergent_style(_ttype)
    constitutional_prompt = build_constitutional_prompt()
    
    # Soul 风格引导
    soul_guidance = SOUL.get_style_guidance(_ttype)
    soul_hint = ""
    if soul_guidance.get("ready"):
        affinities_str = ", ".join(f"{a[0]}({a[1]:.1f})" for a in soul_guidance.get("affinities", []))
        hints_str = "; ".join(soul_guidance.get("stylistic_hints", []))
        soul_hint = f"""
[灵魂状态: {soul_guidance.get('growth_phase')}]
理论共鸣: {affinities_str if affinities_str else '尚未成形'}
风格倾向: {hints_str}
张力感受: {soul_guidance.get('tension_feel', 0.3):.2f}
"""
    
    system_prompt = f"""{constitutional_prompt}
{emergent_style_prompt(_ttype)}{soul_hint}

当前二重态:
视角A: {state.perspective_A.name} — {state.perspective_A.characteristics}
视角B: {state.perspective_B.name} — {state.perspective_B.characteristics}
不可调和点: {state.tension.irreconcilable_points if state.tension else '待识别'}
折叠深度: {state.fold_depth}/{state.max_fold_depth}
悬置质量: {'真正悬置' if state.suspended and not state.forced else '强制悬置' if state.forced else '折叠中'}

任务: 从上述不可调和的张力中生成表达。保持张力，不缝合。"""
    
    response = _generate_response(query, system_prompt, provider)
    
    # Constitutional critique
    critique = constitutional_critique(response, str(state))
    if critique.get("violations"):
        response = _generate_response(query, system_prompt + "\n[修正] 上一轮输出违反宪政原则，请重新生成。", provider)
    
    # Phase 6: 记录
    TensionBus.emit(FoldCompleteEvent(state=state, response=response, session_id=session_id))
    
    try:
        MEM.record_dual_session(
            session_id=session_id, query=query, dual_state=state,
            response=response, suspension_quality=(
                "genuine" if state.suspended and not state.forced
                else "forced" if state.forced else "unknown"
            )
        )
    except Exception:
        pass
    
    # Phase 6.5: 学习摘要注入 + Soul 记录
    try:
        lean = L.get_lean_summary()
        MEM.inject_session_metadata(session_id, {"lean_summary": lean})
    except Exception:
        pass

    # Soul 更新（慢性烫伤 — 零 LLM，仅本地 EMA）
    try:
        theories = SOUL.extract_theories_from_dialogues(state.activated_dialogue)
        patterns = SOUL.extract_stylistic_patterns(response)
        SOUL.record_interaction(
            session_id=session_id,
            theories_used=theories,
            tension_type=_ttype,
            stylistic_patterns=patterns,
        )
    except Exception:
        pass
    
    TensionBus.clear_session(session_id)
    
    return {
        "response": response, "session_id": session_id,
        "mode": "academic",
        "tension_type": state.tension.tension_type if state.tension else tension_type,
        "fold_depth": state.fold_depth,
        "suspension_quality": "genuine" if (state.suspended and not state.forced) else "forced",
    }


def detect_dual_nature(query: str):
    """检测二重性张力。"""
    query_lower = query.lower()
    for duality in RECOMMENDED_DUALITIES:
        patterns = duality.get("typical_query_patterns", [])
        if any(p in query_lower for p in patterns):
            depth = determine_max_fold_depth(query, tension_type=duality.get("tension", ""))
            return (duality["perspective_A"], duality["perspective_B"],
                    duality["tension"], depth)
    return None


def _retrieve_concepts(query: str, tension_type: str, perspective_A=None, perspective_B=None, top_k: int = 6):
    """从图谱检索概念。优先张力共振，fallback BM25。"""
    try:
        if hasattr(GB, 'dialogical_retrieval'):
            tension_ctx = {
                "tension_type": tension_type,
                "perspective_a": perspective_A.name if perspective_A else "",
                "perspective_b": perspective_B.name if perspective_B else "",
            }
            pool = GB.dialogical_retrieval(query, tension_ctx, top_k=top_k)
            return pool.get("candidates", []) if isinstance(pool, dict) else []
    except Exception:
        pass
    try:
        return GB.search_concepts_bm25(query, top_k=top_k)
    except Exception:
        return []


def _activate_dialogues(query, concepts, perspective_A, perspective_B, max_theories: int = 3):
    """对话式理论激活。"""
    dialogues = []
    for c in concepts[:max_theories]:
        dialogues.append({
            "theory": c.get("name", ""),
            "thinker": c.get("thinker", ""),
            "original_frame": c.get("definition", c.get("tier1_def", "")),
            "transformed_frame": c.get("definition", c.get("tier1_def", "")),
            "transformation_tension": "",
        })
    return dialogues


def _casual_respond(query: str) -> str:
    if any(k in query for k in ["谢谢", "多谢"]):
        return "不必。"
    if any(k in query for k in ["你好", "嗨"]):
        return "请讲。"
    return "…"


def _generate_response(query, system_prompt, provider=None) -> str:
    if provider is not None:
        import asyncio
        async def _call():
            resp = await provider.text_chat(prompt=query, system_prompt=system_prompt)
            return resp.completion_text if hasattr(resp, 'completion_text') else str(resp)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, _call()).result(timeout=120)
            return loop.run_until_complete(_call())
        except Exception as e:
            return f"[生成失败: {e}]"
    return "[TEST_MODE] 二重态已构建，等待 LLM provider 注入。"


def status() -> dict:
    """获取系统状态。"""
    try:
        gs = GB.get_stats()
        ms = MEM.get_stats()
        lr = L.get_learner_report()
        return {"graph": gs, "memory": ms, "learner": lr}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    test_q = "福柯和韦伯的权力理论有什么根本差异？"
    result = coordinate(test_q)
    print(f"Tension: {result.get('tension_type')}, Fold: {result.get('fold_depth')}, Quality: {result.get('suspension_quality')}")
    print(result.get('response', '')[:200])
