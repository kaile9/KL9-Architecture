#!/usr/bin/env python3
"""
kailejiu-reasoner TensionBus 订阅入口。
当被多入口激活时，独立从理论视角 transform query 并发射张力事件。
"""

import sys
import os

SHARED = os.path.join(os.path.dirname(__file__), '..', '..', 'kailejiu-shared', 'lib')
sys.path.insert(0, SHARED)

from tension_bus import bus, TensionSubscription, TensionEmittedEvent, QueryEvent
from perspective_types import PERSPECTIVE_TYPES


def on_query(event: QueryEvent):
    """接收 query，从理论视角做 transform 并发射张力。"""
    # 轻量：仅做字段启发式检测，不做完整 dual_fold
    query = event.query

    matched_types = []
    for ptype, info in PERSPECTIVE_TYPES.items():
        signals = info.get("signals", [])
        if any(s in query for s in signals):
            matched_types.append(ptype)

    if len(matched_types) >= 2:
        tension = type('Tension', (), {
            'tension_type': 'DIALECTICAL',
            'perspective_a': matched_types[0],
            'perspective_b': matched_types[1],
            'irreconcilable_points': [f"{matched_types[0]} vs {matched_types[1]}"],
            'activated_dialogue': [],
        })()
        bus.emit(TensionEmittedEvent(
            tension=tension,
            source_skill="kailejiu-reasoner",
            session_id=event.session_id,
        ))


def register():
    bus.subscribe(TensionSubscription(
        skill_name="kailejiu-reasoner",
        role="subscriber",
        tension_types=["EPISTEMIC", "DIALECTICAL"],
        event_types=["QueryEvent"],
        priority=8,
        callback=on_query,
    ))


register()
