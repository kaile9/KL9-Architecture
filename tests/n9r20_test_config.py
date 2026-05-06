"""
9R-2.0 RHIZOME · 配置模块单元测试（补充版）
────────────────────────────────────────────────────────
在原有 n9r20_test_config.py 基础上，额外覆盖：
  - 所有配置类可实例化（通过各自 TestCase）
  - 默认值正确性（绝对值断言）
  - 配置常量范围合理性
  - N9R20LLMCompressorConfig 的基础配置
  - 配置类组合使用
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.n9r20_config import (
    N9R20RoutingConfig,
    N9R20CompressionConfig,
    N9R20MemoryConfig,
    N9R20SemanticGraphConfig,
    N9R20TensionConfig,
    n9r20_routing_config,
    n9r20_compression_config,
    n9r20_memory_config,
    n9r20_semantic_graph_config,
    n9r20_tension_config,
)
from core.n9r20_llm_compressor import N9R20LLMCompressorConfig


# ════════════════════════════════════════════════════════════════════
# § 1 · 所有配置类可实例化
# ════════════════════════════════════════════════════════════════════

class TestAllConfigsInstantiable(unittest.TestCase):
    """所有配置类均可通过默认构造函数实例化"""

    def test_routing_config_instantiable(self):
        """N9R20RoutingConfig 可实例化"""
        cfg = N9R20RoutingConfig()
        self.assertIsInstance(cfg, N9R20RoutingConfig)

    def test_compression_config_instantiable(self):
        """N9R20CompressionConfig 可实例化"""
        cfg = N9R20CompressionConfig()
        self.assertIsInstance(cfg, N9R20CompressionConfig)

    def test_memory_config_instantiable(self):
        """N9R20MemoryConfig 可实例化"""
        cfg = N9R20MemoryConfig()
        self.assertIsInstance(cfg, N9R20MemoryConfig)

    def test_semantic_graph_config_instantiable(self):
        """N9R20SemanticGraphConfig 可实例化"""
        cfg = N9R20SemanticGraphConfig()
        self.assertIsInstance(cfg, N9R20SemanticGraphConfig)

    def test_tension_config_instantiable(self):
        """N9R20TensionConfig 可实例化"""
        cfg = N9R20TensionConfig()
        self.assertIsInstance(cfg, N9R20TensionConfig)

    def test_llm_compressor_config_instantiable(self):
        """N9R20LLMCompressorConfig 可实例化"""
        cfg = N9R20LLMCompressorConfig()
        self.assertIsInstance(cfg, N9R20LLMCompressorConfig)

    def test_multiple_instances_independent(self):
        """多个实例互相独立（frozen dataclass 保证）"""
        r1 = N9R20RoutingConfig()
        r2 = N9R20RoutingConfig()
        # frozen dataclass：不同实例但内容相同，值相等
        self.assertEqual(r1.FOLD_DEPTH_MIN, r2.FOLD_DEPTH_MIN)
        self.assertEqual(r1.FOLD_DEPTH_MAX, r2.FOLD_DEPTH_MAX)


# ════════════════════════════════════════════════════════════════════
# § 2 · 默认值正确性（绝对值断言）
# ════════════════════════════════════════════════════════════════════

class TestRoutingConfigDefaults(unittest.TestCase):
    """N9R20RoutingConfig 默认值正确性"""

    def setUp(self):
        self.cfg = N9R20RoutingConfig()

    def test_fold_depth_min_is_2(self):
        """FOLD_DEPTH_MIN 默认值为 2"""
        self.assertEqual(self.cfg.FOLD_DEPTH_MIN, 2)

    def test_fold_depth_max_is_9(self):
        """FOLD_DEPTH_MAX 默认值为 9"""
        self.assertEqual(self.cfg.FOLD_DEPTH_MAX, 9)

    def test_fold_depth_default_is_4(self):
        """FOLD_DEPTH_DEFAULT 默认值为 4"""
        self.assertEqual(self.cfg.FOLD_DEPTH_DEFAULT, 4)

    def test_compression_ratio_min_is_2_0(self):
        """COMPRESSION_RATIO_MIN 默认值为 2.0"""
        self.assertAlmostEqual(self.cfg.COMPRESSION_RATIO_MIN, 2.0)

    def test_compression_ratio_max_is_2_5(self):
        """COMPRESSION_RATIO_MAX 默认值为 2.5"""
        self.assertAlmostEqual(self.cfg.COMPRESSION_RATIO_MAX, 2.5)

    def test_compression_ratio_default_is_2_5(self):
        """COMPRESSION_RATIO_DEFAULT 默认值为 2.5"""
        self.assertAlmostEqual(self.cfg.COMPRESSION_RATIO_DEFAULT, 2.5)

    def test_length_max_chars_is_1000(self):
        """LENGTH_MAX_CHARS 默认值为 1000"""
        self.assertEqual(self.cfg.LENGTH_MAX_CHARS, 1000)

    def test_quick_threshold_is_25(self):
        """QUICK_THRESHOLD_CHARS 默认值为 25"""
        self.assertEqual(self.cfg.QUICK_THRESHOLD_CHARS, 25)

    def test_difficulty_weights_exact(self):
        """难度权重精确默认值"""
        self.assertAlmostEqual(self.cfg.DIFFICULTY_WEIGHT_LENGTH, 0.2)
        self.assertAlmostEqual(self.cfg.DIFFICULTY_WEIGHT_CONCEPT, 0.3)
        self.assertAlmostEqual(self.cfg.DIFFICULTY_WEIGHT_TENSION, 0.2)
        self.assertAlmostEqual(self.cfg.DIFFICULTY_WEIGHT_SPECIALIZED, 0.3)


class TestCompressionConfigDefaults(unittest.TestCase):
    """N9R20CompressionConfig 默认值正确性"""

    def setUp(self):
        self.cfg = N9R20CompressionConfig()

    def test_simple_threshold_is_0_3(self):
        """MODE_SIMPLE_DIFFICULTY_THRESHOLD 默认值为 0.3"""
        self.assertAlmostEqual(self.cfg.MODE_SIMPLE_DIFFICULTY_THRESHOLD, 0.3)

    def test_medium_threshold_is_0_7(self):
        """MODE_MEDIUM_DIFFICULTY_THRESHOLD 默认值为 0.7"""
        self.assertAlmostEqual(self.cfg.MODE_MEDIUM_DIFFICULTY_THRESHOLD, 0.7)

    def test_simple_compress_ratio_is_0_6(self):
        """SIMPLE_COMPRESS_RATIO 默认值为 0.6"""
        self.assertAlmostEqual(self.cfg.SIMPLE_COMPRESS_RATIO, 0.6)

    def test_semantic_retention_threshold_is_0_85(self):
        """SEMANTIC_RETENTION_THRESHOLD 默认值为 0.85"""
        self.assertAlmostEqual(self.cfg.SEMANTIC_RETENTION_THRESHOLD, 0.85)

    def test_mode_sequences_correct(self):
        """模式序列默认值正确"""
        self.assertEqual(self.cfg.MODE_SEQUENCE_SIMPLE,
                         ["construct", "interrupt"])
        self.assertEqual(self.cfg.MODE_SEQUENCE_MEDIUM,
                         ["construct", "deconstruct", "interrupt"])
        self.assertEqual(self.cfg.MODE_SEQUENCE_HARD,
                         ["construct", "deconstruct", "validate", "interrupt"])


class TestMemoryConfigDefaults(unittest.TestCase):
    """N9R20MemoryConfig 默认值正确性"""

    def setUp(self):
        self.cfg = N9R20MemoryConfig()

    def test_max_memories_is_1000(self):
        """MAX_MEMORIES 默认值为 1000"""
        self.assertEqual(self.cfg.MAX_MEMORIES, 1000)

    def test_forget_halflife_is_86400(self):
        """FORGET_HALFLIFE 默认值为 86400（1 天秒数）"""
        self.assertAlmostEqual(self.cfg.FORGET_HALFLIFE, 86400.0)

    def test_forget_threshold_is_0_1(self):
        """FORGET_THRESHOLD 默认值为 0.1"""
        self.assertAlmostEqual(self.cfg.FORGET_THRESHOLD, 0.1)

    def test_propagation_rate_is_0_1(self):
        """PROPAGATION_RATE 默认值为 0.1"""
        self.assertAlmostEqual(self.cfg.PROPAGATION_RATE, 0.1)


class TestSemanticGraphConfigDefaults(unittest.TestCase):
    """N9R20SemanticGraphConfig 默认值正确性"""

    def setUp(self):
        self.cfg = N9R20SemanticGraphConfig()

    def test_edge_decay_halflife_is_3600(self):
        """EDGE_DECAY_HALFLIFE 默认值为 3600（1 小时秒数）"""
        self.assertAlmostEqual(self.cfg.EDGE_DECAY_HALFLIFE, 3600.0)

    def test_cluster_min_size_is_3(self):
        """CLUSTER_MIN_SIZE 默认值为 3"""
        self.assertEqual(self.cfg.CLUSTER_MIN_SIZE, 3)

    def test_path_max_depth_is_4(self):
        """PATH_MAX_DEPTH 默认值为 4"""
        self.assertEqual(self.cfg.PATH_MAX_DEPTH, 4)

    def test_prune_period_is_10(self):
        """PRUNE_PERIOD 默认值为 10"""
        self.assertEqual(self.cfg.PRUNE_PERIOD, 10)

    def test_edge_initial_weight_is_0_3(self):
        """EDGE_INITIAL_WEIGHT 默认值为 0.3"""
        self.assertAlmostEqual(self.cfg.EDGE_INITIAL_WEIGHT, 0.3)


class TestTensionConfigDefaults(unittest.TestCase):
    """N9R20TensionConfig 默认值正确性"""

    def setUp(self):
        self.cfg = N9R20TensionConfig()

    def test_default_tension_type_is_semantic(self):
        """DEFAULT_TENSION_TYPE 默认值为 'semantic'"""
        self.assertEqual(self.cfg.DEFAULT_TENSION_TYPE, "semantic")

    def test_default_intensity_is_0_5(self):
        """DEFAULT_INTENSITY 默认值为 0.5"""
        self.assertAlmostEqual(self.cfg.DEFAULT_INTENSITY, 0.5)

    def test_builtin_types_includes_semantic(self):
        """内置张力类型包含 'semantic'"""
        self.assertIn("semantic", self.cfg.BUILTIN_TENSION_TYPES)

    def test_builtin_types_count(self):
        """内置张力类型至少有 5 种"""
        self.assertGreaterEqual(len(self.cfg.BUILTIN_TENSION_TYPES), 5)


class TestLLMCompressorConfigDefaults(unittest.TestCase):
    """N9R20LLMCompressorConfig 默认值正确性"""

    def setUp(self):
        self.cfg = N9R20LLMCompressorConfig()

    def test_api_endpoint_default_empty(self):
        """api_endpoint 默认为空（表示未配置）"""
        self.assertEqual(self.cfg.api_endpoint, "")

    def test_api_key_default_empty(self):
        """api_key 默认为空（表示未配置）"""
        self.assertEqual(self.cfg.api_key, "")

    def test_model_name_default(self):
        """model_name 有合理的默认值"""
        self.assertIsInstance(self.cfg.model_name, str)
        self.assertGreater(len(self.cfg.model_name), 0)

    def test_fallback_to_simple_default_true(self):
        """fallback_to_simple 默认为 True（安全降级）"""
        self.assertTrue(self.cfg.fallback_to_simple)

    def test_max_tokens_positive(self):
        """max_tokens 为正数"""
        self.assertGreater(self.cfg.max_tokens, 0)

    def test_temperature_in_range(self):
        """temperature 在 [0, 2] 范围内"""
        self.assertGreaterEqual(self.cfg.temperature, 0.0)
        self.assertLessEqual(self.cfg.temperature, 2.0)

    def test_is_configured_false_by_default(self):
        """默认未配置 LLM（端点和密钥均为空）"""
        self.assertFalse(self.cfg.is_configured())

    def test_is_configured_true_when_both_set(self):
        """端点和密钥均设置时，is_configured 返回 True"""
        cfg = N9R20LLMCompressorConfig(
            api_endpoint="https://api.example.com",
            api_key="sk-test-key",
        )
        self.assertTrue(cfg.is_configured())

    def test_is_configured_false_when_only_endpoint(self):
        """仅设置端点时，is_configured 返回 False"""
        cfg = N9R20LLMCompressorConfig(api_endpoint="https://api.example.com")
        self.assertFalse(cfg.is_configured())

    def test_is_configured_false_when_only_key(self):
        """仅设置密钥时，is_configured 返回 False"""
        cfg = N9R20LLMCompressorConfig(api_key="sk-test")
        self.assertFalse(cfg.is_configured())


# ════════════════════════════════════════════════════════════════════
# § 3 · 配置常量范围合理性
# ════════════════════════════════════════════════════════════════════

class TestConfigConstantsRangeRationale(unittest.TestCase):
    """配置常量范围合理性综合测试"""

    def test_routing_fold_range_covers_useful_range(self):
        """Fold 深度范围 [2,9] 覆盖合理的思维折叠层级"""
        cfg = N9R20RoutingConfig()
        self.assertGreaterEqual(cfg.FOLD_DEPTH_MAX - cfg.FOLD_DEPTH_MIN, 5,
                                "Fold 深度范围至少跨越 5 个层级")

    def test_compression_ratio_range_is_tight(self):
        """压缩率范围 [2.0, 2.5] 为适度紧凑区间"""
        cfg = N9R20RoutingConfig()
        span = cfg.COMPRESSION_RATIO_MAX - cfg.COMPRESSION_RATIO_MIN
        self.assertLessEqual(span, 1.0, "压缩率范围不应超过 1.0")
        self.assertGreater(span, 0.0, "压缩率最大值必须大于最小值")

    def test_all_difficulty_weights_between_0_and_1(self):
        """所有难度权重分量均在 [0, 1] 内"""
        cfg = N9R20RoutingConfig()
        for attr in [
            "DIFFICULTY_WEIGHT_LENGTH",
            "DIFFICULTY_WEIGHT_CONCEPT",
            "DIFFICULTY_WEIGHT_TENSION",
            "DIFFICULTY_WEIGHT_SPECIALIZED",
        ]:
            w = getattr(cfg, attr)
            with self.subTest(attr=attr):
                self.assertGreaterEqual(w, 0.0)
                self.assertLessEqual(w, 1.0)

    def test_memory_forget_threshold_less_than_1(self):
        """遗忘阈值应小于 1.0（否则永不遗忘）"""
        cfg = N9R20MemoryConfig()
        self.assertLess(cfg.FORGET_THRESHOLD, 1.0)

    def test_propagation_rate_less_than_1(self):
        """传播率应小于 1.0（防止信息爆炸）"""
        cfg = N9R20MemoryConfig()
        self.assertLess(cfg.PROPAGATION_RATE, 1.0)

    def test_edge_decay_halflife_reasonable(self):
        """边衰减半衰期应在合理范围内（至少 60 秒）"""
        cfg = N9R20SemanticGraphConfig()
        self.assertGreaterEqual(cfg.EDGE_DECAY_HALFLIFE, 60.0)

    def test_edge_initial_weight_in_range(self):
        """边初始权重应在 (0, 1] 范围内"""
        cfg = N9R20SemanticGraphConfig()
        self.assertGreater(cfg.EDGE_INITIAL_WEIGHT, 0.0)
        self.assertLessEqual(cfg.EDGE_INITIAL_WEIGHT, 1.0)

    def test_semantic_retention_threshold_not_too_low(self):
        """语义保留率阈值不应过低（至少 0.5）"""
        cfg = N9R20CompressionConfig()
        self.assertGreaterEqual(cfg.SEMANTIC_RETENTION_THRESHOLD, 0.5)

    def test_tension_intensity_default_at_midpoint(self):
        """默认张力强度为中间值（0.5），允许双向调整"""
        cfg = N9R20TensionConfig()
        self.assertAlmostEqual(cfg.DEFAULT_INTENSITY, 0.5, places=1)

    def test_difficulty_thresholds_last_covers_all(self):
        """难度阈值最后一档应覆盖到 1.0 以上"""
        cfg = N9R20RoutingConfig()
        last_threshold = cfg.DIFFICULTY_THRESHOLDS[-1][0]
        self.assertGreaterEqual(last_threshold, 0.9,
                                "最后一个难度阈值应接近或等于 1.0")

    def test_cluster_max_iterations_reasonable(self):
        """簇检测最大迭代次数应在合理范围 [5, 100] 内"""
        cfg = N9R20SemanticGraphConfig()
        self.assertGreaterEqual(cfg.CLUSTER_MAX_ITERATIONS, 5)
        self.assertLessEqual(cfg.CLUSTER_MAX_ITERATIONS, 100)

    def test_module_singletons_are_correct_types(self):
        """模块级单例类型正确"""
        self.assertIsInstance(n9r20_routing_config, N9R20RoutingConfig)
        self.assertIsInstance(n9r20_compression_config, N9R20CompressionConfig)
        self.assertIsInstance(n9r20_memory_config, N9R20MemoryConfig)
        self.assertIsInstance(n9r20_semantic_graph_config, N9R20SemanticGraphConfig)
        self.assertIsInstance(n9r20_tension_config, N9R20TensionConfig)

    def test_simple_compress_ratio_less_than_1(self):
        """简单压缩比例应小于 1（确实在压缩）"""
        cfg = N9R20CompressionConfig()
        self.assertLess(cfg.SIMPLE_COMPRESS_RATIO, 1.0)
        self.assertGreater(cfg.SIMPLE_COMPRESS_RATIO, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
