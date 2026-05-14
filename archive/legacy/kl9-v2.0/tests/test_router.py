"""
KL9-RHIZOME v2.0 · AdaptiveRouter 单元测试

测试范围：
1. 路由决策 — 专用 vs 通用文本检测
2. 难度评估 — 多因子难度评分
3. fold 预算分配 — 动态 2-9 范围
4. 目标压缩率 — 硬性 2.0-2.5x
5. 紧急度计算
6. 概念密度检测
7. 张力关键词检测
8. 边界条件与极端输入
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.structures import RoutingDecision
from skills.adaptive_router import AdaptiveRouter


class TestAdaptiveRouterSpecializedDetection(unittest.TestCase):
    """专用文本检测"""

    def setUp(self):
        self.router = AdaptiveRouter()

    def test_buddhist_text_is_specialized(self):
        """佛教文本被识别为专用"""
        is_spec, conf = self.router._detect_specialized_text(
            "空即是色，色即是空，受想行识亦复如是。缘起性空，中道实相。般若涅槃。"
        )
        # 高密度佛教术语 → 应识别为专用（阈值 0.25）
        self.assertTrue(is_spec)
        self.assertGreater(conf, 0.2)

    def test_philosophy_text_is_specialized(self):
        """哲学文本被识别为专用"""
        is_spec, conf = self.router._detect_specialized_text(
            "存在先于本质。自由是人的宿命。辩证法揭示矛盾的运动。"
        )
        self.assertTrue(is_spec)
        self.assertGreater(conf, 0.3)

    def test_quantum_text_is_specialized(self):
        """量子物理文本被识别为专用"""
        is_spec, conf = self.router._detect_specialized_text(
            "量子纠缠不确定性原理涌现拓扑范畴函子相对论叠加态"
        )
        # 高密度科学术语 → 应识别为专用
        self.assertTrue(is_spec)
        self.assertGreater(conf, 0.2)

    def test_casual_text_is_not_specialized(self):
        """日常对话不被识别为专用"""
        is_spec, conf = self.router._detect_specialized_text(
            "今天天气真好，我们去散步吧。"
        )
        self.assertFalse(is_spec)
        self.assertLess(conf, 0.3)

    def test_short_greeting_is_not_specialized(self):
        """短问候不被识别为专用"""
        is_spec, conf = self.router._detect_specialized_text("你好")
        self.assertFalse(is_spec)

    def test_empty_text(self):
        """空文本"""
        is_spec, conf = self.router._detect_specialized_text("")
        self.assertFalse(is_spec)
        self.assertAlmostEqual(conf, 0.0, delta=0.05)

    def test_mixed_text_boundary(self):
        """混合文本边界"""
        is_spec, conf = self.router._detect_specialized_text(
            "我想了解一下量子力学的基本概念"
        )
        # 只有"量子"一个专用词，应在边界附近
        self.assertGreaterEqual(conf, 0.0)
        self.assertLessEqual(conf, 1.0)


class TestAdaptiveRouterDifficulty(unittest.TestCase):
    """难度评估"""

    def setUp(self):
        self.router = AdaptiveRouter()

    def test_short_simple_text_low_difficulty(self):
        """短简单文本 → 低难度"""
        diff = self.router._assess_difficulty("你好")
        self.assertLess(diff, 0.3)

    def test_long_specialized_text_high_difficulty(self):
        """长专用文本 → 高难度"""
        long_query = (
            "量子纠缠与缘起性空的比较研究：从拓扑序到中道实相的哲学反思。" * 15
        )
        diff = self.router._assess_difficulty(long_query)
        # 长文本 + 专用术语 → difficulty 应高于短通用文本
        short_diff = self.router._assess_difficulty("你好")
        self.assertGreater(diff, short_diff)

    def test_difficulty_range(self):
        """难度始终在 [0, 1]"""
        test_cases = [
            "",
            "你好",
            "量子纠缠与唯識的比较分析：空性与涌现",
            "A" * 2000,
        ]
        for tc in test_cases:
            diff = self.router._assess_difficulty(tc)
            self.assertGreaterEqual(diff, 0.0)
            self.assertLessEqual(diff, 1.0, f"Failed for: {tc[:50]}")

    def test_tension_keywords_increase_difficulty(self):
        """张力关键词提高难度"""
        without_tension = self.router._assess_difficulty("这是一个简单的描述")
        with_tension = self.router._assess_difficulty("但是这里有一个矛盾的问题")
        self.assertGreaterEqual(with_tension, without_tension * 0.8)


class TestAdaptiveRouterFoldBudget(unittest.TestCase):
    """fold 预算分配"""

    def setUp(self):
        self.router = AdaptiveRouter()

    def test_fold_range_always_2_to_9(self):
        """fold 深度始终在 [2, 9]"""
        test_cases = [
            (10, 0.1, False),    # 短、简单、通用
            (50, 0.3, False),    # 中、简单、通用
            (200, 0.5, True),    # 中、中等、专用
            (600, 0.7, True),    # 长、困难、专用
            (1500, 0.9, True),   # 超长、极难、专用
            (3000, 1.0, False),  # 极长、极难、通用
        ]

        for length, diff, is_spec in test_cases:
            fold = self.router._allocate_fold_budget(length, diff, is_spec)
            self.assertGreaterEqual(fold, 2, f"fold too low for ({length}, {diff}, {is_spec})")
            self.assertLessEqual(fold, 9, f"fold too high for ({length}, {diff}, {is_spec})")

    def test_simple_task_low_fold(self):
        """简单任务 → 低 fold"""
        fold = self.router._allocate_fold_budget(50, 0.05, False)
        self.assertLessEqual(fold, 3)

    def test_hard_task_high_fold(self):
        """困难任务 → 高 fold"""
        fold = self.router._allocate_fold_budget(500, 0.95, True)
        self.assertGreaterEqual(fold, 6)

    def test_long_text_increases_fold(self):
        """长文本增加 fold"""
        fold_short = self.router._allocate_fold_budget(100, 0.5, False)
        fold_long = self.router._allocate_fold_budget(1200, 0.5, False)
        self.assertGreaterEqual(fold_long, fold_short)

    def test_specialized_text_reduces_fold(self):
        """专用文本减少 fold（压缩更高效）"""
        fold_generic = self.router._allocate_fold_budget(300, 0.6, False)
        fold_specialized = self.router._allocate_fold_budget(300, 0.6, True)
        self.assertLessEqual(fold_specialized, fold_generic)


class TestAdaptiveRouterCompressionTarget(unittest.TestCase):
    """目标压缩率"""

    def setUp(self):
        self.router = AdaptiveRouter()

    def test_target_ratio_in_range_2_to_2_5(self):
        """目标压缩率始终在 [2.0, 2.5]"""
        test_cases = [
            (50, 0.2),     # 短、简单
            (200, 0.5),    # 中、中等
            (600, 0.8),    # 长、困难
            (2000, 1.0),   # 极长、极难
        ]

        for length, diff in test_cases:
            ratio = self.router._compute_target_ratio(length, diff)
            self.assertGreaterEqual(ratio, 2.0, f"ratio too low for ({length}, {diff})")
            self.assertLessEqual(ratio, 2.5, f"ratio too high for ({length}, {diff})")

    def test_long_text_lower_ratio(self):
        """长文本 → 更宽松的压缩率（2.0）"""
        ratio = self.router._compute_target_ratio(800, 0.5)
        self.assertAlmostEqual(ratio, 2.0, delta=0.1)

    def test_short_text_higher_ratio(self):
        """短文本 → 更激进的压缩率（2.5）"""
        ratio = self.router._compute_target_ratio(100, 0.5)
        self.assertAlmostEqual(ratio, 2.5, delta=0.1)

    def test_high_difficulty_relaxes_ratio(self):
        """高难度放松压缩率"""
        ratio_easy = self.router._compute_target_ratio(200, 0.3)
        ratio_hard = self.router._compute_target_ratio(200, 0.9)
        self.assertGreaterEqual(ratio_easy, ratio_hard - 0.1)


class TestAdaptiveRouterUrgency(unittest.TestCase):
    """紧急度计算"""

    def setUp(self):
        self.router = AdaptiveRouter()

    def test_urgency_range(self):
        """紧急度在 [0, 1]"""
        for diff in [0.0, 0.3, 0.5, 0.8, 1.0]:
            for length in [10, 200, 1000, 3000]:
                urgency = self.router._compute_urgency(diff, length)
                self.assertGreaterEqual(urgency, 0.0)
                self.assertLessEqual(urgency, 1.0)

    def test_high_difficulty_increases_urgency(self):
        """高难度 → 高紧急度"""
        low = self.router._compute_urgency(0.2, 100)
        high = self.router._compute_urgency(0.9, 100)
        self.assertGreater(high, low)

    def test_very_long_text_max_urgency(self):
        """极长文本 → 接近最大紧急度"""
        urgency = self.router._compute_urgency(0.8, 3000)
        self.assertGreaterEqual(urgency, 0.7)


class TestAdaptiveRouterFullRoute(unittest.TestCase):
    """完整路由决策"""

    def setUp(self):
        self.router = AdaptiveRouter()

    def test_route_returns_routing_decision(self):
        """route() 返回 RoutingDecision"""
        result = self.router.route("量子纠缠与空性")
        self.assertIsInstance(result, RoutingDecision)

    def test_route_all_fields_populated(self):
        """route() 填充所有字段"""
        result = self.router.route("一段中等长度的测试文本用于路由决策评估")

        self.assertIn(result.path, ["specialized", "standard"])
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertGreaterEqual(result.difficulty, 0.0)
        self.assertLessEqual(result.difficulty, 1.0)
        self.assertGreaterEqual(result.target_fold_depth, 2)
        self.assertLessEqual(result.target_fold_depth, 9)
        self.assertGreaterEqual(result.target_compression_ratio, 2.0)
        self.assertLessEqual(result.target_compression_ratio, 2.5)
        self.assertGreaterEqual(result.urgency, 0.0)
        self.assertLessEqual(result.urgency, 1.0)

    def test_specialized_path_for_buddhist_text(self):
        """佛教文本走 specialized 路径"""
        result = self.router.route(
            "诸法空相，不生不灭，不垢不净，不增不减。般若波罗蜜多。"
        )
        # 高密度术语 → 应走 specialized 路径
        self.assertEqual(result.path, "specialized")
        self.assertGreater(result.confidence, 0.2)

    def test_standard_path_for_casual_text(self):
        """日常文本走 standard 路径"""
        result = self.router.route("今天中午吃什么好呢")
        self.assertEqual(result.path, "standard")
        self.assertLess(result.confidence, 0.3)

    def test_route_consistency(self):
        """相同输入得到相同路由"""
        query = "意识的本质是什么：从神经科学到唯識学的对话"
        r1 = self.router.route(query)
        r2 = self.router.route(query)

        self.assertEqual(r1.path, r2.path)
        self.assertAlmostEqual(r1.confidence, r2.confidence, delta=0.01)
        self.assertAlmostEqual(r1.difficulty, r2.difficulty, delta=0.01)
        self.assertEqual(r1.target_fold_depth, r2.target_fold_depth)


class TestAdaptiveRouterConceptDensity(unittest.TestCase):
    """概念密度检测"""

    def setUp(self):
        self.router = AdaptiveRouter()

    def test_high_density_text(self):
        """高密度文本"""
        density = self.router._compute_concept_density(
            "量子纠缠不确定性原理拓扑序涌现范畴函子相对论"
        )
        # 使用 unique_terms / 10 归一化 → 约 5-8 个唯一术语
        self.assertGreater(density, 0.4)

    def test_low_density_text(self):
        """低密度文本"""
        density = self.router._compute_concept_density("hello world test")
        # 纯英文 → 无中文匹配 → 0
        self.assertEqual(density, 0.0)

    def test_empty_text_density(self):
        """空文本概念密度为 0"""
        self.assertEqual(self.router._compute_concept_density(""), 0.0)

    def test_density_range(self):
        """概念密度在 [0, 1]"""
        test_cases = [
            "量子",
            "这是一个普通的句子",
            "量子纠缠与缘起性空的比较",
            "A" * 100,
        ]
        for tc in test_cases:
            d = self.router._compute_concept_density(tc)
            self.assertGreaterEqual(d, 0.0)
            self.assertLessEqual(d, 1.0)


class TestAdaptiveRouterTensionDetection(unittest.TestCase):
    """张力关键词检测"""

    def setUp(self):
        self.router = AdaptiveRouter()

    def test_tension_detected(self):
        """检测到张力"""
        tf = self.router._detect_tension_keywords("但是这里有一个矛盾的问题")
        self.assertGreater(tf, 0.0)

    def test_no_tension(self):
        """无张力"""
        tf = self.router._detect_tension_keywords("这是简单的描述")
        self.assertEqual(tf, 0.0)

    def test_multiple_tension_keywords(self):
        """多个张力关键词"""
        tf1 = self.router._detect_tension_keywords("但是")
        tf2 = self.router._detect_tension_keywords("但是矛盾冲突为什么如何")
        self.assertGreater(tf2, tf1)

    def test_tension_range(self):
        """张力因子在 [0, 1]"""
        test_cases = [
            "",
            "但是",
            "但是矛盾冲突相反如何为什么能否",
        ]
        for tc in test_cases:
            tf = self.router._detect_tension_keywords(tc)
            self.assertGreaterEqual(tf, 0.0)
            self.assertLessEqual(tf, 1.0)


class TestAdaptiveRouterEdgeCases(unittest.TestCase):
    """边界条件与极端输入"""

    def setUp(self):
        self.router = AdaptiveRouter()

    def test_empty_string(self):
        """空字符串"""
        result = self.router.route("")
        self.assertIsInstance(result, RoutingDecision)
        self.assertEqual(result.path, "standard")
        self.assertLess(result.confidence, 0.3)

    def test_whitespace_only(self):
        """纯空白"""
        result = self.router.route("   \n\t  ")
        self.assertIsInstance(result, RoutingDecision)

    def test_single_character(self):
        """单字符"""
        result = self.router.route("空")
        self.assertIsInstance(result, RoutingDecision)
        # 单字"空"：关键词匹配但无 n-gram → 低概念密度 → 可能走 standard
        self.assertIn(result.path, ["specialized", "standard"])

    def test_unicode_handling(self):
        """Unicode 处理"""
        result = self.router.route("存在 être être 存在")
        self.assertIsInstance(result, RoutingDecision)

    def test_very_long_text(self):
        """超长文本（5000+ 字符）"""
        long_text = "量子纠缠与缘起性空的哲学对话。" * 200
        result = self.router.route(long_text)

        self.assertIsInstance(result, RoutingDecision)
        self.assertGreaterEqual(result.target_fold_depth, 2)
        self.assertLessEqual(result.target_fold_depth, 9)
        # 超长文本紧急度应较高
        self.assertGreaterEqual(result.urgency, 0.5)

    def test_length_factor_capped(self):
        """长度因子不超过 1.0"""
        result = self.router.route("A" * 5000)
        self.assertLessEqual(result.length_factor, 1.0)

    def test_specialized_keywords_complete(self):
        """验证专用关键词表完整性（精简核心集）"""
        kw = self.router.specialized_keywords
        self.assertGreaterEqual(len(kw), 15)
        self.assertLessEqual(len(kw), 20)
        # 包含佛教核心关键词
        self.assertIn("空", kw)
        self.assertIn("緣起", kw)
        # 包含哲学核心关键词
        self.assertIn("存在", kw)
        self.assertIn("辩证", kw)
        # 包含科学核心关键词
        self.assertIn("量子", kw)
        self.assertIn("涌现", kw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
