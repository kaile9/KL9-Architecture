"""
9R-2.0 RHIZOME · 配置常量
────────────────────────────────────────────────────────
消除系统中所有魔法数字，统一管理配置参数。

每个配置类对应一个子系统：
  N9R20RoutingConfig      — 路由与 fold 深度分配
  N9R20CompressionConfig  — 压缩率、保留率与验证
  N9R20MemoryConfig       — 记忆存储与遗忘
  N9R20SemanticGraphConfig— 语义图谱边衰减与剪枝
  N9R20TensionConfig      — 张力类型内置列表

使用方式：
  from core.n9r20_config import N9R20RoutingConfig
  min_fold = N9R20RoutingConfig.FOLD_DEPTH_MIN
"""

from dataclasses import dataclass, field
from typing import List, Tuple


# ════════════════════════════════════════════════════════════════════
# § 1 · 路由配置
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class N9R20RoutingConfig:
    """
    路由与 fold 深度分配的所有常量。

    涵盖自适应路由器（N9R20AdaptiveRouter）和
    LLM 评估器（N9R20LLMFoldEvaluator）中所有硬编码阈值。
    """

    # ── Fold 深度范围 ──────────────────────────────────────────
    FOLD_DEPTH_MIN: int = 2
    FOLD_DEPTH_MAX: int = 9
    FOLD_DEPTH_DEFAULT: int = 4

    # ── 压缩率范围 ─────────────────────────────────────────────
    COMPRESSION_RATIO_MIN: float = 2.0
    COMPRESSION_RATIO_MAX: float = 2.5
    COMPRESSION_RATIO_DEFAULT: float = 2.5

    # ── 难度阈值（用于 fold 深度分配） ─────────────────────────
    DIFFICULTY_THRESHOLDS: Tuple[Tuple[float, int], ...] = (
        (0.1, 2),
        (0.2, 3),
        (0.3, 4),
        (0.4, 5),
        (0.5, 6),
        (0.6, 7),
        (0.7, 8),
        (1.0, 9),
    )

    # ── 长度因子 ───────────────────────────────────────────────
    LENGTH_MAX_CHARS: int = 1000
    LENGTH_MEDIUM_CHARS: int = 500
    LENGTH_LONG_CHARS: int = 2000
    CHARS_PER_TERM: int = 5
    TERM_BASELINE_MIN: int = 3
    CHARS_FULL_LENGTH: int = 100
    CHARS_MEDIUM_THRESHOLD: int = 200

    # ── 张力因子 ───────────────────────────────────────────────
    TENSION_MAX_KEYWORDS: int = 5
    TENSION_FALLBACK_MAX: int = 3

    # ── 难度综合权重 ──────────────────────────────────────────
    DIFFICULTY_WEIGHT_LENGTH: float = 0.2
    DIFFICULTY_WEIGHT_CONCEPT: float = 0.3
    DIFFICULTY_WEIGHT_TENSION: float = 0.2
    DIFFICULTY_WEIGHT_SPECIALIZED: float = 0.3
    FALLBACK_WEIGHT_LENGTH: float = 0.3
    FALLBACK_WEIGHT_CONCEPT: float = 0.4
    FALLBACK_WEIGHT_TENSION: float = 0.3

    # ── 专用文本检测 ──────────────────────────────────────────
    SPECIALIZED_CONFIDENCE_THRESHOLD: float = 0.2
    SPECIALIZED_KEYWORD_HIT_BASELINE: float = 1.0
    SPECIALIZED_WEIGHT_KEYWORD: float = 0.5
    SPECIALIZED_WEIGHT_CONCEPT: float = 0.3
    SPECIALIZED_WEIGHT_TENSION: float = 0.2

    # ── 紧急度 ────────────────────────────────────────────────
    URGENCY_DIFFICULTY_WEIGHT: float = 0.6
    URGENCY_LONG_BONUS: float = 0.4
    URGENCY_MEDIUM_BONUS: float = 0.2
    URGENCY_SHORT_BONUS: float = 0.1
    URGENCY_HIGH_THRESHOLD: float = 0.8
    URGENCY_MEDIUM_THRESHOLD: float = 0.5

    # ── 压缩率动态调整 ────────────────────────────────────────
    COMPRESSION_LONG_TEXT_RATIO: float = 2.0
    COMPRESSION_HIGH_DIFFICULTY_DELTA: float = 0.3
    COMPRESSION_HIGH_DIFFICULTY_THRESHOLD: float = 0.8

    # ── Fold 调整 ─────────────────────────────────────────────
    FOLD_LONG_TEXT_BONUS: int = 2
    FOLD_MEDIUM_TEXT_BONUS: int = 1
    FOLD_SPECIALIZED_PENALTY: int = 1

    # ── LLM 评估器备用置信度 ─────────────────────────────────
    LLM_FALLBACK_CONFIDENCE: float = 0.6
    
    # ── 用户可配置的学术标记（默认空，由 SkillBook 填充） ─────────────────
    ACADEMIC_MARKERS: List[str] = field(default_factory=list)
    ACADEMIC_MARKER_DEEP_THRESHOLD: int = 2
    
    # ── 快速路由阈值 ──────────────────────────────────────────
    QUICK_THRESHOLD_CHARS: int = 25
    
    # ── 路由层级 fold_depth 范围 ──────────────────────────────
    ROUTING_TIER_QUICK: Tuple[int, int] = (0, 0)
    ROUTING_TIER_STANDARD: Tuple[int, int] = (1, 3)
    ROUTING_TIER_DEEP: Tuple[int, int] = (3, 6)
    ROUTING_TIER_FALLBACK: Tuple[int, int] = (1, 2)


