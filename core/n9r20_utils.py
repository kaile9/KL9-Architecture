"""
9R-2.0 RHIZOME · 工具函数模块
─────────────────────────────
从现有模块中提取的共享工具函数，消除重复逻辑。

提取来源：
    - skills/n9r20_adaptive_router.py    → compute_concept_density, compute_tension_factor,
                                           compute_difficulty
    - core/n9r20_tension_bus.py          → compute_concept_density（重复实现）
    - skills/n9r20_compression_core.py   → 验证/计算辅助逻辑

设计原则：
    1. 纯函数，无副作用
    2. 完整的类型注解
    3. 关键词列表参数化（允许调用方传入自定义关键词）
    4. 保持与原始实现完全一致的默认行为
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple


# ════════════════════════════════════════════════════════════════════
# § 1 · clamp — 范围限制
# ════════════════════════════════════════════════════════════════════


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """
    将值限制在 [lo, hi] 闭区间内。

    参数：
        value: 输入值
        lo: 下界（含），默认 0.0
        hi: 上界（含），默认 1.0

    返回：
        钳制后的值

    示例：
        >>> clamp(1.5, 0.0, 1.0)
        1.0
        >>> clamp(-0.3, 0.0, 1.0)
        0.0
        >>> clamp(0.5)
        0.5
    """
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


# ════════════════════════════════════════════════════════════════════
# § 2 · extract_terms — 共享词项提取
# ════════════════════════════════════════════════════════════════════


def extract_terms(
    query: str,
    specialized_keywords: Optional[Tuple[str, ...]] = None,
    term_min_len: int = 2,
    term_max_len: int = 4,
) -> Tuple[List[str], List[str]]:
    """
    从查询文本中提取中文和英文术语。

    提取逻辑（与 N9R20AdaptiveRouter._compute_concept_density 一致）：
    1. 匹配中文字符的 2-4 字 n-gram
    2. 过滤：保留命中专用关键词的术语，或术语本身在关键词列表中
    3. 匹配英文 3+ 字母词（排除停用词），仅在中英混合时启用
    4. 去重保持顺序

    参数：
        query: 查询文本
        specialized_keywords: 专用文本关键词元组，用于过滤术语。
                              None 时不过滤（保留所有 2-4 字中文 n-gram）。
        term_min_len: 中文术语最小长度（字符），默认 2
        term_max_len: 中文术语最大长度（字符），默认 4

    返回：
        (chinese_terms, english_terms) — 去重的术语列表

    示例：
        >>> extract_terms("量子纠缠与缘起性空", ("量子", "缘起"))
        (['量子', '缘起'], [])
        >>> extract_terms("hello world test")
        ([], [])
        >>> extract_terms("空 and 色", ("空", "色"))
        (['空', '色'], ['and'])
    """
    # 中文术语提取（2-4 个汉字）
    all_terms: List[str] = re.findall(
        rf'[\u4e00-\u9fff]{{{term_min_len},{term_max_len}}}',
        query,
    )

    # 过滤：保留命中专用关键词的术语，或术语本身在关键词列表中
    if specialized_keywords:
        potential_terms: List[str] = []
        for term in all_terms:
            if term in specialized_keywords:
                potential_terms.append(term)
            elif any(kw in term for kw in specialized_keywords):
                potential_terms.append(term)
    else:
        potential_terms = list(all_terms)

    # 英文术语提取（仅当有中文混合时）
    english_terms: List[str] = []
    if re.search(r'[\u4e00-\u9fff]', query):
        english_words: List[str] = re.findall(r'[a-zA-Z]{3,}', query)
        _stop_words: frozenset = frozenset({
            'the', 'and', 'for', 'that', 'this', 'with', 'from',
            'what', 'how', 'are', 'you', 'was', 'were',
        })
        english_terms = [
            w.lower() for w in english_words if w.lower() not in _stop_words
        ]

    # 去重（保持顺序）
    seen: set = set()
    unique_chinese: List[str] = []
    for t in potential_terms:
        if t not in seen:
            seen.add(t)
            unique_chinese.append(t)

    seen_en: set = set()
    unique_english: List[str] = []
    for t in english_terms:
        if t not in seen_en:
            seen_en.add(t)
            unique_english.append(t)

    return unique_chinese, unique_english


# ════════════════════════════════════════════════════════════════════
# § 3 · compute_concept_density — 概念密度计算
# ════════════════════════════════════════════════════════════════════


def compute_concept_density(
    query: str,
    specialized_keywords: Optional[Tuple[str, ...]] = None,
    window: int = 5,
    min_base: int = 3,
    term_min_len: int = 2,
    term_max_len: int = 4,
) -> float:
    """
    计算查询文本的概念密度。

    公式：
        density = min(len(unique_terms) / max(len(query) / window, min_base), 1.0)

    其中：
    - unique_terms = 去重的中文术语 + 英文术语
    - window = 每 window 个字符期望 1 个术语为满密度
    - min_base = 最少术语基准（短文本保护，避免密度被高估）

    参数：
        query: 查询文本
        specialized_keywords: 专用文本关键词元组（传入以过滤术语），
                              None 时保留所有 2-4 字中文 n-gram
        window: 归一化窗口大小（字符），默认 5
        min_base: 最少术语基准，默认 3
        term_min_len: 中文术语最小长度，默认 2
        term_max_len: 中文术语最大长度，默认 4

    返回：
        概念密度 [0.0, 1.0]，保留两位小数

    示例：
        >>> compute_concept_density("量子纠缠不确定性原理", ("量子",))
        0.67
        >>> compute_concept_density("hello world")
        0.0
        >>> compute_concept_density("")
        0.0
    """
    if not query:
        return 0.0

    chinese_terms, english_terms = extract_terms(
        query,
        specialized_keywords=specialized_keywords,
        term_min_len=term_min_len,
        term_max_len=term_max_len,
    )
    unique_terms = chinese_terms + english_terms

    if not unique_terms:
        return 0.0

    normalized_length = max(len(query) / window, min_base)
    density = min(len(unique_terms) / normalized_length, 1.0)

    return round(density, 2)


# ════════════════════════════════════════════════════════════════════
# § 4 · compute_tension_factor — 张力因子计算
# ════════════════════════════════════════════════════════════════════


def compute_tension_factor(
    query: str,
    tension_keywords: Optional[Tuple[str, ...]] = None,
    normalizer: int = 5,
) -> float:
    """
    检测查询文本中的张力关键词并计算张力因子。

    张力关键词：对立、矛盾、冲突、疑问词等表示结构性张力的词语。

    公式：
        tension_factor = min(tension_count / normalizer, 1.0)

    参数：
        query: 查询文本
        tension_keywords: 张力关键词元组，None 时使用内置默认列表
        normalizer: 归一化分母（达到此数量 = 满张力），默认 5

    返回：
        张力因子 [0.0, 1.0]，保留两位小数

    示例：
        >>> compute_tension_factor("但是这里有一个矛盾的问题")
        0.4
        >>> compute_tension_factor("这是简单的描述")
        0.0
        >>> compute_tension_factor("但是矛盾冲突为什么如何")
        1.0
    """
    if tension_keywords is None:
        tension_keywords = (
            "但是", "然而", "不过", "却", "反而",
            "矛盾", "冲突", "对立", "相反", "相对",
            "問題", "困難", "挑戰", "困境", "難題",
            "為什麼", "如何", "怎麼", "什麼", "是否",
            "能否", "可否", "難道", "豈非",
        )

    if not query:
        return 0.0

    tension_count = sum(1 for kw in tension_keywords if kw in query)
    tension_factor = min(tension_count / normalizer, 1.0)

    return round(tension_factor, 2)


# ════════════════════════════════════════════════════════════════════
# § 5 · compute_difficulty — 难度计算
# ════════════════════════════════════════════════════════════════════


def compute_difficulty(
    query: str,
    specialized_keywords: Optional[Tuple[str, ...]] = None,
    tension_keywords: Optional[Tuple[str, ...]] = None,
    length_divisor: int = 200,
    length_weight: float = 0.2,
    concept_weight: float = 0.3,
    tension_weight: float = 0.2,
    specialized_weight: float = 0.3,
    specialized_bonus: float = 0.3,
    specialized_threshold: float = 0.2,
) -> float:
    """
    评估任务难度（0-1 连续谱）。

    影响因素：
    1. 长度因子：长文本通常更复杂
    2. 概念密度因子：术语数量 / 总字数
    3. 张力因子：是否包含对立概念
    4. 专用文本加成：专用文本通常更难

    公式：
        difficulty = length_factor * length_weight
                   + concept_density * concept_weight
                   + tension_factor * tension_weight
                   + specialized_factor * specialized_weight

    参数：
        query: 查询文本
        specialized_keywords: 专用文本关键词（用于概念密度 + 专用检测）
        tension_keywords: 张力关键词（用于张力因子）
        length_divisor: 长度因子归一化除数，默认 200
        length_weight: 长度因子权重，默认 0.2
        concept_weight: 概念密度权重，默认 0.3
        tension_weight: 张力因子权重，默认 0.2
        specialized_weight: 专用文本权重，默认 0.3
        specialized_bonus: 专用文本难度加成，默认 0.3
        specialized_threshold: 专用文本判定阈值，默认 0.2

    返回：
        难度 [0.0, 1.0]，保留两位小数

    示例：
        >>> compute_difficulty("你好")
        0.07
        >>> compute_difficulty("量子纠缠与缘起性空的比较研究" * 10)
        0.48
    """
    # 1. 长度因子
    length_factor = clamp(len(query) / length_divisor, 0.0, 1.0)

    # 2. 概念密度因子
    concept_density = compute_concept_density(
        query, specialized_keywords=specialized_keywords
    )

    # 3. 张力因子
    tension_factor = compute_tension_factor(
        query, tension_keywords=tension_keywords
    )

    # 4. 专用文本检测
    is_specialized = _is_specialized_text(
        query,
        specialized_keywords=specialized_keywords,
        tension_keywords=tension_keywords,
        threshold=specialized_threshold,
    )
    specialized_factor_val = specialized_bonus if is_specialized else 0.0

    # 综合难度
    difficulty = (
        length_factor * length_weight
        + concept_density * concept_weight
        + tension_factor * tension_weight
        + specialized_factor_val * specialized_weight
    )

    return round(clamp(difficulty, 0.0, 1.0), 2)


# ════════════════════════════════════════════════════════════════════
# § 6 · _is_specialized_text — 专用文本判定（内部）
# ════════════════════════════════════════════════════════════════════


def _is_specialized_text(
    query: str,
    specialized_keywords: Optional[Tuple[str, ...]] = None,
    tension_keywords: Optional[Tuple[str, ...]] = None,
    keyword_weight: float = 0.5,
    density_weight: float = 0.3,
    tension_weight_val: float = 0.2,
    threshold: float = 0.2,
) -> bool:
    """
    判定查询是否为专用文本（内部辅助函数）。

    参数：
        query: 查询文本
        specialized_keywords: 专用关键词元组
        tension_keywords: 张力关键词元组
        keyword_weight: 关键词置信度权重
        density_weight: 概念密度权重
        tension_weight_val: 张力权重
        threshold: 判定阈值

    返回：
        True 如果综合置信度 > threshold
    """
    if specialized_keywords is None:
        specialized_keywords = (
            "空", "識", "识", "緣起", "缘起", "中道", "般若",
            "如來", "如来", "菩薩", "菩萨", "涅槃", "因果",
            "存在", "本质", "辯證", "辩证",
            "量子", "涌现",
        )

    keyword_count = sum(1 for kw in specialized_keywords if kw in query)
    keyword_score = min(keyword_count / 1.0, 1.0)

    concept_density = compute_concept_density(
        query, specialized_keywords=specialized_keywords
    )

    tension_factor = compute_tension_factor(
        query, tension_keywords=tension_keywords
    )

    confidence = (
        keyword_score * keyword_weight
        + concept_density * density_weight
        + tension_factor * tension_weight_val
    )

    return confidence > threshold


# ════════════════════════════════════════════════════════════════════
# § 7 · compute_length_factor — 长度因子
# ════════════════════════════════════════════════════════════════════


def compute_length_factor(query: str, cap: float = 1000.0) -> float:
    """
    计算文本长度因子 [0.0, 1.0]。

    公式：
        length_factor = min(len(query) / cap, 1.0)

    参数：
        query: 查询文本
        cap: 归一化除数（达到此长度 = 1.0），默认 1000.0

    返回：
        长度因子 [0.0, 1.0]

    示例：
        >>> compute_length_factor("hello")
        0.005
        >>> compute_length_factor("A" * 500)
        0.5
    """
    return round(clamp(len(query) / cap, 0.0, 1.0), 2)


# ════════════════════════════════════════════════════════════════════
# § 8 · allocate_fold_budget — fold 预算分配
# ════════════════════════════════════════════════════════════════════


def allocate_fold_budget(
    query_length: int,
    difficulty: float,
    is_specialized: bool = False,
    fold_by_difficulty: Optional[Tuple[Tuple[float, int], ...]] = None,
    fold_min: int = 2,
    fold_max: int = 9,
    long_threshold_1: int = 500,
    long_bonus_1: int = 1,
    long_threshold_2: int = 1000,
    long_bonus_2: int = 2,
    specialized_penalty: int = 1,
) -> int:
    """
    动态分配 fold 深度。

    难度 → fold 映射（来自 N9R20RoutingConfig.fold_by_difficulty）。

    调整因素：
    - 长文本：增加 fold（上限 fold_max）
    - 专用文本：减少 fold（下限 fold_min，压缩更高效）

    参数：
        query_length: 查询文本长度
        difficulty: 任务难度 [0.0, 1.0]
        is_specialized: 是否为专用文本
        fold_by_difficulty: (difficulty_threshold, fold) 元组列表
        fold_min: fold 下界
        fold_max: fold 上界
        long_threshold_1: 长文本第一阈值
        long_bonus_1: 长文本第一加成
        long_threshold_2: 长文本第二阈值
        long_bonus_2: 长文本第二加成
        specialized_penalty: 专用文本 fold 减少量

    返回：
        分配的 fold 深度 [fold_min, fold_max]
    """
    if fold_by_difficulty is None:
        fold_by_difficulty = (
            (0.1, 2), (0.2, 3), (0.3, 4), (0.4, 5),
            (0.5, 6), (0.6, 7), (0.7, 8), (1.0, 9),
        )

    # 难度 → fold
    base_fold = fold_min
    for threshold, fold_val in fold_by_difficulty:
        if difficulty < threshold:
            base_fold = fold_val
            break
    else:
        base_fold = fold_max

    # 长文本加成
    if query_length > long_threshold_2:
        base_fold = min(base_fold + long_bonus_2, fold_max)
    elif query_length > long_threshold_1:
        base_fold = min(base_fold + long_bonus_1, fold_max)

    # 专用文本惩罚
    if is_specialized:
        base_fold = max(base_fold - specialized_penalty, fold_min)

    return base_fold


# ════════════════════════════════════════════════════════════════════
# § 9 · compute_target_ratio — 目标压缩率
# ════════════════════════════════════════════════════════════════════


def compute_target_ratio(
    query_length: int,
    difficulty: float,
    base_ratio: float = 2.5,
    long_threshold: int = 500,
    long_target: float = 2.0,
    high_difficulty_threshold: float = 0.8,
    high_difficulty_reduction: float = 0.3,
    ratio_min: float = 2.0,
    ratio_max: float = 2.5,
) -> float:
    """
    动态计算目标压缩率。

    策略：
    - 基准：base_ratio（默认 2.5）
    - 长文本（> long_threshold）：降至 long_target
    - 高难度（> high_difficulty_threshold）：降低 high_difficulty_reduction

    参数：
        query_length: 查询文本长度
        difficulty: 任务难度
        base_ratio: 基准压缩率
        long_threshold: 长文本阈值
        long_target: 长文本目标压缩率
        high_difficulty_threshold: 高难度阈值
        high_difficulty_reduction: 高难度压缩率降低量
        ratio_min: 压缩率下界
        ratio_max: 压缩率上界

    返回：
        目标压缩率 [ratio_min, ratio_max]
    """
    ratio = base_ratio

    if query_length > long_threshold:
        ratio = long_target

    if difficulty > high_difficulty_threshold:
        ratio = max(ratio - high_difficulty_reduction, ratio_min)

    return round(clamp(ratio, ratio_min, ratio_max), 1)


__all__ = [
    "clamp",
    "extract_terms",
    "compute_concept_density",
    "compute_tension_factor",
    "compute_difficulty",
    "compute_length_factor",
    "allocate_fold_budget",
    "compute_target_ratio",
]
