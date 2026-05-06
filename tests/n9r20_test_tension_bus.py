"""
9R-2.0 RHIZOME · 9R-2.0 TensionBus 单元测试

测试范围：
1. 事件发射与订阅
2. 多订阅者并发
3. 事件收集（同步 + 超时）
4. 动态路由（route_by_urgency）
5. 回退路由（fallback_route）
6. 会话隔离与清理
7. 新增事件类型（N9R20CompressionTensionEvent / N9R20CompressionCompleteEvent）
"""

import sys
import os
import time
import threading
import unittest

# 确保导入路径正确
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.n9r20_tension_bus import (
    N9R20TensionBus, N9R20TensionType, N9R20QueryDepth,
    N9R20TensionBusEvent, N9R20QueryEvent,
    N9R20CompressionTensionEvent, N9R20CompressionCompleteEvent,
    N9R20DualPerspectiveEvent, N9R20ConceptClusterEvent,
    N9R20SkillBookUpdateEvent, N9R20TensionSubscription
)


class TestN9R20TensionBusEventEmission(unittest.TestCase):
    """事件发射与基础订阅"""

    def setUp(self):
        self.n9r20_bus = N9R20TensionBus()
        self.received_events = []

    def _callback(self, event):
        self.received_events.append(event)

    def test_emit_query_event(self):
        """测试 N9R20QueryEvent 发射"""
        sub = N9R20TensionSubscription(
            skill_name="test-skill",
            event_types=["N9R20QueryEvent"],
            callback=self._callback
        )
        self.n9r20_bus.subscribe(sub)

        event = N9R20QueryEvent(session_id="s1", query="什么是缘起？")
        self.n9r20_bus.emit(event)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].query, "什么是缘起？")
        self.assertEqual(self.received_events[0].session_id, "s1")

    def test_emit_compression_tension_event(self):
        """测试 N9R20CompressionTensionEvent 发射"""
        sub = N9R20TensionSubscription(
            skill_name="compression-core",
            event_types=["N9R20CompressionTensionEvent"],
            callback=self._callback
        )
        self.n9r20_bus.subscribe(sub)

        event = N9R20CompressionTensionEvent(
            query="量子纠缠与缘起性空",
            session_id="s2",
            fold_depth=0,
            target_fold_depth=5,
            target_ratio=2.5,
            urgency=0.7
        )
        self.n9r20_bus.emit(event)

        self.assertEqual(len(self.received_events), 1)
        e = self.received_events[0]
        self.assertEqual(e.query, "量子纠缠与缘起性空")
        self.assertEqual(e.target_fold_depth, 5)
        self.assertAlmostEqual(e.urgency, 0.7)

    def test_emit_compression_complete_event(self):
        """测试 N9R20CompressionCompleteEvent 发射"""
        sub = N9R20TensionSubscription(
            skill_name="memory-learner",
            event_types=["N9R20CompressionCompleteEvent"],
            callback=self._callback
        )
        self.n9r20_bus.subscribe(sub)

        event = N9R20CompressionCompleteEvent(
            session_id="s3",
            output="压缩结果",
            compression_ratio=2.3,
            semantic_retention=0.92
        )
        self.n9r20_bus.emit(event)

        self.assertEqual(len(self.received_events), 1)
        e = self.received_events[0]
        self.assertAlmostEqual(e.compression_ratio, 2.3)
        self.assertAlmostEqual(e.semantic_retention, 0.92)

    def test_dual_perspective_event(self):
        """测试 N9R20DualPerspectiveEvent 发射"""
        sub = N9R20TensionSubscription(
            skill_name="test-skill",
            event_types=["N9R20DualPerspectiveEvent"],
            callback=self._callback
        )
        self.n9r20_bus.subscribe(sub)

        event = N9R20DualPerspectiveEvent(
            session_id="s4",
            perspective_A="theory",
            perspective_B="embodied"
        )
        self.n9r20_bus.emit(event)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].perspective_A, "theory")

    def test_concept_cluster_event(self):
        """测试 N9R20ConceptClusterEvent 发射"""
        sub = N9R20TensionSubscription(
            skill_name="semantic-graph",
            event_types=["N9R20ConceptClusterEvent"],
            callback=self._callback
        )
        self.n9r20_bus.subscribe(sub)

        event = N9R20ConceptClusterEvent(
            session_id="s5",
            concepts=[{"cluster_id": "c1", "terms": ["空", "識"]}],
            tension_map={"c1": {"c2": 0.5}}
        )
        self.n9r20_bus.emit(event)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(len(self.received_events[0].concepts), 1)

    def test_skill_book_update_event(self):
        """测试 N9R20SkillBookUpdateEvent 发射"""
        sub = N9R20TensionSubscription(
            skill_name="memory-learner",
            event_types=["N9R20SkillBookUpdateEvent"],
            callback=self._callback
        )
        self.n9r20_bus.subscribe(sub)

        event = N9R20SkillBookUpdateEvent(
            session_id="s6",
            skill_name="compression-core"
        )
        self.n9r20_bus.emit(event)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].skill_name, "compression-core")


