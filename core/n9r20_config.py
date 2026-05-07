"""
9R-2.0 RHIZOME · 配置常量模块
──────────────────────────────
从现有模块中提取所有可调配置参数为独立数据类。

设计原则：
    1. 所有默认值保持与现有代码完全一致（向后兼容）
    2. 使用 frozen dataclass 确保不可变性
    3. 每个配置类只包含相关参数
    4. 提供模块级单例作为全局默认配置源

涉及模块（默认值来源）：
    - N9R20AdaptiveRouter     → 路由阈值 / 关键词列表
    - N9R20CompressionCore    → 压缩参数
    - N9R20MemoryLearner      → 记忆 / 遗忘参数
    - n9r20_semantic_graph    → 语义图参数
    - N9R20PersonaConfig      → 张力检测阈值
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ════════════════════════════════════════════════════════════════════
# § 1 · 路由配置
# ════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class N9R20RoutingConfig:
    """
    自适应路由器的配置常量。

    默认值来源：skills/n9r20_adaptive_router.py — N9R20AdaptiveRouter

    属性：
        specialized_keywords: 专用文本关键词（精简核心集，15-20 个）
        tension_keywords: 张力检测关键词列表
        fold_depth_min: fold 深度下界（含）
        fold_depth_max: fold 深度上界（含）
        fold_by_difficulty: 难度 → fold 映射阈值
        base_compression_ratio: 基准压缩率
        concept_density_window: 概念密度滑动窗口（字符数）
        concept_density_min_base: 概念密度归一化最小基准
        length_factor_cap: 长度因子归一化除数（字符数）
        keyword_confidence_weight: 关键词在置信度中的权重
        concept_density_weight: 概念密度在置信度中的权重
        tension_weight: 张力在置信度中的权重
        specialized_threshold: 判定为专用文本的置信度阈值
        difficulty_length_divisor: 难度评估长度因子除数
        difficulty_length_weight: 难度评估长度权重
        difficulty_concept_weight: 难度评估概念密度权重
        difficulty_tension_weight: 难度评估张力权重
        difficulty_specialized_weight: 难度评估专用文本权重
        specialized_bonus: 专用文本难度加成
        urgency_difficulty_weight: 紧急度中难度权重
        urgency_long_text_thresholds: 长文本紧急度加成（字符数→加成值）
        tension_normalizer: 张力因子归一化分母
        length_factor_max: 长度因子最大值除数
        ratio_long_threshold: 长文本压缩率调整阈值
        ratio_long_target: 长文本目标压缩率
        ratio_high_difficulty_threshold: 高难度压缩率调整阈值
        ratio_high_difficulty_reduction: 高难度压缩率降低量
        ratio_min: 压缩率绝对下界
        ratio_max: 压缩率绝对上界
    """

    # ── 路由关键词 ───────────────────────────────────────────────
    specialized_keywords: Tuple[str, ...] = (
        "空", "識", "识", "緣起", "缘起", "中道", "般若",
        "如來", "如来", "菩薩", "菩萨", "涅槃", "因果",
        "存在", "本质", "辯證", "辩证",
        "量子", "涌现",
    )

    tension_keywords: Tuple[str, ...] = (
        "但是", "然而", "不过", "却", "反而",
        "矛盾", "冲突", "对立", "相反", "相对",
        "問題", "困難", "挑戰", "困境", "難題",
        "為什麼", "如何", "怎麼", "什麼", "是否",
        "能否", "可否", "難道", "豈非",
    )

    # ── fold 预算参数 ────────────────────────────────────────────
    fold_depth_min: int = 2
    fold_depth_max: int = 9
    fold_by_difficulty: Tuple[Tuple[float, int], ...] = (
        (0.1, 2),
        (0.2, 3),
        (0.3, 4),
        (0.4, 5),
        (0.5, 6),
        (0.6, 7),
        (0.7, 8),
        (1.0, 9),
    )
    fold_long_text_threshold_1: int = 500
    fold_long_text_bonus_1: int = 1
    fold_long_text_threshold_2: int = 1000
    fold_long_text_bonus_2: int = 2
    fold_specialized_penalty: int = 1

    # ── 压缩率参数 ────────────────────────────────────────────────
    base_compression_ratio: float = 2.5
    ratio_long_threshold: int = 500
    ratio_long_target: float = 2.0
    ratio_high_difficulty_threshold: float = 0.8
    ratio_high_difficulty_reduction: float = 0.3
    ratio_min: float = 2.0
    ratio_max: float = 2.5

    # ── 概念密度参数 ─────────────────────────────────────────────
    concept_density_window: int = 5
    concept_density_min_base: int = 3

    # ── 置信度权重 ───────────────────────────────────────────────
    keyword_confidence_weight: float = 0.5
    concept_density_weight: float = 0.3
    tension_weight: float = 0.2
    specialized_threshold: float = 0.2

    # ── 难度评估权重 ─────────────────────────────────────────────
    difficulty_length_divisor: int = 200
    difficulty_length_weight: float = 0.2
    difficulty_concept_weight: float = 0.3
    difficulty_tension_weight: float = 0.2
    difficulty_specialized_weight: float = 0.3
    specialized_bonus: float = 0.3

    # ── 紧急度参数 ───────────────────────────────────────────────
    urgency_difficulty_weight: float = 0.6
    urgency_long_text_thresholds: Tuple[Tuple[int, float], ...] = (
        (2000, 0.4),
        (1000, 0.2),
        (500, 0.1),
    )

    # ── 张力度量参数 ─────────────────────────────────────────────
    tension_normalizer: int = 5
    length_factor_max: float = 1000.0


# ════════════════════════════════════════════════════════════════════
# § 2 · 压缩配置
# ════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class N9R20CompressionConfig:
    """
    压缩核心引擎的配置常量。

    属性（新命名，全大写）：
        SEMANTIC_RETENTION_THRESHOLD: 语义保留率通过阈值
        FOLD_DEPTH_PENALTY_PER_LEVEL: 每层 fold 的保留率惩罚
        VALIDATOR_ESTIMATION_DIVISOR: 保留率估算分母系数
        SIMPLE_COMPRESS_RATIO: 简单压缩保留比例
        MODE_SIMPLE_DIFFICULTY_THRESHOLD: 简单模式难度阈值
        MODE_MEDIUM_DIFFICULTY_THRESHOLD: 中等模式难度阈值
        MODE_SEQUENCE_SIMPLE/MEDIUM/HARD: 模式序列

    向后兼容属性（通过 @property 暴露）：
        retention_pass_threshold, fold_depth_retention_penalty,
        retention_estimation_denom, simple_compress_ratio,
        mode_simple_threshold, mode_hard_threshold
    """

    default_target_fold_depth: int = 4
    default_target_compression_ratio: float = 2.5
    SEMANTIC_RETENTION_THRESHOLD: float = 0.85
    FOLD_DEPTH_PENALTY_PER_LEVEL: float = 0.02
    VALIDATOR_ESTIMATION_DIVISOR: float = 0.5
    SIMPLE_COMPRESS_RATIO: float = 0.6

    MODE_SIMPLE_DIFFICULTY_THRESHOLD: float = 0.3
    MODE_MEDIUM_DIFFICULTY_THRESHOLD: float = 0.7
    MODE_SEQUENCE_SIMPLE: Tuple[str, ...] = ("construct", "interrupt")
    MODE_SEQUENCE_MEDIUM: Tuple[str, ...] = ("construct", "deconstruct", "interrupt")
    MODE_SEQUENCE_HARD: Tuple[str, ...] = ("construct", "deconstruct", "validate", "interrupt")

    # ── 向后兼容属性 ──
    @property
    def retention_pass_threshold(self) -> float:
        return self.SEMANTIC_RETENTION_THRESHOLD

    @property
    def fold_depth_retention_penalty(self) -> float:
        return self.FOLD_DEPTH_PENALTY_PER_LEVEL

    @property
    def retention_estimation_denom(self) -> float:
        return self.VALIDATOR_ESTIMATION_DIVISOR

    @property
    def simple_compress_ratio(self) -> float:
        return self.SIMPLE_COMPRESS_RATIO

    @property
    def mode_simple_threshold(self) -> float:
        return self.MODE_SIMPLE_DIFFICULTY_THRESHOLD

    @property
    def mode_hard_threshold(self) -> float:
        return self.MODE_MEDIUM_DIFFICULTY_THRESHOLD


# ════════════════════════════════════════════════════════════════════
# § 3 · 记忆 / 遗忘配置
# ════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class N9R20MemoryConfig:
    """
    记忆学习器的配置常量。

    属性（UPPERCASE，供父项目引用）：
        MAX_MEMORIES, FORGET_HALFLIFE, FORGET_THRESHOLD,
        PROPAGATION_RATE, PROPAGATION_THRESHOLD, PROPAGATION_MIN_CALLS,
        PROPAGATION_PERIOD, FORGET_PERIOD,
        QUERY_PREVIEW_MAX_CHARS,
        SKILL_SCORE_WEIGHT_RETENTION/SUCCESS/COMPRESSION,
        RECOMMEND_WEIGHT_RETENTION/SUCCESS/COMPRESSION,
        RECOMMEND_MIN_CALLS, RECOMMEND_RECENCY_WINDOW, RECOMMEND_RECENCY_FACTOR,
        CORE_SKILLS.
    """

    MAX_MEMORIES: int = 1000
    FORGET_HALFLIFE: float = 86400.0
    FORGET_THRESHOLD: float = 0.1
    PROPAGATION_RATE: float = 0.1
    PROPAGATION_THRESHOLD: float = 0.15
    PROPAGATION_MIN_CALLS: int = 3
    PROPAGATION_PERIOD: int = 10
    FORGET_PERIOD: int = 50
    QUERY_PREVIEW_MAX_CHARS: int = 100

    SKILL_SCORE_WEIGHT_RETENTION: float = 0.5
    SKILL_SCORE_WEIGHT_SUCCESS: float = 0.3
    SKILL_SCORE_WEIGHT_COMPRESSION: float = 0.2

    RECOMMEND_WEIGHT_RETENTION: float = 0.4
    RECOMMEND_WEIGHT_SUCCESS: float = 0.3
    RECOMMEND_WEIGHT_COMPRESSION: float = 0.3
    RECOMMEND_MIN_CALLS: int = 2
    RECOMMEND_RECENCY_WINDOW: float = 3600.0
    RECOMMEND_RECENCY_FACTOR: float = 0.1

    CORE_SKILLS: Tuple[str, ...] = (
        "compression-core",
        "dual-reasoner",
        "semantic-graph",
        "memory-learner",
        "adaptive-n9r20_router",
    )

    # ── 向后兼容属性 ──
    @property
    def max_memories(self) -> int:
        return self.MAX_MEMORIES

    @property
    def forget_halflife(self) -> float:
        return self.FORGET_HALFLIFE

    @property
    def propagation_rate(self) -> float:
        return self.PROPAGATION_RATE

    @property
    def propagation_threshold(self) -> float:
        return self.PROPAGATION_THRESHOLD

    @property
    def propagation_min_samples(self) -> int:
        return self.PROPAGATION_MIN_CALLS

    @property
    def forget_return_threshold(self) -> float:
        return self.FORGET_THRESHOLD

    @property
    def propagation_frequency(self) -> int:
        return self.PROPAGATION_PERIOD

    @property
    def forget_frequency(self) -> int:
        return self.FORGET_PERIOD

    @property
    def memory_preview_max_chars(self) -> int:
        return self.QUERY_PREVIEW_MAX_CHARS

    @property
    def core_skills(self) -> Tuple[str, ...]:
        return self.CORE_SKILLS

    @property
    def skill_score_retention_weight(self) -> float:
        return self.SKILL_SCORE_WEIGHT_RETENTION

    @property
    def skill_score_success_weight(self) -> float:
        return self.SKILL_SCORE_WEIGHT_SUCCESS

    @property
    def skill_score_compression_weight(self) -> float:
        return self.SKILL_SCORE_WEIGHT_COMPRESSION

    @property
    def recommend_history_retention_weight(self) -> float:
        return self.RECOMMEND_WEIGHT_RETENTION

    @property
    def recommend_history_success_weight(self) -> float:
        return self.RECOMMEND_WEIGHT_SUCCESS

    @property
    def recommend_history_compression_weight(self) -> float:
        return self.RECOMMEND_WEIGHT_COMPRESSION

    @property
    def recommend_min_samples_for_score(self) -> int:
        return self.RECOMMEND_MIN_CALLS

    @property
    def recommend_recency_hours(self) -> float:
        return self.RECOMMEND_RECENCY_WINDOW

    @property
    def recommend_recency_weight(self) -> float:
        return self.RECOMMEND_RECENCY_FACTOR

    @property
    def recommend_default_score(self) -> float:
        return 0.5


# ════════════════════════════════════════════════════════════════════
# § 4 · 语义图配置
# ════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class N9R20SemanticGraphConfig:
    """
    语义图的配置常量。

    属性：
        EDGE_DECAY_HALFLIFE: 边权重衰减半衰期（秒）
        EDGE_PRUNE_THRESHOLD: 边剪枝阈值（低于此权重移除）
        EDGE_REINFORCE_INCREMENT: 边强化增量
        EDGE_INITIAL_WEIGHT: 新边初始权重
        EDGE_NEIGHBOR_MIN_WEIGHT: 邻居边最小权重
        TERM_CONFIDENCE_DEFAULT: 新术语默认置信度
        TERM_CONFIDENCE_INCREMENT: 术语置信度增量
        PATH_MAX_DEPTH: 路径搜索最大深度
        CLUSTER_MIN_SIZE: 聚类最小尺寸
        CLUSTER_MAX_ITERATIONS: 聚类最大迭代次数
        CLUSTER_TENSION_THRESHOLD: 聚类间张力阈值
        CLUSTER_ISOLATED_TENSION: 孤立节点默认张力
        COOCCURRENCE_WINDOW_SIZE: 共现窗口大小
        EVENT_TERM_COUNT_THRESHOLD: 事件触发术语数阈值
        EVENT_CLUSTER_COUNT_THRESHOLD: 事件触发聚类数阈值
        PRUNE_PERIOD: 剪枝周期（每 N 个 session）
    """

    EDGE_DECAY_HALFLIFE: float = 3600.0
    EDGE_PRUNE_THRESHOLD: float = 0.05
    EDGE_REINFORCE_INCREMENT: float = 0.1
    EDGE_INITIAL_WEIGHT: float = 0.3
    EDGE_NEIGHBOR_MIN_WEIGHT: float = 0.1
    TERM_CONFIDENCE_DEFAULT: float = 0.7
    TERM_CONFIDENCE_INCREMENT: float = 0.05
    PATH_MAX_DEPTH: int = 5
    CLUSTER_MIN_SIZE: int = 3
    CLUSTER_MAX_ITERATIONS: int = 20
    CLUSTER_TENSION_THRESHOLD: float = 0.4
    CLUSTER_ISOLATED_TENSION: float = 0.2
    COOCCURRENCE_WINDOW_SIZE: int = 10
    EVENT_TERM_COUNT_THRESHOLD: int = 5
    EVENT_CLUSTER_COUNT_THRESHOLD: int = 2
    PRUNE_PERIOD: int = 50

    # ── 向后兼容属性 ──
    term_min_len: int = 2
    term_max_len: int = 4
    default_confidence: float = 0.7
    edge_decay_rate: float = 0.01
    min_edge_weight: float = 0.05
    max_edges_per_node: int = 20
    clustering_similarity_threshold: float = 0.6


# ════════════════════════════════════════════════════════════════════
# § 5 · 张力检测配置
# ════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class N9R20TensionConfig:
    """
    张力类型系统的内置常量。

    支持运行时动态注册新张力类型，此处仅定义内置类型。

    属性：
        BUILTIN_TENSION_TYPES: 内置张力类型元组
        DEFAULT_TENSION_TYPE: 默认张力类型
        DEFAULT_INTENSITY: 默认张力强度
        DEFAULT_TENSION_KEYWORDS: 通用张力检测关键词
        DEFAULT_SPECIALIZED_KEYWORDS: 专用文本关键词（精简核心集）
        ENGLISH_STOP_WORDS: 英文停用词元组
        quick_routing_threshold: 快速路由字符阈值（含边界）
        academic_markers: 学术关键词表（触发 DEEP 层的依据，命中 ≥2 触发）
        routing_tiers: 路由层级定义（tier → fold_depth 范围）
        fallback_confidence: FALLBACK 决策置信度
        fallback_urgency: FALLBACK 决策紧急度
        fallback_difficulty: FALLBACK 决策难度
        urgency_high_threshold: 高紧急度阈值（仅核心技能）
        urgency_medium_threshold: 中紧急度阈值（核心+专用）
        is_specialized_keywords: fallback_route 专用文本关键词
        is_specialized_keyword_weight: fallback_route 关键词权重
        is_specialized_density_weight: fallback_route 概念密度权重
        is_specialized_threshold: fallback_route 专用判定阈值
        deep_academic_min_count: 触发 DEEP 层所需最小学术标记数
    """

    # ── 内置张力类型 ─────────────────────────────────────────
    BUILTIN_TENSION_TYPES: Tuple[str, ...] = (
        "epistemic",
        "dialectical",
        "temporal",
        "existential",
        "aesthetic",
        "ethical",
        "semantic",
    )

    # ── 默认张力参数 ─────────────────────────────────────────
    DEFAULT_TENSION_TYPE: str = "semantic"
    DEFAULT_INTENSITY: float = 0.5

    # ── 张力关键词（通用检测用） ─────────────────────────────
    DEFAULT_TENSION_KEYWORDS: Tuple[str, ...] = (
        "但是", "然而", "不过", "却", "反而",
        "矛盾", "冲突", "对立", "相反", "相对",
        "問題", "困難", "挑戰", "困境", "難題",
        "问题", "困难", "挑战", "困境", "难题",
        "為什麼", "如何", "怎麼", "什麼", "是否",
        "为什么", "怎么", "什么",
        "能否", "可否", "難道", "岂非",
    )

    # ── 专用文本关键词（精简核心集） ─────────────────────────
    DEFAULT_SPECIALIZED_KEYWORDS: Tuple[str, ...] = (
        "空", "識", "识", "緣起", "缘起", "中道", "般若",
        "如來", "如来", "菩薩", "菩萨", "涅槃", "因果",
        "存在", "本质", "辯證", "辩证",
        "量子", "涌现",
    )

    # ── 英文停用词 ───────────────────────────────────────────
    ENGLISH_STOP_WORDS: Tuple[str, ...] = (
        "the", "and", "for", "that", "this",
        "with", "from", "what", "how", "are",
        "you", "was", "were",
    )

    # ── 路由层级与阈值（来自 persona 人设系统） ─────────────
    quick_routing_threshold: int = 25

    academic_markers: Tuple[str, ...] = (
        "认识论", "本体论", "现象学", "存在主义", "辩证法", "形而上学",
        "逻辑学", "伦理学", "美学", "诠释学", "结构主义", "解构主义",
        "般若", "空性", "缘起", "涅槃", "唯识", "如来藏", "中观", "菩提",
        "量子", "拓扑", "范畴论", "函子", "涌现", "熵", "复杂性",
        "符号学", "语义学", "现象场", "主体性", "他者性", "间性",
    )

    routing_tiers: Tuple[Tuple[str, int, int], ...] = (
        ("QUICK",    0, 0),
        ("STANDARD", 1, 3),
        ("DEEP",     3, 6),
        ("FALLBACK", 1, 2),
    )

    fallback_confidence: float = 0.0
    fallback_urgency: float = 0.3
    fallback_difficulty: float = 0.3

    urgency_high_threshold: float = 0.8
    urgency_medium_threshold: float = 0.5

    is_specialized_keywords: Tuple[str, ...] = (
        "空", "識", "緣起", "中道", "般若", "唯識", "禪",
        "如來", "菩薩", "涅槃", "輪迴", "業", "因果",
        "量子", "熵", "涌现", "拓扑", "范畴", "函子",
        "存在", "虚无", "自由", "必然", "偶然",
    )

    is_specialized_keyword_weight: float = 0.4
    is_specialized_density_weight: float = 0.6
    is_specialized_threshold: float = 0.3

    deep_academic_min_count: int = 2


# ════════════════════════════════════════════════════════════════════
# § 6 · 全局单例
# ════════════════════════════════════════════════════════════════════

#: 全局路由配置单例
n9r20_routing_config: N9R20RoutingConfig = N9R20RoutingConfig()

#: 全局压缩配置单例
n9r20_compression_config: N9R20CompressionConfig = N9R20CompressionConfig()

#: 全局记忆配置单例
n9r20_memory_config: N9R20MemoryConfig = N9R20MemoryConfig()

#: 全局语义图配置单例
n9r20_semantic_graph_config: N9R20SemanticGraphConfig = N9R20SemanticGraphConfig()

#: 全局张力检测配置单例
n9r20_tension_config: N9R20TensionConfig = N9R20TensionConfig()


__all__ = [
    "N9R20RoutingConfig",
    "N9R20CompressionConfig",
    "N9R20MemoryConfig",
    "N9R20SemanticGraphConfig",
    "N9R20TensionConfig",
    "n9r20_routing_config",
    "n9r20_compression_config",
    "n9r20_memory_config",
    "n9r20_semantic_graph_config",
    "n9r20_tension_config",
]
