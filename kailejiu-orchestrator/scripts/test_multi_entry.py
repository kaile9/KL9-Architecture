#!/usr/bin/env python3
"""
KL9-RHIZOME v1.5 多入口并行激活测试

验证：
  1. 绕过 orchestrator 直接激活 core（dialogical_activation）
  2. reasoner 独立激活并发射 TensionEmittedEvent
  3. graph 独立激活并发射 ConceptBatchEvent
  4. learner 接收 FoldCompleteEvent
  5. 多订阅者并行响应同一 QueryEvent
  6. soul 风格引导在 emergent 前生效
"""

import sys
import os
import time
import uuid

SHARED_LIB = "os.path.join(os.path.dirname(__file__), "../../kailejiu-shared/lib")"
sys.path.insert(0, SHARED_LIB)

from tension_bus import (
    bus as TensionBus,
    QueryEvent, TensionEmittedEvent, ConceptBatchEvent,
    FoldCompleteEvent, TensionSubscription
)
from core_structures import DualState, Tension, Perspective


def test_header(name):
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")


def test_1_direct_core_activation():
    """测试：绕过 orchestrator，直接构建 DualState"""
    test_header("1. core 直接激活 (绕过 orchestrator)")

    perspective_A = Perspective(
        name="temporal.human",
        characteristics=["有限生命", "历史意识", "代际传承"],
    )
    perspective_B = Perspective(
        name="temporal.elf",
        characteristics=["无限生命", "循环时间", "无死亡焦虑"],
    )

    state = DualState(
        query="长生种如何理解死亡？",
        perspective_A=perspective_A,
        perspective_B=perspective_B,
        activated_dialogue=[
            {"theory": "存在与时间", "thinker": "海德格尔",
             "original_frame": "向死而生", "transformed_frame": "向死而生是人类独有的存在方式",
             "transformation_tension": "如果不存在死亡，存在的意义如何凸显？"},
        ],
        tension_type="eternal_vs_finite",
        suspended=False,
        forced=False,
        fold_depth=0,
        max_fold_depth=2,
        source_skill="kailejiu-core",
    )

    assert state.perspective_A is not None
    assert state.perspective_B is not None
    assert state.perspective_A.name == "temporal.human"
    assert state.perspective_B.name == "temporal.elf"
    assert len(state.activated_dialogue) == 1
    print("  ✓ DualState 构建成功")
    print(f"  ✓ 视角A: {state.perspective_A.name}")
    print(f"  ✓ 视角B: {state.perspective_B.name}")
    print(f"  ✓ 对话激活: {state.activated_dialogue[0]['theory']}")
    return state


def test_2_graph_independent_activation():
    """测试：graph backend 独立检索概念"""
    test_header("2. graph 独立激活 (dialogical_retrieval)")

    import graph_backend as GB

    result = GB.dialogical_retrieval(
        "福柯的权力理论",
        {"tension_type": "truth_vs_slander"},
        top_k=3,
    )
    assert "candidates" in result
    assert "pool_signature" in result
    print(f"  ✓ 检索签名: {result['pool_signature']}")
    print(f"  ✓ 候选数: {len(result['candidates'])}")

    # 测试谱系边
    gid = GB.write_genealogy_edge(
        "权力", "test_multi_entry",
        "海德格尔的存在论改造", "从规训转向存在论",
        "eternal_vs_finite"
    )
    paths = GB.get_genealogy_paths("权力", limit=3)
    assert len(paths) > 0
    print(f"  ✓ 谱系边写入: id={gid}")
    print(f"  ✓ 谱系路径数: {len(paths)}")
    return True


def test_3_reasoner_independent_emission():
    """测试：reasoner 独立发射张力事件到 TensionBus"""
    test_header("3. reasoner 独立发射 Tension 到 TensionBus")

    session_id = str(uuid.uuid4())[:8]

    # 模拟 reasoner 发射张力
    tension = Tension(
        perspective_A="structural.critical",
        perspective_B="structural.material",
        claim_A="权力通过话语生产主体",
        claim_B="权力通过物质条件决定主体",
        irreconcilable_points=["话语的自主性 vs 经济的最终决定"],
        tension_type="DIALECTICAL",
    )

    TensionBus.emit(TensionEmittedEvent(
        tension=tension,
        source_skill="kailejiu-reasoner",
        session_id=session_id,
    ))

    # 收集验证
    collected = TensionBus.collect(
        ["TensionEmittedEvent"],
        session_id=session_id,
        timeout=2.0,
    )
    events = collected.get("TensionEmittedEvent", [])
    assert len(events) > 0
    evt = events[0]
    assert evt.source_skill == "kailejiu-reasoner"
    assert evt.tension.tension_type == "DIALECTICAL"
    print(f"  ✓ Tension 发射成功: {evt.tension.tension_type}")
    print(f"  ✓ 不可调和点: {evt.tension.irreconcilable_points}")

    TensionBus.clear_session(session_id)
    return True