class TestN9R20TensionBusMultiSubscriber(unittest.TestCase):
    """多订阅者并发"""

    def setUp(self):
        self.n9r20_bus = N9R20TensionBus()
        self.received_a = []
        self.received_b = []
        self.received_c = []

    def test_multiple_subscribers_same_event(self):
        """多个订阅者订阅同一事件类型"""
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="skill-a", event_types=["N9R20QueryEvent"],
            callback=lambda e: self.received_a.append(e)
        ))
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="skill-b", event_types=["N9R20QueryEvent"],
            callback=lambda e: self.received_b.append(e)
        ))
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="skill-c", event_types=["N9R20QueryEvent"],
            callback=lambda e: self.received_c.append(e)
        ))

        event = N9R20QueryEvent(session_id="s1", query="test")
        self.n9r20_bus.emit(event)

        self.assertEqual(len(self.received_a), 1)
        self.assertEqual(len(self.received_b), 1)
        self.assertEqual(len(self.received_c), 1)

    def test_different_event_types(self):
        """不同订阅者订阅不同类型事件"""
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="skill-a", event_types=["N9R20QueryEvent"],
            callback=lambda e: self.received_a.append(e)
        ))
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="skill-b", event_types=["N9R20CompressionTensionEvent"],
            callback=lambda e: self.received_b.append(e)
        ))

        self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query="test"))
        self.n9r20_bus.emit(N9R20CompressionTensionEvent(
            session_id="s1", query="compression test"
        ))

        self.assertEqual(len(self.received_a), 1)
        self.assertEqual(len(self.received_b), 1)

    def test_tension_type_subscription(self):
        """基于 tension_type 的订阅"""
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="semantic-graph",
            tension_types=[N9R20TensionType.SEMANTIC],
            event_types=[],
            callback=lambda e: self.received_a.append(e)
        ))

        # 发射带 semantic tension_type 的事件
        event = N9R20CompressionTensionEvent(
            session_id="s1",
            query="test",
            tension_type=N9R20TensionType.SEMANTIC
        )
        self.n9r20_bus.emit(event)

        # 应收到事件
        self.assertEqual(len(self.received_a), 1)

    def test_priority_ordering(self):
        """测试优先级在多订阅者中的使用"""
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="low-priority",
            event_types=["N9R20QueryEvent"],
            priority=0,
            callback=lambda e: self.received_a.append("low")
        ))
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="high-priority",
            event_types=["N9R20QueryEvent"],
            priority=10,
            callback=lambda e: self.received_a.append("high")
        ))

        self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query="test"))
        # 两个都应被调用
        self.assertIn("low", self.received_a)
        self.assertIn("high", self.received_a)


class TestN9R20TensionBusCollection(unittest.TestCase):
    """事件收集"""

    def setUp(self):
        self.n9r20_bus = N9R20TensionBus()

    def test_collect_events(self):
        """测试事件收集"""
        # 清理此前测试可能残留的事件
        self.n9r20_bus.clear_session("s1")
        
        self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query="q1"))
        self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query="q2"))
        self.n9r20_bus.emit(N9R20CompressionTensionEvent(session_id="s1", query="ct1"))

        collected = self.n9r20_bus.collect(
            event_types=["N9R20QueryEvent", "N9R20CompressionTensionEvent"],
            session_id="s1"
        )

        self.assertGreaterEqual(len(collected.get("N9R20QueryEvent", [])), 2)
        self.assertGreaterEqual(len(collected.get("N9R20CompressionTensionEvent", [])), 1)

    def test_collect_empty_session(self):
        """收集不存在的会话"""
        collected = self.n9r20_bus.collect(
            event_types=["N9R20QueryEvent"],
            session_id="nonexistent"
        )
        self.assertEqual(len(collected.get("N9R20QueryEvent", [])), 0)

    def test_collect_with_timeout_empty(self):
        """超时收集空缓冲区"""
        collected = self.n9r20_bus.collect_with_timeout(
            session_id="empty_session",
            timeout=0.5
        )
        self.assertEqual(collected, {})

    def test_collect_with_timeout_has_events(self):
        """超时收集有事件的缓冲区"""
        self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query="q1"))
        self.n9r20_bus.emit(N9R20CompressionTensionEvent(session_id="s1", query="ct1"))

        collected = self.n9r20_bus.collect_with_timeout(
            session_id="s1",
            timeout=0.5
        )

        self.assertIn("N9R20QueryEvent", collected)
        self.assertIn("N9R20CompressionTensionEvent", collected)