# ════════════════════════════════════════════════════════════════════
# § 2 · 压缩配置
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class N9R20CompressionConfig:
    """
    压缩引擎的所有常量。

    涵盖 N9R20CompressionCore、N9R20SemanticValidator、
    N9R20DynamicFoldEngine 中的阈值。
    """

    # ── 四模编码难度阈值 ─────────────────────────────────────
    MODE_SIMPLE_DIFFICULTY_THRESHOLD: float = 0.3
    MODE_MEDIUM_DIFFICULTY_THRESHOLD: float = 0.7
    
    # ── 模式序列定义 ─────────────────────────────────────────
    MODE_SEQUENCE_SIMPLE: list = field(default_factory=lambda: ["construct", "interrupt"])
    MODE_SEQUENCE_MEDIUM: list = field(default_factory=lambda: ["construct", "deconstruct", "interrupt"])
    MODE_SEQUENCE_HARD: list = field(default_factory=lambda: ["construct", "deconstruct", "validate", "interrupt"])
    
    # ── 简单压缩参数（fallback 实现） ─────────────────────────
    SIMPLE_COMPRESS_RATIO: float = 0.6
    
    # ── 验证器估算参数 ───────────────────────────────────────
    VALIDATOR_ESTIMATION_DIVISOR: float = 0.5
    
    # ── 语义保留率阈值 ──────────────────────────────────────
    SEMANTIC_RETENTION_THRESHOLD: float = 0.85
    
    # ── fold 深度惩罚系数 ────────────────────────────────────
    FOLD_DEPTH_PENALTY_PER_LEVEL: float = 0.02


