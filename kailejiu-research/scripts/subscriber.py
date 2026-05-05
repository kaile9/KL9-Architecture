#!/usr/bin/env python3
"""
kailejiu-research TensionBus 订阅入口。
Dialogical Activation 层：接收 QueryEvent → 搜索理论 → 对话式改造 → 发射 ResearchFindingsEvent。
"""

import sys
import os

SHARED = os.path.join(os.path.dirname(__file__), '..', '..', 'kailejiu-shared', 'lib')
sys.path.insert(0, SHARED)

from tension_bus import (
    bus, TensionSubscription, ResearchFindingsEvent, QueryEvent, InitialStateEvent,
)
import graph_backend as GB
import routing as ROUTE


def dialogical_activation(query: str, tension_type: str = None, top_k: int = 5) -> list:
    """
    搜索相关理论并与之对话改造。
    
    Returns:
        List[dict] 每项含 theory/thinker/original_frame/transformed_frame/
                    transformation_tension/perspective_affinity/derived_tension_type
    """
    try:
        # 优先张力共振检索
        tension_ctx = None
        if tension_type:
            tension_ctx = {"tension_type": tension_type}
        
        result = GB.dialogical_retrieval(query, tension_ctx, top_k=top_k)
        candidates = result.get("candidates", []) if isinstance(result, dict) else []
    except Exception:
        try:
            candidates = GB.search_concepts_bm25(query, top_k=top_k)
        except Exception:
            candidates = []

    # 对话式改造：每条理论记录改造张力
    dialogues = []
    for c in candidates:
        original = c.get("definition", c.get("tier1_def", c.get("name", "")))
        transformed = original  # 无 LLM 时保持原框架不变

        dialogues.append({
            "theory": c.get("name", ""),
            "thinker": c.get("thinker", ""),
            "original_frame": original,
            "transformed_frame": transformed,
            "transformation_tension": f"检索-征用张力: 概念'{c.get('name')}'从图谱检索但未经对话改造",
            "perspective_affinity": c.get("tag", ""),
            "derived_tension_type": tension_type or "",
        })

    return dialogues


def on_query(event: QueryEvent):
    """接收 query，对话式激活理论，发射 ResearchFindingsEvent。"""
    query = event.query
    session_id = event.session_id

    # 检测二重性以推断张力类型
    has_dual, tension_type, _ = ROUTE.detect_dual_nature(query)

    if not has_dual:
        return  # 无二重性则跳过

    # 对话式激活
    findings = dialogical_activation(query, tension_type)

    if findings:
        bus.emit(ResearchFindingsEvent(
            findings=findings,
            source_skill="kailejiu-research",
            session_id=session_id,
        ))


def on_initial_state(event: InitialStateEvent):
    """
    接收 InitialStateEvent（来自 kailejiu-core），
    在 DualState 已构建后补充理论资源。
    """
    state = event.state
    query = state.query
    session_id = event.session_id

    # 使用 state 的 tension_type 进行精准检索
    tension_type = getattr(state, 'tension_type', None)
    findings = dialogical_activation(query, tension_type, top_k=3)

    if findings:
        # 注入到 state 的 activated_dialogue
        for f in findings:
            state.activated_dialogue.append(f)

        bus.emit(ResearchFindingsEvent(
            findings=findings,
            source_skill="kailejiu-research",
            session_id=session_id,
        ))


def register():
    # 订阅 QueryEvent（独立多入口激活）
    bus.subscribe(TensionSubscription(
        skill_name="kailejiu-research",
        role="subscriber",
        tension_types=[
            "eternal_vs_finite", "mediated_vs_real", "regression_vs_growth",
            "freedom_vs_security", "economic_vs_grotesque", "truth_vs_slander",
        ],
        event_types=["QueryEvent"],
        priority=6,
        callback=on_query,
    ))

    # 也订阅 InitialStateEvent 以补充 DualState
    bus.subscribe(TensionSubscription(
        skill_name="kailejiu-research",
        role="subscriber",
        tension_types=[
            "eternal_vs_finite", "mediated_vs_real", "regression_vs_growth",
            "freedom_vs_security", "economic_vs_grotesque", "truth_vs_slander",
        ],
        event_types=["InitialStateEvent"],
        priority=4,
        callback=on_initial_state,
    ))


register()
