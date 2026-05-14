#!/usr/bin/env python3
"""
kailejiu-memory TensionBus 订阅入口。
持久记忆层：接收 FoldCompleteEvent → 记录折叠历史 → 持续参与 DualState 构建。
所有记忆保持活跃，无归档门控。检索由 tension_context 驱动。
"""

import sys
import os

SHARED = os.path.join(os.path.dirname(__file__), '..', '..', 'kailejiu-shared', 'lib')
sys.path.insert(0, SHARED)

from tension_bus import (
    bus, TensionSubscription, FoldCompleteEvent, InitialStateEvent,
)
import memory as M
import routing as ROUTE


def on_fold_complete(event: FoldCompleteEvent):
    """
    折叠完成后持久化记录。
    
    记录内容：
    - 折叠历史（作为 fold_node 图节点）
    - 张力特征（用于未来 tension_context 驱动检索）
    - 响应概要
    """
    try:
        state = event.state
        response = event.response
        session_id = event.session_id

        # 提取记录要素
        query = getattr(state, 'query', '')
        tension_type = getattr(state, 'tension_type', '')
        fold_depth = getattr(state, 'fold_depth', 0)
        suspended = getattr(state, 'suspended', False)
        forced = getattr(state, 'forced', False)

        # 提取激活的理论
        theories = []
        for d in getattr(state, 'activated_dialogue', []):
            thinker = d.get("thinker", "")
            theory = d.get("theory", "")
            if theory and theory not in theories:
                theories.append(theory)
            if thinker and thinker not in theories:
                theories.append(thinker)

        # 记录到记忆后端
        M.record_session(
            session_id=session_id,
            query=query,
            response=response[:800],
            tension_type=tension_type,
            fold_depth=fold_depth,
            suspended=suspended,
            forced=forced,
            theories=theories,
        )
    except Exception:
        pass  # 记忆记录失败不中断主流程


def on_initial_state(event: InitialStateEvent):
    """
    接收 InitialStateEvent，从记忆层注入历史上下文。
    
    使用 tension_context（非权重衰减）检索相关历史：
    - 相似张力类型的历史折叠
    - 相关理论的过往对话
    """
    try:
        state = event.state
        query = state.query
        tension_type = getattr(state, 'tension_type', '')

        if not tension_type:
            return

        # 张力上下文驱动检索（共振度排序）
        memory_context = M.retrieve_by_tension_context(
            query=query,
            tension_type=tension_type,
            top_k=3,
        )

        if memory_context:
            # 注入到 state 的记忆层
            state.activated_dialogue.append({
                "theory": "MemoryContext",
                "thinker": "KL9-RHIZOME",
                "original_frame": f"历史折叠 {len(memory_context)} 条",
                "transformed_frame": memory_context[0].get("response_preview", "") if memory_context else "",
                "transformation_tension": "记忆回流: 过往张力经验参与当前认知构建",
            })
    except Exception:
        pass


def register():
    # 接收折叠完成事件 → 持久化
    bus.subscribe(TensionSubscription(
        skill_name="kailejiu-memory",
        role="subscriber",
        tension_types=[
            "eternal_vs_finite", "mediated_vs_real", "regression_vs_growth",
            "freedom_vs_security", "economic_vs_grotesque", "truth_vs_slander",
        ],
        event_types=["FoldCompleteEvent"],
        priority=1,  # 折叠后最后记录
        callback=on_fold_complete,
    ))

    # 接收初始状态事件 → 注入历史上下文
    bus.subscribe(TensionSubscription(
        skill_name="kailejiu-memory",
        role="subscriber",
        tension_types=[
            "eternal_vs_finite", "mediated_vs_real", "regression_vs_growth",
            "freedom_vs_security", "economic_vs_grotesque", "truth_vs_slander",
        ],
        event_types=["InitialStateEvent"],
        priority=3,
        callback=on_initial_state,
    ))


register()