# ════════════════════════════════════════════════════════════════════
# § 3 · 记忆配置
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class N9R20MemoryConfig:
    """
    记忆学习器的所有常量。

    涵盖 N9R20MemoryLearner 中的环形缓冲区、遗忘曲线
    和技能书传播参数。
    """

    # ── 记忆容量 ─────────────────────────────────────────────
    MAX_MEMORIES: int = 1000
    FORGET_HALFLIFE: float = 86400.0
    FORGET_THRESHOLD: float = 0.1

    # ── 技能书传播 ───────────────────────────────────────────
    PROPAGATION_RATE: float = 0.1
    PROPAGATION_THRESHOLD: float = 0.15
    PROPAGATION_MIN_CALLS: int = 3
    PROPAGATION_PERIOD: int = 10
    FORGET_PERIOD: int = 50

    # ── 技能传播得分权重 ─────────────────────────────────────
    SKILL_SCORE_WEIGHT_RETENTION: float = 0.5
    SKILL_SCORE_WEIGHT_SUCCESS: float = 0.3
    SKILL_SCORE_WEIGHT_COMPRESSION: float = 0.2

    # ── 推荐系统 ─────────────────────────────────────────────
    RECOMMEND_MIN_CALLS: int = 2
    RECOMMEND_WEIGHT_RETENTION: float = 0.4
    RECOMMEND_WEIGHT_SUCCESS: float = 0.3
    RECOMMEND_WEIGHT_COMPRESSION: float = 0.3
    RECOMMEND_RECENCY_FACTOR: float = 0.1
    RECOMMEND_RECENCY_WINDOW: float = 3600.0

    # ── 查询预览 ─────────────────────────────────────────────
    QUERY_PREVIEW_MAX_CHARS: int = 100

    # ── 核心技能列表 ─────────────────────────────────────────
    CORE_SKILLS: Tuple[str, ...] = (
        "compression-core",
        "dual-reasoner",
        "semantic-graph",
        "memory-learner",
        "adaptive-n9r20_router",
    )


# ════════════════════════════════════════════════════════════════════
# § 4 · 语义图谱配置
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class N9R20SemanticGraphConfig:
    """
    语义图谱的所有常量。

    涵盖 N9R20SemanticGraph、N9R20EdgeWeightDecay、
    N9R20ConceptCluster 中的参数。
    """

    # ── 边权重衰减 ───────────────────────────────────────────
    EDGE_DECAY_HALFLIFE: float = 3600.0
    EDGE_PRUNE_THRESHOLD: float = 0.05
    EDGE_REINFORCE_INCREMENT: float = 0.1
    EDGE_INITIAL_WEIGHT: float = 0.3
    EDGE_NEIGHBOR_MIN_WEIGHT: float = 0.1

    # ── 术语提取 ─────────────────────────────────────────────
    TERM_CONFIDENCE_DEFAULT: float = 0.7
    TERM_CONFIDENCE_INCREMENT: float = 0.05

    # ── 共现窗口 ─────────────────────────────────────────────
    COOCCURRENCE_WINDOW_SIZE: int = 3

    # ── 簇检测 ───────────────────────────────────────────────
    CLUSTER_MIN_SIZE: int = 3
    CLUSTER_MAX_ITERATIONS: int = 10
    CLUSTER_TENSION_THRESHOLD: float = 0.1
    CLUSTER_ISOLATED_TENSION: float = 0.7

    # ── 剪枝周期 ─────────────────────────────────────────────
    PRUNE_PERIOD: int = 10

    # ── BFS 路径搜索 ─────────────────────────────────────────
    PATH_MAX_DEPTH: int = 4

    # ── 事件触发阈值 ─────────────────────────────────────────
    EVENT_TERM_COUNT_THRESHOLD: int = 5
    EVENT_CLUSTER_COUNT_THRESHOLD: int = 2


# ════════════════════════════════════════════════════════════════════
# § 5 · 张力类型配置
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class N9R20TensionConfig:
    """
    张力类型系统的内置常量。

    支持运行时动态注册新张力类型，此处仅定义内置类型。
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

    # ── 默认张力类型 ─────────────────────────────────────────
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


# ════════════════════════════════════════════════════════════════════
# § 6 · 模块级便捷访问
# ════════════════════════════════════════════════════════════════════

n9r20_routing_config = N9R20RoutingConfig()
n9r20_compression_config = N9R20CompressionConfig()
n9r20_memory_config = N9R20MemoryConfig()
n9r20_semantic_graph_config = N9R20SemanticGraphConfig()
n9r20_tension_config = N9R20TensionConfig()
