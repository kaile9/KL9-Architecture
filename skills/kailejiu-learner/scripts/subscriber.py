#!/usr/bin/env python3
"""
kailejiu-learner TensionBus 订阅入口。
在 FoldCompleteEvent 后异步提取反馈信号并记录。
"""

import sys
import os

SHARED = os.path.join(os.path.dirname(__file__), '..', '..', 'kailejiu-shared', 'lib')
sys.path.insert(0, SHARED)

from tension_bus import bus, TensionSubscription, FoldCompleteEvent
import learner as L


def on_fold_complete(event: FoldCompleteEvent):
    """折叠完成后记录学习信号。"""
    try:
        state = event.state
        response = event.response
        session_id = event.session_id

        # 提取使用的理论
        theories = []
        for d in getattr(state, 'activated_dialogue', []):
            thinker = d.get("thinker", "")
            if thinker and thinker not in theories:
                theories.append(thinker)

        # 判断质量（简化版：有 genuine 悬置 = 正确）
        is_genuine = getattr(state, 'suspended', False) and not getattr(state, 'forced', False)
        feedback_type = "correct" if is_genuine else "wrong"

        L.process_feedback(session_id, feedback_type, response[:500])
    except Exception:
        pass


def register():
    bus.subscribe(TensionSubscription(
        skill_name="kailejiu-learner",
        role="subscriber",
        event_types=["FoldCompleteEvent"],
        priority=2,
        callback=on_fold_complete,
    ))


register()