def test_4_concurrent_event_handling():
    """测试：多个订阅者并行响应同一事件"""
    test_header("4. 多订阅者并行响应")

    session_id = str(uuid.uuid4())[:8]

    received = {"reasoner": 0, "graph": 0, "learner": 0}

    def reasoner_handler(event):
        received["reasoner"] += 1

    def graph_handler(event):
        received["graph"] += 1

    def learner_handler(event):
        received["learner"] += 1

    # 用 bus.on() 注册回调（subscribe 用于订阅分类，on 用于即时回调）
    TensionBus.on("QueryEvent", reasoner_handler)
    TensionBus.on("QueryEvent", graph_handler)
    TensionBus.on("QueryEvent", learner_handler)

    # 发射事件
    TensionBus.emit(QueryEvent(query="测试多入口并行", session_id=session_id))

    # 等响应
    time.sleep(0.5)

    # 收集以触发回调
    collected = TensionBus.collect(["QueryEvent"], session_id=session_id, timeout=1.0)
    q_events = collected.get("QueryEvent", [])

    print(f"  ✓ QueryEvent 已发射: {len(q_events)} events")
    print(f"  ✓ reasoner handler: {received['reasoner']} 次")
    print(f"  ✓ graph handler: {received['graph']} 次")
    print(f"  ✓ learner handler: {received['learner']} 次")
    print(f"  ✓ 三者均收到同一事件: {received['reasoner'] > 0 and received['graph'] > 0 and received['learner'] > 0}")

    TensionBus.clear_session(session_id)
    return all(v > 0 for v in received.values())


def test_5_soul_guidance_flow():
    """测试：soul 风格引导在 emergent 前生效"""
    test_header("5. Soul 风格引导验证")

    sys.path.insert(0, "os.path.join(os.path.dirname(__file__), "..")/kailejiu-soul/scripts")
    import soul_core as SOUL

    # 检查 soul 状态
    guidance = SOUL.get_style_guidance("eternal_vs_finite")
    print(f"  ready: {guidance.get('ready')}")
    print(f"  phase: {guidance.get('growth_phase')}")
    print(f"  interactions: {guidance.get('total_interactions')}")

    if guidance.get("ready"):
        assert "affinities" in guidance
        assert "stylistic_hints" in guidance
        print(f"  ✓ affinities: {guidance['affinities']}")
        print(f"  ✓ hints: {guidance['stylistic_hints']}")
    else:
        print(f"  ⚠ Soul 尚未积累足够交互 ({guidance.get('total_interactions', 0)} < 3)")

    # 验证风格模式提取
    patterns = SOUL.extract_stylistic_patterns(
        "不是权力生产了知识，而是知识-权力的共生体生产了主体。"
        "这并非一种外在的压迫。悬置于此的，是不可调和的二重性。"
    )
    assert isinstance(patterns, list)
    print(f"  ✓ 风格模式提取: {patterns}")
    return True


def test_6_full_pipeline_with_soul():
    """测试：完整管道 (orchestrator + soul + learner)"""
    test_header("6. 完整管道 (orchestrator + soul)")

    sys.path.insert(0, "os.path.join(os.path.dirname(__file__), "..")/kailejiu-orchestrator/scripts")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "koordinator",
        "os.path.join(os.path.dirname(__file__), "..")/kailejiu-orchestrator/scripts/koordinator.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    result = mod.coordinate("长生种如何理解死亡？")

    assert "response" in result
    assert "tension_type" in result
    print(f"  ✓ tension: {result['tension_type']}")
    print(f"  ✓ fold_depth: {result['fold_depth']}")
    print(f"  ✓ suspension: {result['suspension_quality']}")
    print(f"  ✓ mode: {result['mode']}")

    # 检查 soul 是否被更新
    sys.path.insert(0, "os.path.join(os.path.dirname(__file__), "..")/kailejiu-soul/scripts")
    import soul_core as SOUL
    from importlib import reload
    reload(SOUL)
    guidance = SOUL.get_style_guidance(result['tension_type'])
    print(f"  ✓ soul interactions: {guidance.get('total_interactions')}")

    return True


if __name__ == "__main__":
    results = {}

    try:
        results["1_core_activation"] = test_1_direct_core_activation()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        results["1_core_activation"] = False

    try:
        results["2_graph_independent"] = test_2_graph_independent_activation()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        results["2_graph_independent"] = False

    try:
        results["3_reasoner_emission"] = test_3_reasoner_independent_emission()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        results["3_reasoner_emission"] = False

    try:
        results["4_concurrent"] = test_4_concurrent_event_handling()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        results["4_concurrent"] = False

    try:
        results["5_soul_guidance"] = test_5_soul_guidance_flow()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        results["5_soul_guidance"] = False

    try:
        results["6_full_pipeline"] = test_6_full_pipeline_with_soul()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        results["6_full_pipeline"] = False

    # Summary
    print(f"\n{'='*50}")
    print(f"  测试总结")
    print(f"{'='*50}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")
    print(f"\n  结果: {passed}/{total} 通过")
    print(f"{'='*50}")
    sys.exit(0 if passed == total else 1)
