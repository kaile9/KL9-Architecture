"""
9R-2.0 RHIZOME · Adaptive-Router
自适应路由器 · 动态 fold 预算分配 · 回退决策

Phase 3 重构：
- 将 specialized_keywords 移到 N9R20RoutingConfig
- 用配置常量替换魔法数字
- 将重复的 _compute_concept_density() 提取到 n9r20_utils
"""

import re
import time
from typing import Tuple, List

from core.n9r20_structures import N9R20RoutingDecision
from core.n9r20_tension_bus import N9R20TensionBus, n9r20_bus
from core.n9r20_config import n9r20_routing_config
from core.n9r20_utils import (
    compute_concept_density,
    compute_tension_factor,
    compute_difficulty,
    allocate_fold_budget,
    compute_target_ratio,
    compute_length_factor,
    clamp,
)


class N9R20AdaptiveRouter:
    """
    自适应路由器

    三级决策：
    1. 文本类型检测（专用 vs 通用）
    2. 难度评估（0-1 连续谱）
    3. fold 预算分配（2-9 动态）

    Phase 3: 所有魔法数字和关键词列表从 N9R20RoutingConfig 导入。
    """

    def __init__(self):
        self.n9r20_bus = n9r20_bus
        self._config = n9r20_routing_config

        # Phase 3: 从配置导入关键词列表（向后兼容属性）
        self.specialized_keywords = list(self._config.specialized_keywords)

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

        # Level 2: 难度评估 — Phase 3: 使用 n9r20_utils.compute_difficulty
        difficulty = self._assess_difficulty(query)

        # Level 3: fold 预算分配 — Phase 3: 使用 n9r20_utils.allocate_fold_budget
        target_fold_depth = self._allocate_fold_budget(
            query_length=len(query),
            difficulty=difficulty,
            is_specialized=is_specialized,
        )

        # Level 4: 压缩率目标 — Phase 3: 使用 n9r20_utils.compute_target_ratio
        target_ratio = self._compute_target_ratio(
            query_length=len(query),
            difficulty=difficulty,
        )

        # Level 5: 紧急度计算
        urgency = self._compute_urgency(difficulty, len(query))

        # Phase 3: 使用 n9r20_utils 函数计算辅助指标
        density = compute_concept_density(
            query,
            specialized_keywords=self._config.specialized_keywords,
            window=self._config.concept_density_window,
            min_base=self._config.concept_density_min_base,
        )
        tension = compute_tension_factor(
            query,
            tension_keywords=self._config.tension_keywords,
            normalizer=self._config.tension_normalizer,
        )
        length_f = compute_length_factor(
            query,
            cap=self._config.length_factor_max,
        )

        return N9R20RoutingDecision(
            path="specialized" if is_specialized else "standard",
            confidence=confidence,
            difficulty=difficulty,
            target_fold_depth=target_fold_depth,
            target_compression_ratio=target_ratio,
            urgency=urgency,
            concept_density=density,
            tension_factor=tension,
            length_factor=length_f,
        )

    def _detect_specialized_text(self, query: str) -> Tuple[bool, float]:
        """
        检测专用文本 + 置信度

        Phase 3: 使用配置常量替代魔法数字。
        """
        kw = self._config.specialized_keywords
        keyword_count = sum(1 for k in kw if k in query)
        keyword_score = min(keyword_count / 1.0, 1.0)

        # Phase 3: 使用 n9r20_utils 函数
        concept_density_val = compute_concept_density(
            query,
            specialized_keywords=kw,
            window=self._config.concept_density_window,
            min_base=self._config.concept_density_min_base,
        )
        tension_factor_val = compute_tension_factor(
            query,
            tension_keywords=self._config.tension_keywords,
            normalizer=self._config.tension_normalizer,
        )

        confidence = (
            keyword_score * self._config.keyword_confidence_weight +
            concept_density_val * self._config.concept_density_weight +
            tension_factor_val * self._config.tension_weight
        )

        is_specialized = confidence > self._config.specialized_threshold

        return is_specialized, round(confidence, 2)

    def _assess_difficulty(self, query: str) -> float:
        """
        评估任务难度（0-1 连续谱）

        Phase 3: 委托给 n9r20_utils.compute_difficulty。
        """
        return compute_difficulty(
            query,
            specialized_keywords=self._config.specialized_keywords,
            tension_keywords=self._config.tension_keywords,
            length_divisor=self._config.difficulty_length_divisor,
            length_weight=self._config.difficulty_length_weight,
            concept_weight=self._config.difficulty_concept_weight,
            tension_weight=self._config.difficulty_tension_weight,
            specialized_weight=self._config.difficulty_specialized_weight,
            specialized_bonus=self._config.specialized_bonus,
            specialized_threshold=self._config.specialized_threshold,
        )

    def _allocate_fold_budget(self, query_length: int,
                             difficulty: float,
                             is_specialized: bool) -> int:
        """
        动态分配 fold 深度（2-9）

        Phase 3: 委托给 n9r20_utils.allocate_fold_budget。
        """
        return allocate_fold_budget(
            query_length=query_length,
            difficulty=difficulty,
            is_specialized=is_specialized,
            fold_by_difficulty=self._config.fold_by_difficulty,
            fold_min=self._config.fold_depth_min,
            fold_max=self._config.fold_depth_max,
            long_threshold_1=self._config.fold_long_text_threshold_1,
            long_bonus_1=self._config.fold_long_text_bonus_1,
            long_threshold_2=self._config.fold_long_text_threshold_2,
            long_bonus_2=self._config.fold_long_text_bonus_2,
            specialized_penalty=self._config.fold_specialized_penalty,
        )

    def _compute_target_ratio(self, query_length: int,
                              difficulty: float) -> float:
        """
        动态调整目标压缩率

        Phase 3: 委托给 n9r20_utils.compute_target_ratio。
        """
        return compute_target_ratio(
            query_length=query_length,
            difficulty=difficulty,
            base_ratio=self._config.base_compression_ratio,
            long_threshold=self._config.ratio_long_threshold,
            long_target=self._config.ratio_long_target,
            high_difficulty_threshold=self._config.ratio_high_difficulty_threshold,
            high_difficulty_reduction=self._config.ratio_high_difficulty_reduction,
            ratio_min=self._config.ratio_min,
            ratio_max=self._config.ratio_max,
        )

    def _compute_urgency(self, difficulty: float,
                         query_length: int) -> float:
        """
        计算紧急度 [0,1]

        Phase 3: 使用配置常量替代魔法数字。
        """
        urgency = difficulty * self._config.urgency_difficulty_weight

        for threshold, bonus in self._config.urgency_long_text_thresholds:
            if query_length > threshold:
                urgency += bonus
                break

        return round(clamp(urgency, 0.0, 1.0), 2)

    # Phase 3: 保留向后兼容的方法签名（委托给 n9r20_utils）

    def _compute_concept_density(self, query: str) -> float:
        """
        计算概念密度 — 向后兼容方法

        Phase 3: 委托给 n9r20_utils.compute_concept_density。
        """
        return compute_concept_density(
            query,
            specialized_keywords=self._config.specialized_keywords,
            window=self._config.concept_density_window,
            min_base=self._config.concept_density_min_base,
        )

    def _detect_tension_keywords(self, query: str) -> float:
        """
        检测张力关键词 — 向后兼容方法

        Phase 3: 委托给 n9r20_utils.compute_tension_factor。
        """
        return compute_tension_factor(
            query,
            tension_keywords=self._config.tension_keywords,
            normalizer=self._config.tension_normalizer,
        )


# 全局单例
n9r20_router = N9R20AdaptiveRouter()