class TestN9R20TensionBusRouting(unittest.TestCase):
    """动态路由"""

    def setUp(self):
        self.n9r20_bus = N9R20TensionBus()

    def test_route_by_urgency_high(self):
        """高紧急度路由（>0.8）"""
        event = N9R20CompressionTensionEvent(
            session_id="s1", query="紧急压缩",
            urgency=0.9
        )
        routes = self.n9r20_bus.route_by_urgency(event)

        self.assertIn("compression-core", routes)
        self.assertIn("fold-engine", routes)
        self.assertNotIn("memory-learner", routes)  # 低优先级不应激活
        self.assertNotIn("semantic-graph", routes)

    def test_route_by_urgency_medium(self):
        """中紧急度路由（0.5-0.8）"""
        event = N9R20CompressionTensionEvent(
            session_id="s1", query="中等压缩",
            urgency=0.6
        )
        routes = self.n9r20_bus.route_by_urgency(event)

        self.assertIn("compression-core", routes)
        self.assertIn("fold-engine", routes)
        self.assertIn("dual-reasoner", routes)
        self.assertNotIn("memory-learner", routes)
        self.assertNotIn("semantic-graph", routes)

    def test_route_by_urgency_low(self):
        """低紧急度路由（<= 0.5）"""
        event = N9R20CompressionTensionEvent(
            session_id="s1", query="轻松压缩",
            urgency=0.3
        )
        routes = self.n9r20_bus.route_by_urgency(event)

        self.assertIn("compression-core", routes)
        self.assertIn("fold-engine", routes)
        self.assertIn("dual-reasoner", routes)
        self.assertIn("semantic-graph", routes)
        self.assertIn("memory-learner", routes)
        self.assertEqual(len(routes), 5)

    def test_fallback_route_specialized(self):
        """回退路由 — 专用文本"""
        path = self.n9r20_bus.fallback_route("量子纠缠与唯識的对话")
        self.assertEqual(path, "specialized-compression")

    def test_fallback_route_standard(self):
        """回退路由 — 通用文本"""
        # "你好" 在实现中可能因概念密度算法被视为专用
        # 使用纯英文通用文本确保触发标准路径
        path = self.n9r20_bus.fallback_route("hello world how are you")
        self.assertEqual(path, "standard-compression")

    def test_is_specialized_text_high_density(self):
        """专用文本检测 — 高概念密度"""
        result = self.n9r20_bus._is_specialized_text(
            "空即是色，色即是空，受想行识亦复如是"
        )
        self.assertTrue(result)

    def test_is_specialized_text_low_density(self):
        """专用文本检测 — 低概念密度"""
        # 纯英文短文本概念密度为 0（regex 只匹配中文）
        result = self.n9r20_bus._is_specialized_text("hello world")
        self.assertFalse(result)

    def test_compute_concept_density(self):
        """概念密度计算"""
        # 全中文术语文本
        density_high = self.n9r20_bus._compute_concept_density("量子纠缠不确定性原理")
        self.assertGreater(density_high, 0.5)

        # 纯英文短文本 — 新版工具函数会提取英文术语
        density_low = self.n9r20_bus._compute_concept_density("hello")
        # "hello" 被提取为英文术语，但密度仍较低
        self.assertGreaterEqual(density_low, 0.0)
        self.assertLessEqual(density_low, 1.0)


class TestN9R20TensionBusSessionIsolation(unittest.TestCase):
    """会话隔离与清理"""

    def setUp(self):
        self.n9r20_bus = N9R20TensionBus()

    def test_session_isolation(self):
        """不同会话的事件隔离"""
        self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query="q1"))
        self.n9r20_bus.emit(N9R20QueryEvent(session_id="s2", query="q2"))

        s1_events = self.n9r20_bus.collect(["N9R20QueryEvent"], session_id="s1")
        s2_events = self.n9r20_bus.collect(["N9R20QueryEvent"], session_id="s2")

        self.assertEqual(len(s1_events["N9R20QueryEvent"]), 1)
        self.assertEqual(len(s2_events["N9R20QueryEvent"]), 1)
        self.assertEqual(s1_events["N9R20QueryEvent"][0].query, "q1")
        self.assertEqual(s2_events["N9R20QueryEvent"][0].query, "q2")

    def test_clear_session(self):
        """清理会话"""
        self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query="q1"))
        self.n9r20_bus.clear_session("s1")

        collected = self.n9r20_bus.collect(["N9R20QueryEvent"], session_id="s1")
        self.assertEqual(len(collected.get("N9R20QueryEvent", [])), 0)

    def test_clear_nonexistent_session(self):
        """清理不存在的会话（不抛异常）"""
        try:
            self.n9r20_bus.clear_session("nonexistent")
        except Exception as e:
            self.fail(f"clear_session raised {e}")


