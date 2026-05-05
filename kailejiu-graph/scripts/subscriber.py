#!/usr/bin/env python3
"""
kailejiu-graph TensionBus 订阅入口。
在 query 事件中独立检索概念图谱并发射 ConceptBatchEvent。
"""

import sys
import os

SHARED = os.path.join(os.path.dirname(__file__), '..', '..', 'kailejiu-shared', 'lib')
sys.path.insert(0, SHARED)

from tension_bus import bus, TensionSubscription, ConceptBatchEvent, QueryEvent
import graph_backend as GB


def on_query(event: QueryEvent):
    """接收 query，检索概念并发射。"""
    try:
        result = GB.dialogical_retrieval(event.query, None, top_k=6)
        concepts = result.get("candidates", [])
        if concepts:
            bus.emit(ConceptBatchEvent(
                concepts=concepts,
                source_skill="kailejiu-graph",
                session_id=event.session_id,
            ))
    except Exception:
        pass  # 图谱检索失败不中断


def register():
    bus.subscribe(TensionSubscription(
        skill_name="kailejiu-graph",
        role="subscriber",
        tension_types=["EPISTEMIC"],
        event_types=["QueryEvent"],
        priority=5,
        callback=on_query,
    ))


register()
