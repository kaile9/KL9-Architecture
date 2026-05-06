"""
9R-2.0 RHIZOME · Adaptive-Router
自适应路由器 · 动态 fold 预算分配 · 回退决策

重构说明（魔法数字消除）：
- 所有数值常量引用 core/n9r20_config.py
- 专用关键词改为可配置（默认从 N9R20TensionConfig 读取）
- 张力关键词改为可配置
- 内联计算委托给 core/n9r20_utils.py
"""

from typing import List, Optional, Tuple

from core.n9r20_structures import N9R20RoutingDecision
from core.n9r20_tension_bus import n9r20_bus
from core.n9r20_config import (
    n9r20_routing_config  as R_CFG,
    n9r20_tension_config  as T_CFG,
)
from core.n9r20_utils import (
    clamp,
    compute_concept_density,
    compute_tension_factor,
    compute_length_factor,
    compute_difficulty,
    allocate_fold_budget,
    compute_target_ratio,
)


class N9R20AdaptiveRouter:
    """
    自适应路由器

    三级决策：
    1. 文本类型检测（专用 vs 通用）
    2. 难度评估（0-1 连续谱）
    3. fold 预算分配（2-9 动态）
    """

    def __init__(
        self,
        specialized_keywords: Optional[List[str]] = None,
        tension_keywords: Optional[List[str]] = None,
    ):
        """
        初始化路由器

        参数：
            specialized_keywords: 专用文本关键词，None 时从配置读取
            tension_keywords: 张力关键词，None 时从配置读取
        """
        self.n9r20_bus = n9r20_bus

        # 专用文本关键词（可配置，默认从 TensionConfig 读取）
        self.specialized_keywords: List[str] = (
            list(specialized_keywords)
            if specialized_keywords is not None
            else list(T_CFG.DEFAULT_SPECIALIZED_KEYWORDS)
        )

        # 张力关键词（可配置，默认从 TensionConfig 读取）
        self._tension_keywords: List[str] = (
            list(tension_keywords)
            if tension_keywords is not None
            else list(T_CFG.DEFAULT_TENSION_KEYWORDS)
        )

    # ══════════════════════════════════════════════
    # 公共 API
    # ══════════════════════════════════════════════

    def route(self, query: str) -> N9R20RoutingDecision:
        """
        主路由函数

        返回 N9R20RoutingDecision 包含：
        - path: "specialized" | "standard"
        - confidence: 专用文本检测置信度
        - difficulty: 任务难度 [0,1]
        - target_fold_depth: 动态分配的 fold 深度 [2-9]
        - target_compression_ratio: 目标压缩率
        - urgency: 紧急度 [0,1]
        """
        # Level 1: 文本类型检测
        is_specialized, confidence = self._detect_specialized_text(query)

        # Level 2: 难度评估
        difficulty = self._assess_difficulty(query)

        # Level 3: fold 预算分配
        target_fold_depth = self._allocate_fold_budget(
            query_length=len(query),
            difficulty=difficulty,
            is_specialized=is_specialized,
        )

        # Level 4: 压缩率目标
        target_ratio = self._compute_target_ratio(
            query_length=len(query),
            difficulty=difficulty,
        )

        # Level 5: 紧急度计算
        urgency = self._compute_urgency(difficulty, len(query))

        return N9R20RoutingDecision(
            path="specialized" if is_specialized else "standard",
            confidence=confidence,
            difficulty=difficulty,
            target_fold_depth=target_fold_depth,
            target_compression_ratio=target_ratio,
            urgency=urgency,
            concept_density=self._compute_concept_density(query),
            tension_factor=self._detect_tension_keywords(query),
            length_factor=compute_length_factor(len(query), R_CFG.LENGTH_MAX_CHARS),
        )

    # ══════════════════════════════════════════════
    # 私有方法
    # ══════════════════════════════════════════════

    def _detect_specialized_text(self, query: str) -> Tuple[bool, float]:
        """
        检测专用文本 + 置信度

        综合三个信号：关键词命中密度、概念密度、张力因子
        """
        # 关键词命中密度：单命中即可触发（baseline = 1.0）
        keyword_count = sum(1 for kw in self.specialized_keywords if kw in query)
        keyword_score = min(
            keyword_count / R_CFG.SPECIALIZED_KEYWORD_HIT_BASELINE, 1.0
        )

        # 概念密度（委托给 utils，使用路由器自身的专用关键词集）
        concept_density = self._compute_concept_density(query)

        # 张力因子
        tension_factor = self._detect_tension_keywords(query)

        # 加权置信度
        confidence = (
            keyword_score   * R_CFG.SPECIALIZED_WEIGHT_KEYWORD +
            concept_density * R_CFG.SPECIALIZED_WEIGHT_CONCEPT +
            tension_factor  * R_CFG.SPECIALIZED_WEIGHT_TENSION
        )

        is_specialized = confidence > R_CFG.SPECIALIZED_CONFIDENCE_THRESHOLD

        return is_specialized, round(confidence, 2)

    def _assess_difficulty(self, query: str) -> float:
        """
        评估任务难度（0-1 连续谱）

        影响因素：长度因子、概念密度、张力因子、专用文本加成
        """
        # 长度因子（以 CHARS_MEDIUM_THRESHOLD 作归一化基数，降低阈值）
        length_factor = min(len(query) / R_CFG.CHARS_MEDIUM_THRESHOLD, 1.0)

        concept_density = self._compute_concept_density(query)
        tension_factor  = self._detect_tension_keywords(query)

        is_specialized, _ = self._detect_specialized_text(query)
        specialized_factor = R_CFG.DIFFICULTY_WEIGHT_SPECIALIZED if is_specialized else 0.0

        difficulty = compute_difficulty(
            length_factor=length_factor,
            concept_density=concept_density,
            tension_factor=tension_factor,
            specialized_factor=specialized_factor,
            weights=[
                R_CFG.DIFFICULTY_WEIGHT_LENGTH,
                R_CFG.DIFFICULTY_WEIGHT_CONCEPT,
                R_CFG.DIFFICULTY_WEIGHT_TENSION,
                1.0,   # specialized_factor 已预乘权重，此处设 1.0
            ],
        )

        return difficulty

    def _allocate_fold_budget(
        self,
        query_length: int,
        difficulty: float,
        is_specialized: bool,
    ) -> int:
        """
        动态分配 fold 深度（2-9）

        委托给 core/n9r20_utils.allocate_fold_budget，
        参数均从 N9R20RoutingConfig 读取。
        """
        return allocate_fold_budget(
            difficulty=difficulty,
            query_length=query_length,
            is_specialized=is_specialized,
            length_threshold_1=R_CFG.LENGTH_MEDIUM_CHARS,
            length_threshold_2=R_CFG.LENGTH_MAX_CHARS,
            length_bonus_1=R_CFG.FOLD_MEDIUM_TEXT_BONUS,
            length_bonus_2=R_CFG.FOLD_LONG_TEXT_BONUS,
            specialized_penalty=R_CFG.FOLD_SPECIALIZED_PENALTY,
        )

    def _compute_target_ratio(self, query_length: int, difficulty: float) -> float:
        """
        动态调整目标压缩率

        委托给 core/n9r20_utils.compute_target_ratio，
        参数均从 N9R20RoutingConfig 读取。
        """
        return compute_target_ratio(
            query_length=query_length,
            difficulty=difficulty,
            base_ratio=R_CFG.COMPRESSION_RATIO_DEFAULT,
            long_text_threshold=R_CFG.LENGTH_MEDIUM_CHARS,
            long_text_ratio=R_CFG.COMPRESSION_LONG_TEXT_RATIO,
            high_difficulty_threshold=R_CFG.COMPRESSION_HIGH_DIFFICULTY_THRESHOLD,
            high_difficulty_adjustment=R_CFG.COMPRESSION_HIGH_DIFFICULTY_DELTA,
        )

    def _compute_urgency(self, difficulty: float, query_length: int) -> float:
        """
        计算紧急度 [0,1]

        高难度 + 长文本 → 高紧急度
        所有阈值来自 N9R20RoutingConfig。
        """
        urgency = difficulty * R_CFG.URGENCY_DIFFICULTY_WEIGHT

        if query_length > R_CFG.LENGTH_LONG_CHARS:
            urgency += R_CFG.URGENCY_LONG_BONUS
        elif query_length > R_CFG.LENGTH_MAX_CHARS:
            urgency += R_CFG.URGENCY_MEDIUM_BONUS
        elif query_length > R_CFG.LENGTH_MEDIUM_CHARS:
            urgency += R_CFG.URGENCY_SHORT_BONUS

        return round(clamp(urgency, 0.0, 1.0), 2)

    def _compute_concept_density(self, query: str) -> float:
        """
        计算概念密度

        仅统计命中自身 specialized_keywords 的中文术语；
        纯英文文本（无中文字符）返回 0.0。

        委托给 core/n9r20_utils.compute_concept_density。
        """
        return compute_concept_density(
            query=query,
            keywords=self.specialized_keywords,
            normalization_base=R_CFG.CHARS_PER_TERM,
        )

    def _detect_tension_keywords(self, query: str) -> float:
        """
        检测张力关键词，返回张力因子 [0,1]

        委托给 core/n9r20_utils.compute_tension_factor。
        """
        return compute_tension_factor(
            query=query,
            tension_keywords=self._tension_keywords,
            normalization_count=R_CFG.TENSION_MAX_KEYWORDS,
        )


# 全局单例
n9r20_router = N9R20AdaptiveRouter()
