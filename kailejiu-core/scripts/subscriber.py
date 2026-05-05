#!/usr/bin/env python3
"""
kailejiu-core TensionBus 订阅入口。
感知层第一入口：接收 QueryEvent → 检测二重性 → 发射 InitialStateEvent。
构建初始 DualState 并声明 Constitutional DNA 五原则。
"""

import sys
import os

SHARED = os.path.join(os.path.dirname(__file__), '..', '..', 'kailejiu-shared', 'lib')
sys.path.insert(0, SHARED)

from tension_bus import (
    bus, TensionSubscription, InitialStateEvent, QueryEvent, TensionEmittedEvent,
)
from core_structures import DualState, Perspective, load_perspective
from dual_fold import structural_tension
from constitutional_dna import build_constitutional_prompt
import routing as ROUTE


def on_query(event: QueryEvent):
    """
    接收 QueryEvent → 二重性检测 → 构建初始 DualState → 发射 InitialStateEvent。

    这是 KL9-RHIZOME 的感知层入口：在任何推理、检索、表达发生之前，
    先识别 query 的二重性并构建初始态。
    """
    query = event.query
    session_id = event.session_id

    # Step 1: 路由层二重性检测
    has_dual, tension_type, duality_score = ROUTE.detect_dual_nature(query)

    # Step 2: 无二重性 → 不构建 DualState
    if not has_dual:
        return

    # Step 3: 尝试匹配视角对
    from perspective_types import RECOMMENDED_DUALITIES
    matched = None
    query_lower = query.lower()
    for duality in RECOMMENDED_DUALITIES:
        patterns = duality.get("typical_query_patterns", [])
        if any(p in query_lower for p in patterns):
            matched = duality
            break

    if matched:
        pA_key = matched["perspective_A"]
        pB_key = matched["perspective_B"]
        tension_type = tension_type or matched.get("tension", "")
    else:
        # 有张力但无明确视角匹配 → 默认存在论视角
        pA_key = "temporal"
        pB_key = "existential"
        tension_type = tension_type or "eternal_vs_finite"

    perspective_A = load_perspective(pA_key)
    perspective_B = load_perspective(pB_key)

    if perspective_A is None or perspective_B is None:
        return

    # Step 4: 构建初始 DualState（含 Constitutional DNA）
    dna_prompt = build_constitutional_prompt()
    state = DualState(
        query=query,
        perspective_A=perspective_A,
        perspective_B=perspective_B,
        activated_dialogue=[{
            "theory": "Constitutional DNA",
            "thinker": "KL9-RHIZOME",
            "original_frame": dna_prompt[:200],
            "transformed_frame": dna_prompt[:200],
            "transformation_tension": "DNA声明不可变性",
        }],
        tension=None,
        tension_type=tension_type,
        suspended=False,
        forced=False,
        fold_depth=0,
        max_fold_depth=ROUTE.route_query(query).max_fold_depth,
        source_skill="kailejiu-core",
    )

    # Step 5: 单次发射 InitialStateEvent（含 DNA）
    bus.emit(InitialStateEvent(
        state=state,
        session_id=session_id,
        source_skill="kailejiu-core",
    ))


def register():
    bus.subscribe(TensionSubscription(
        skill_name="kailejiu-core",
        role="subscriber",
        tension_types=[
            "eternal_vs_finite", "mediated_vs_real", "regression_vs_growth",
            "freedom_vs_security", "economic_vs_grotesque", "truth_vs_slander",
            "EPISTEMIC", "DIALECTICAL",
        ],
        event_types=["QueryEvent"],
        priority=10,  # 最高优先级，最早感知
        callback=on_query,
    ))


register()
