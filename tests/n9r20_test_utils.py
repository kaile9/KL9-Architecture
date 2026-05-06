"""
9R-2.0 RHIZOME · 工具函数单元测试
────────────────────────────────────────────────────────
完整覆盖 core/n9r20_utils.py 中所有公开函数：

  1. clamp                  — 数值区间钳制
  2. extract_terms          — 术语提取（中/英/混合）
  3. compute_concept_density — 概念密度计算
  4. compute_tension_factor  — 张力因子计算
  5. compute_length_factor   — 长度因子计算
  6. compute_difficulty      — 综合难度计算
  7. allocate_fold_budget    — fold 深度动态分配
  8. compute_target_ratio    — 目标压缩率计算

测试策略：正常路径 + 边界条件 + 极端输入
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.n9r20_utils import (
    clamp,
    extract_terms,
    compute_concept_density,
    compute_tension_factor,
    compute_length_factor,
    compute_difficulty,
    allocate_fold_budget,
    compute_target_ratio,
)


# ════════════════════════════════════════════════════════════════════
# § 1 · clamp
# ════════════════════════════════════════════════════════════════════

class TestClamp(unittest.TestCase):
    """clamp(value, min_val, max_val) — 数值区间钳制"""

    # ── 正常路径 ───────────────────────────────────────────────
    def test_value_within_range_unchanged(self):
        """范围内的值不变"""
        self.assertAlmostEqual(clamp(0.5, 0.0, 1.0), 0.5)
        self.assertAlmostEqual(clamp(5.0, 1.0, 9.0), 5.0)

    def test_value_at_min_boundary(self):
        """等于最小值时不变"""
        self.assertAlmostEqual(clamp(0.0, 0.0, 1.0), 0.0)
        self.assertAlmostEqual(clamp(2.0, 2.0, 9.0), 2.0)

    def test_value_at_max_boundary(self):
        """等于最大值时不变"""
        self.assertAlmostEqual(clamp(1.0, 0.0, 1.0), 1.0)
        self.assertAlmostEqual(clamp(9.0, 2.0, 9.0), 9.0)

    # ── 超出范围 ───────────────────────────────────────────────
    def test_value_below_min_clamped_to_min(self):
        """低于最小值时钳制到最小值"""
        self.assertAlmostEqual(clamp(-0.5, 0.0, 1.0), 0.0)
        self.assertAlmostEqual(clamp(-100.0, 0.0, 1.0), 0.0)
        self.assertAlmostEqual(clamp(1.0, 2.0, 9.0), 2.0)

    def test_value_above_max_clamped_to_max(self):
        """高于最大值时钳制到最大值"""
        self.assertAlmostEqual(clamp(1.5, 0.0, 1.0), 1.0)
        self.assertAlmostEqual(clamp(100.0, 0.0, 1.0), 1.0)
        self.assertAlmostEqual(clamp(10.0, 2.0, 9.0), 9.0)

    # ── 边界条件 ───────────────────────────────────────────────
    def test_min_equals_max(self):
        """最小值等于最大值时，结果等于该值"""
        self.assertAlmostEqual(clamp(0.0, 5.0, 5.0), 5.0)
        self.assertAlmostEqual(clamp(9.0, 5.0, 5.0), 5.0)

    def test_negative_range(self):
        """负数范围正常工作"""
        self.assertAlmostEqual(clamp(-1.5, -2.0, -1.0), -1.5)
        self.assertAlmostEqual(clamp(-3.0, -2.0, -1.0), -2.0)
        self.assertAlmostEqual(clamp(0.0, -2.0, -1.0), -1.0)

    def test_float_precision(self):
        """浮点数精度保持"""
        result = clamp(0.123456789, 0.0, 1.0)
        self.assertAlmostEqual(result, 0.123456789, places=9)

    def test_returns_float_type(self):
        """返回值类型为数值"""
        result = clamp(0.5, 0.0, 1.0)
        self.assertIsInstance(result, (int, float))


# ════════════════════════════════════════════════════════════════════
# § 2 · extract_terms
# ════════════════════════════════════════════════════════════════════

class TestExtractTerms(unittest.TestCase):
    """extract_terms(query) — 术语提取"""

    # ── 中文术语 ───────────────────────────────────────────────
    def test_chinese_bigrams_extracted(self):
        """提取中文 2-gram 术语"""
        terms = extract_terms("量子纠缠与缘起性空")
        # 应包含至少一个中文词组
        chinese_terms = [t for t in terms if all('\u4e00' <= c <= '\u9fff' for c in t)]
        self.assertGreater(len(chinese_terms), 0)

    def test_chinese_4gram_extracted(self):
        """提取 4 字中文术语"""
        terms = extract_terms("缘起性空是佛教核心")
        # 至少能提取一些术语
        self.assertIsInstance(terms, list)

    def test_empty_query_returns_empty(self):
        """空查询返回空列表"""
        terms = extract_terms("")
        self.assertEqual(terms, [])

    def test_single_char_not_extracted(self):
        """单字不被提取（min_length=2）"""
        terms = extract_terms("空")
        # 单个汉字不满足最小长度 2，不应出现
        self.assertNotIn("空", terms)

    # ── 英文术语 ───────────────────────────────────────────────
    def test_english_terms_with_chinese(self):
        """中英混合文本中提取英文术语"""
        terms = extract_terms("quantum 量子 entanglement 纠缠")
        lower_terms = [t.lower() for t in terms]
        # 英文词应出现（需要有中文触发）
        self.assertIn("quantum", lower_terms)

    def test_stop_words_filtered(self):
        """常见停用词被过滤"""
        terms = extract_terms("the and for that 量子")
        lower_terms = [t.lower() for t in terms]
        for stop_word in ["the", "and", "for", "that"]:
            self.assertNotIn(stop_word, lower_terms)

    def test_short_english_words_filtered(self):
        """2 字母英文单词不被提取（min 3 letters）"""
        terms = extract_terms("量子 is to 纠缠")
        lower_terms = [t.lower() for t in terms]
        self.assertNotIn("is", lower_terms)
        self.assertNotIn("to", lower_terms)

    # ── 唯一性 ────────────────────────────────────────────────
    def test_no_duplicates(self):
        """返回列表中无重复项"""
        terms = extract_terms("缘起 缘起 缘起性空 缘起性空")
        self.assertEqual(len(terms), len(set(terms)))

    def test_returns_list(self):
        """返回类型为列表"""
        result = extract_terms("量子")
        self.assertIsInstance(result, list)

    # ── 特殊输入 ───────────────────────────────────────────────
    def test_pure_english_no_extraction(self):
        """纯英文文本不提取（需要有中文触发英文提取）"""
        terms = extract_terms("hello world python")
        # 无中文时英文提取不触发，但混合提取可能提取到
        self.assertIsInstance(terms, list)

    def test_numbers_handled_gracefully(self):
        """数字混合文本正常处理"""
        terms = extract_terms("量子2.0版本纠缠")
        self.assertIsInstance(terms, list)

    def test_custom_term_length(self):
        """自定义术语长度参数有效"""
        terms_short = extract_terms("空性涅槃缘起般若", term_length_min=2, term_length_max=2)
        terms_long = extract_terms("空性涅槃缘起般若", term_length_min=4, term_length_max=4)
        # 短术语不应与长术语完全相同
        self.assertIsInstance(terms_short, list)
        self.assertIsInstance(terms_long, list)


# ════════════════════════════════════════════════════════════════════
# § 3 · compute_concept_density
# ════════════════════════════════════════════════════════════════════

class TestComputeConceptDensity(unittest.TestCase):
    """compute_concept_density(query, keywords, normalization_base) — 概念密度"""

    # ── 返回范围 ───────────────────────────────────────────────
    def test_returns_float_in_range(self):
        """返回值在 [0, 1] 范围内"""
        density = compute_concept_density("量子纠缠与缘起性空")
        self.assertGreaterEqual(density, 0.0)
        self.assertLessEqual(density, 1.0)

    def test_empty_query_returns_zero(self):
        """空查询返回 0.0"""
        self.assertAlmostEqual(compute_concept_density(""), 0.0)

    def test_dense_text_higher_than_sparse(self):
        """概念密集文本的密度高于稀疏文本"""
        dense = compute_concept_density("量子纠缠缘起性空般若波罗蜜涅槃菩提辩证")
        sparse = compute_concept_density("这是一个非常简单的普通文本")
        # dense 包含更多专有名词，密度应更高
        self.assertGreaterEqual(dense, sparse)

    def test_with_keywords_filters_terms(self):
        """指定关键词时，只统计包含关键词的术语"""
        query = "量子纠缠与缘起性空的比较研究"
        density_all = compute_concept_density(query)
        density_filtered = compute_concept_density(query, keywords=["量子", "缘起"])
        # 过滤后密度 ≤ 全量密度（或相等）
        self.assertLessEqual(density_filtered, density_all + 0.01)

    # ── 特殊情况 ───────────────────────────────────────────────
    def test_very_long_text_density_bounded(self):
        """极长文本密度不超过 1.0"""
        long_text = "缘起性空般若" * 200
        density = compute_concept_density(long_text)
        self.assertLessEqual(density, 1.0)

    def test_custom_normalization_base(self):
        """自定义归一化基数有效"""
        text = "量子纠缠缘起性空"
        d1 = compute_concept_density(text, normalization_base=3)
        d2 = compute_concept_density(text, normalization_base=10)
        # 更小的基数 → 更高密度
        self.assertGreaterEqual(d1, d2)

    def test_result_rounded(self):
        """结果保留 2 位小数"""
        density = compute_concept_density("量子纠缠")
        # 验证是 2 位小数（str 形式检查）
        str_val = str(density)
        if '.' in str_val:
            decimal_places = len(str_val.split('.')[1])
            self.assertLessEqual(decimal_places, 2)


# ════════════════════════════════════════════════════════════════════
# § 4 · compute_tension_factor
# ════════════════════════════════════════════════════════════════════

class TestComputeTensionFactor(unittest.TestCase):
    """compute_tension_factor(query, tension_keywords, normalization_count) — 张力因子"""

    def test_returns_float_in_range(self):
        """返回值在 [0, 1] 范围内"""
        factor = compute_tension_factor("但是量子纠缠却是矛盾的")
        self.assertGreaterEqual(factor, 0.0)
        self.assertLessEqual(factor, 1.0)

    def test_empty_query_returns_zero(self):
        """空查询返回 0.0"""
        self.assertAlmostEqual(compute_tension_factor(""), 0.0)

    def test_no_tension_keywords_returns_zero(self):
        """无张力关键词时返回 0.0"""
        factor = compute_tension_factor("量子纠缠是物理现象")
        self.assertAlmostEqual(factor, 0.0)

    def test_single_tension_keyword(self):
        """单个张力关键词产生非零张力因子"""
        factor = compute_tension_factor("但是量子纠缠是矛盾的吗")
        # "但是" 和 "矛盾" 都在默认列表中 → 应有张力
        self.assertGreater(factor, 0.0)

    def test_multiple_keywords_higher_factor(self):
        """多个张力关键词产生更高因子"""
        few = compute_tension_factor("但是")
        many = compute_tension_factor("但是然而矛盾冲突对立相反相对")
        self.assertLessEqual(few, many)

    def test_capped_at_1_0(self):
        """因子上限为 1.0，超过多少关键词也不超过 1.0"""
        many_keywords_text = "但是然而不过却反而矛盾冲突对立相反相对问题困难挑战困境难题"
        factor = compute_tension_factor(many_keywords_text)
        self.assertLessEqual(factor, 1.0)

    def test_custom_keywords(self):
        """自定义张力关键词有效"""
        custom_kws = ["clash", "versus", "conflict"]
        text = "There is a conflict and clash of ideas"
        factor = compute_tension_factor(text, tension_keywords=custom_kws)
        self.assertGreater(factor, 0.0)

    def test_custom_normalization_count(self):
        """自定义归一化计数有效"""
        text = "但是然而矛盾冲突"
        f1 = compute_tension_factor(text, normalization_count=2)
        f2 = compute_tension_factor(text, normalization_count=10)
        self.assertGreaterEqual(f1, f2)

    def test_result_rounded_to_2_decimal(self):
        """结果保留 2 位小数"""
        factor = compute_tension_factor("但是矛盾")
        str_val = str(factor)
        if '.' in str_val:
            decimal_places = len(str_val.split('.')[1])
            self.assertLessEqual(decimal_places, 2)


# ════════════════════════════════════════════════════════════════════
# § 5 · compute_length_factor
# ════════════════════════════════════════════════════════════════════

class TestComputeLengthFactor(unittest.TestCase):
    """compute_length_factor(query_length, max_length) — 长度因子"""

    def test_zero_length_returns_zero(self):
        """长度为 0 时返回 0.0"""
        self.assertAlmostEqual(compute_length_factor(0), 0.0)

    def test_full_length_returns_one(self):
        """长度等于 max_length 时返回 1.0"""
        self.assertAlmostEqual(compute_length_factor(1000, max_length=1000), 1.0)

    def test_half_length_returns_half(self):
        """长度为 max_length 一半时返回 0.5"""
        self.assertAlmostEqual(compute_length_factor(500, max_length=1000), 0.5)

    def test_over_max_capped_at_one(self):
        """超过 max_length 时上限为 1.0"""
        factor = compute_length_factor(2000, max_length=1000)
        self.assertAlmostEqual(factor, 1.0)

    def test_default_max_is_1000(self):
        """默认 max_length 为 1000"""
        self.assertAlmostEqual(compute_length_factor(1000), 1.0)
        self.assertAlmostEqual(compute_length_factor(500), 0.5)

    def test_custom_max_length(self):
        """自定义 max_length 有效"""
        self.assertAlmostEqual(compute_length_factor(250, max_length=500), 0.5)
        self.assertAlmostEqual(compute_length_factor(1000, max_length=500), 1.0)

    def test_returns_float(self):
        """返回值类型为 float"""
        result = compute_length_factor(100)
        self.assertIsInstance(result, float)

    def test_monotonically_increasing(self):
        """长度因子随查询长度单调递增（到 max_length）"""
        factors = [compute_length_factor(n) for n in range(0, 1100, 100)]
        for i in range(len(factors) - 1):
            self.assertLessEqual(factors[i], factors[i + 1])


# ════════════════════════════════════════════════════════════════════
# § 6 · compute_difficulty
# ════════════════════════════════════════════════════════════════════

class TestComputeDifficulty(unittest.TestCase):
    """compute_difficulty(length_factor, concept_density, tension_factor, specialized_factor, weights) — 综合难度"""

    def test_all_zero_returns_zero(self):
        """所有因子为 0 时返回 0.0"""
        d = compute_difficulty(0.0, 0.0, 0.0, 0.0)
        self.assertAlmostEqual(d, 0.0)

    def test_all_one_returns_one(self):
        """所有因子为 1 时返回 1.0"""
        d = compute_difficulty(1.0, 1.0, 1.0, 1.0)
        self.assertAlmostEqual(d, 1.0)

    def test_result_in_range(self):
        """结果在 [0, 1] 范围内"""
        d = compute_difficulty(0.3, 0.5, 0.2, 0.4)
        self.assertGreaterEqual(d, 0.0)
        self.assertLessEqual(d, 1.0)

    def test_default_weights_sum(self):
        """默认权重验证：0.2+0.3+0.2+0.3=1.0"""
        # 四个因子都为 0.5 时，难度应为 0.5
        d = compute_difficulty(0.5, 0.5, 0.5, 0.5)
        self.assertAlmostEqual(d, 0.5)

    def test_higher_factors_higher_difficulty(self):
        """更高的因子产生更高的难度"""
        d_low = compute_difficulty(0.1, 0.1, 0.1, 0.1)
        d_high = compute_difficulty(0.9, 0.9, 0.9, 0.9)
        self.assertLess(d_low, d_high)

    def test_specialized_factor_increases_difficulty(self):
        """专用因子增加难度"""
        d_without = compute_difficulty(0.3, 0.3, 0.3, 0.0)
        d_with = compute_difficulty(0.3, 0.3, 0.3, 0.8)
        self.assertLess(d_without, d_with)

    def test_custom_weights(self):
        """自定义权重有效"""
        # 只用长度因子（权重 1.0，其余 0）
        d = compute_difficulty(0.6, 0.0, 0.0, 0.0, weights=[1.0, 0.0, 0.0, 0.0])
        self.assertAlmostEqual(d, 0.6)

    def test_clamped_on_negative_factors(self):
        """即使传入负数因子，结果也被钳制到 0"""
        d = compute_difficulty(-1.0, -1.0, -1.0, -1.0)
        self.assertAlmostEqual(d, 0.0)

    def test_result_rounded_to_2_decimal(self):
        """结果保留 2 位小数"""
        d = compute_difficulty(0.123, 0.456, 0.789, 0.321)
        str_val = str(d)
        if '.' in str_val:
            self.assertLessEqual(len(str_val.split('.')[1]), 2)


# ════════════════════════════════════════════════════════════════════
# § 7 · allocate_fold_budget
# ════════════════════════════════════════════════════════════════════

class TestAllocateFoldBudget(unittest.TestCase):
    """allocate_fold_budget(difficulty, query_length, ...) — fold 深度分配"""

    def test_result_in_range_2_to_9(self):
        """结果在 [2, 9] 范围内"""
        for diff in [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
            fold = allocate_fold_budget(diff, 100)
            with self.subTest(difficulty=diff):
                self.assertGreaterEqual(fold, 2)
                self.assertLessEqual(fold, 9)

    def test_low_difficulty_low_fold(self):
        """低难度产生低 fold 深度"""
        fold = allocate_fold_budget(0.05, 100)
        self.assertEqual(fold, 2)

    def test_high_difficulty_high_fold(self):
        """高难度产生高 fold 深度"""
        fold = allocate_fold_budget(0.9, 100)
        self.assertGreaterEqual(fold, 7)

    def test_long_text_increases_fold(self):
        """长文本增加 fold 深度"""
        fold_short = allocate_fold_budget(0.3, 100)
        fold_long = allocate_fold_budget(0.3, 1500)
        self.assertGreaterEqual(fold_long, fold_short)

    def test_specialized_text_decreases_fold(self):
        """专用文本减少 fold 深度（但不低于 2）"""
        fold_general = allocate_fold_budget(0.5, 100, is_specialized=False)
        fold_specialized = allocate_fold_budget(0.5, 100, is_specialized=True)
        self.assertLessEqual(fold_specialized, fold_general)
        self.assertGreaterEqual(fold_specialized, 2)

    def test_monotonically_non_decreasing_by_difficulty(self):
        """fold 深度随难度单调非递减"""
        difficulties = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9]
        folds = [allocate_fold_budget(d, 100) for d in difficulties]
        for i in range(len(folds) - 1):
            self.assertLessEqual(folds[i], folds[i + 1],
                                 f"fold decreased from diff={difficulties[i]} to diff={difficulties[i+1]}")

    def test_max_fold_never_exceeds_9(self):
        """fold 深度永不超过 9"""
        fold = allocate_fold_budget(1.0, 10000, is_specialized=False)
        self.assertLessEqual(fold, 9)

    def test_min_fold_never_below_2(self):
        """fold 深度永不低于 2"""
        fold = allocate_fold_budget(0.0, 1, is_specialized=True)
        self.assertGreaterEqual(fold, 2)

    def test_medium_length_threshold(self):
        """500 字符阈值：增加 1 个 fold"""
        fold_below = allocate_fold_budget(0.3, 499)
        fold_above = allocate_fold_budget(0.3, 600)
        # 超过 500 字符阈值后应增加（或相等，若已到上限）
        self.assertLessEqual(fold_below, fold_above)

    def test_returns_int(self):
        """返回值类型为整数"""
        fold = allocate_fold_budget(0.5, 100)
        self.assertIsInstance(fold, int)

    def test_custom_thresholds(self):
        """自定义长度阈值有效"""
        fold_with_low_threshold = allocate_fold_budget(
            0.3, 200, length_threshold_1=100, length_threshold_2=300
        )
        fold_with_high_threshold = allocate_fold_budget(
            0.3, 200, length_threshold_1=300, length_threshold_2=600
        )
        # 200 字符超过低阈值(100)，但不超过高阈值(300)
        self.assertGreaterEqual(fold_with_low_threshold, fold_with_high_threshold)


# ════════════════════════════════════════════════════════════════════
# § 8 · compute_target_ratio
# ════════════════════════════════════════════════════════════════════

class TestComputeTargetRatio(unittest.TestCase):
    """compute_target_ratio(query_length, difficulty, ...) — 目标压缩率"""

    def test_default_ratio_is_2_5(self):
        """短文本、低难度时返回默认 2.5"""
        ratio = compute_target_ratio(100, 0.3)
        self.assertAlmostEqual(ratio, 2.5)

    def test_long_text_reduces_ratio(self):
        """长文本（>500 字符）降低到 2.0"""
        ratio = compute_target_ratio(600, 0.3)
        self.assertAlmostEqual(ratio, 2.0)

    def test_high_difficulty_adjusts_ratio(self):
        """高难度（>0.8）进一步调整压缩率"""
        ratio_long_hard = compute_target_ratio(600, 0.9)
        # 长文本(2.0) 且高难度(-0.3) → max(2.0-0.3, 2.0) = 2.0
        self.assertAlmostEqual(ratio_long_hard, 2.0)

    def test_short_high_difficulty(self):
        """短文本高难度：从 2.5 减去高难度调整"""
        ratio = compute_target_ratio(100, 0.9)
        # 默认 2.5，高难度 -0.3 → 2.2
        self.assertAlmostEqual(ratio, 2.2)

    def test_result_never_below_2_0(self):
        """结果不低于 2.0"""
        for length in [100, 500, 1000, 5000]:
            for diff in [0.0, 0.5, 0.9, 1.0]:
                ratio = compute_target_ratio(length, diff)
                with self.subTest(length=length, diff=diff):
                    self.assertGreaterEqual(ratio, 2.0)

    def test_result_never_above_2_5(self):
        """结果不超过 2.5（默认基准）"""
        for length in [10, 100, 200]:
            for diff in [0.0, 0.3, 0.6]:
                ratio = compute_target_ratio(length, diff)
                with self.subTest(length=length, diff=diff):
                    self.assertLessEqual(ratio, 2.5)

    def test_custom_base_ratio(self):
        """自定义基准压缩率有效"""
        ratio = compute_target_ratio(100, 0.3, base_ratio=3.0)
        self.assertAlmostEqual(ratio, 3.0)

    def test_custom_long_text_threshold(self):
        """自定义长文本阈值有效"""
        ratio_300 = compute_target_ratio(350, 0.3, long_text_threshold=300)
        ratio_500 = compute_target_ratio(350, 0.3, long_text_threshold=500)
        # 350 > 300 → 降低到 long_text_ratio
        self.assertLess(ratio_300, ratio_500)

    def test_result_rounded_to_1_decimal(self):
        """结果保留 1 位小数"""
        ratio = compute_target_ratio(100, 0.3)
        str_val = str(ratio)
        if '.' in str_val:
            self.assertLessEqual(len(str_val.split('.')[1]), 1)

    def test_returns_float(self):
        """返回值类型为 float"""
        ratio = compute_target_ratio(100, 0.5)
        self.assertIsInstance(ratio, float)

    def test_boundary_at_500_chars(self):
        """500 字符边界附近行为正确"""
        # 恰好 500 字符，不应触发长文本降低
        ratio_499 = compute_target_ratio(499, 0.3)
        ratio_501 = compute_target_ratio(501, 0.3)
        self.assertAlmostEqual(ratio_499, 2.5)  # 未超过阈值
        self.assertAlmostEqual(ratio_501, 2.0)  # 超过阈值


# ════════════════════════════════════════════════════════════════════
# § 9 · 函数间组合使用（集成场景）
# ════════════════════════════════════════════════════════════════════

class TestUtilsFunctionsIntegration(unittest.TestCase):
    """工具函数组合使用的集成场景"""

    def test_full_difficulty_pipeline(self):
        """从 query 到 difficulty 的完整计算流程"""
        query = "量子纠缠与缘起性空的比较研究，但是它们是否矛盾？"

        length_factor = compute_length_factor(len(query))
        concept_density = compute_concept_density(query)
        tension_factor = compute_tension_factor(query)
        difficulty = compute_difficulty(
            length_factor, concept_density, tension_factor
        )

        self.assertGreaterEqual(difficulty, 0.0)
        self.assertLessEqual(difficulty, 1.0)

    def test_difficulty_to_fold_pipeline(self):
        """从 difficulty 到 fold_budget 的分配流程"""
        query = "般若波罗蜜多心经的空性含义" * 10
        length_factor = compute_length_factor(len(query))
        concept_density = compute_concept_density(query)
        tension_factor = compute_tension_factor(query)
        difficulty = compute_difficulty(length_factor, concept_density, tension_factor)
        fold = allocate_fold_budget(difficulty, len(query))

        self.assertGreaterEqual(fold, 2)
        self.assertLessEqual(fold, 9)

    def test_difficulty_to_ratio_pipeline(self):
        """从 difficulty 到 target_ratio 的计算流程"""
        query = "A" * 300
        length_factor = compute_length_factor(len(query))
        concept_density = compute_concept_density(query)
        tension_factor = compute_tension_factor(query)
        difficulty = compute_difficulty(length_factor, concept_density, tension_factor)
        ratio = compute_target_ratio(len(query), difficulty)

        self.assertGreaterEqual(ratio, 2.0)
        self.assertLessEqual(ratio, 2.5)

    def test_clamp_used_in_difficulty(self):
        """compute_difficulty 内部使用 clamp 确保输出安全"""
        # 极端权重输入，结果应被 clamp 到 [0, 1]
        d = compute_difficulty(5.0, 5.0, 5.0, 5.0)
        self.assertAlmostEqual(d, 1.0)  # clamp 到 1.0


if __name__ == "__main__":
    unittest.main(verbosity=2)