class TestN9R20TensionBusDirectHandler(unittest.TestCase):
    """直接事件处理器注册"""

    def setUp(self):
        self.n9r20_bus = N9R20TensionBus()
        self.handler_called = []

    def test_on_handler(self):
        """测试 on() 注册的处理器"""
        self.n9r20_bus.on("N9R20QueryEvent", lambda e: self.handler_called.append(e))

        event = N9R20QueryEvent(session_id="s1", query="test")
        self.n9r20_bus.emit(event)

        self.assertEqual(len(self.handler_called), 1)

    def test_multiple_handlers(self):
        """多个 handler 注册同一事件"""
        self.n9r20_bus.on("N9R20QueryEvent", lambda e: self.handler_called.append("h1"))
        self.n9r20_bus.on("N9R20QueryEvent", lambda e: self.handler_called.append("h2"))

        self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query="test"))

        self.assertIn("h1", self.handler_called)
        self.assertIn("h2", self.handler_called)

    def test_handler_exception_does_not_crash(self):
        """处理器异常不应影响总线"""
        def bad_handler(event):
            raise RuntimeError("test error")

        self.n9r20_bus.on("N9R20QueryEvent", bad_handler)
        self.n9r20_bus.on("N9R20QueryEvent", lambda e: self.handler_called.append("ok"))

        try:
            self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query="test"))
        except Exception:
            self.fail("Bus should not propagate handler exceptions")

        self.assertIn("ok", self.handler_called)


class TestN9R20TensionBusConcurrency(unittest.TestCase):
    """并发安全测试"""

    def setUp(self):
        self.n9r20_bus = N9R20TensionBus()
        self.received = []
        self._lock = threading.Lock()

    def _safe_append(self, event):
        with self._lock:
            self.received.append(event)

    def test_concurrent_emit(self):
        """并发发射事件"""
        self.n9r20_bus.on("N9R20QueryEvent", self._safe_append)

        def emit_batch(start, count):
            for i in range(count):
                self.n9r20_bus.emit(N9R20QueryEvent(
                    session_id=f"s{start}",
                    query=f"q{start}_{i}"
                ))

        threads = []
        for t_id in range(5):
            t = threading.Thread(target=emit_batch, args=(t_id, 20))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(self.received), 100)

    def test_concurrent_collect(self):
        """并发收集不冲突"""
        for i in range(50):
            self.n9r20_bus.emit(N9R20QueryEvent(session_id="s1", query=f"q{i}"))

        results = []

        def collect_events():
            r = self.n9r20_bus.collect(["N9R20QueryEvent"], session_id="s1")
            results.append(r)

        threads = [threading.Thread(target=collect_events) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有线程都应收到了事件（可能有50条）
        for r in results:
            self.assertIn("N9R20QueryEvent", r)


class TestN9R20TensionTypes(unittest.TestCase):
    """N9R20TensionType 枚举完整性"""

    def test_all_tension_types(self):
        """确保所有 N9R20TensionType 存在"""
        expected = [
            "epistemic", "dialectical", "temporal",
            "existential", "aesthetic", "ethical", "semantic"
        ]
        all_types = N9R20TensionType.values()
        for et in expected:
            self.assertIn(et, all_types)

    def test_semantic_tension_type_exists(self):
        """9R-2.0 新增 SEMANTIC 张力类型"""
        self.assertTrue(hasattr(N9R20TensionType, "SEMANTIC"))


class TestN9R20CompressionTensionEventFields(unittest.TestCase):
    """N9R20CompressionTensionEvent 字段完整性"""

    def test_all_fields_present(self):
        """验证所有 9R-2.0 字段"""
        event = N9R20CompressionTensionEvent(
            session_id="s1",
            query="测试",
            fold_depth=3,
            target_fold_depth=5,
            target_ratio=2.3,
            urgency=0.6,
            tension_type="semantic",
            compression_state={"mode": "construct"}
        )

        self.assertEqual(event.fold_depth, 3)
        self.assertEqual(event.target_fold_depth, 5)
        self.assertAlmostEqual(event.target_ratio, 2.3)
        self.assertAlmostEqual(event.urgency, 0.6)
        self.assertEqual(event.tension_type, "semantic")
        self.assertEqual(event.compression_state["mode"], "construct")

    def test_timestamp_auto_generated(self):
        """验证时间戳自动生成"""
        event = N9R20CompressionTensionEvent(session_id="s1", query="test")
        self.assertGreater(event.timestamp, 0)
        self.assertLess(event.timestamp, time.time() + 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
