"""
9R-2.0 RHIZOME · Dual-Reasoner
双视角推理器 · 整合 reasoner + soul

职责：
1. 构建 A/B 视角 → 辩证折叠 → 生成张力
2. 统一理论视角（A）和具身视角（B）
3. 输出 N9R20Tension + 四模编码建议

Phase 3 重构：
- 移除硬编码哲学关键词
- 通过 N9R20UserConfig 使关键词列表可配置
- 集成概念冲突检测
"""

import time
from typing import List, Dict, Optional

from core.n9r20_structures import (
    N9R20Perspective, N9R20Tension, N9R20PerspectiveType, N9R20ConceptConflict,
)
from core.n9r20_tension_bus import (
    N9R20TensionBus, n9r20_bus,
    N9R20CompressionTensionEvent, N9R20DualPerspectiveEvent,
    N9R20TensionSubscription,
)
from core.n9r20_user_config import N9R20UserConfig, n9r20_user_config
from core.n9r20_concept_conflict import (
    N9R20ConceptConflictDetector, n9r20_conflict_detector,
)


class N9R20DualReasoner:
    """
    双视角推理器

    整合 reasoner（理论视角）+ soul（具身视角）

    核心功能：
    1. 构建 N9R20Perspective A（理论视角）
    2. 构建 N9R20Perspective B（具身视角）
    3. 生成 A/B 之间的张力
    4. 发射到 N9R20TensionBus
    5. Phase 3: 集成概念冲突检测
    """

    def __init__(self,
                 user_config: Optional[N9R20UserConfig] = None,
                 conflict_detector: Optional[N9R20ConceptConflictDetector] = None):
        self.n9r20_bus = n9r20_bus
        self._user_config = user_config or n9r20_user_config
        self._conflict_detector = conflict_detector or n9r20_conflict_detector

        # Phase 3: 可配置的关键词列表（通过 N9R20UserConfig）
        self._theoretical_keywords = self._build_theoretical_keywords()
        self._embodied_keywords = self._build_embodied_keywords()
        self._opposition_pairs = [
            ("抽象", "具体"),
            ("逻辑", "直觉"),
            ("分析", "综合"),
            ("理论", "实践"),
            ("普遍", "特殊"),
        ]

        # 订阅 N9R20CompressionTensionEvent
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="dual-reasoner",
            event_types=["N9R20CompressionTensionEvent"],
            callback=self.on_compression_event,
        ))

    def _build_theoretical_keywords(self) -> List[str]:
        """构建理论视角关键词（默认 + 用户自定义）"""
        base = [
            "理论", "概念", "抽象", "逻辑", "分析",
            "結構", "系統", "模型", "框架", "原理",
        ]
        # Phase 3: 合并用户自定义关键词
        custom = getattr(self._user_config, 'custom_keywords', [])
        return list(dict.fromkeys(base + custom))

    def _build_embodied_keywords(self) -> List[str]:
        """构建具身视角关键词（默认 + 用户自定义）"""
        base = [
            "经验", "感受", "直觉", "具体", "实践",
            "體驗", "直觀", "現象", "情境", "個案",
        ]
        custom = getattr(self._user_config, 'custom_tension_keywords', [])
        return list(dict.fromkeys(base + custom))

    def on_compression_event(self, event: N9R20CompressionTensionEvent):
        """
        响应压缩事件，构建 A/B 视角
        """
        query = event.query

        perspective_A = self._construct_theoretical_perspective(query)
        perspective_B = self._construct_embodied_perspective(query)
        tension = self._generate_tension(perspective_A, perspective_B, query)

        self.n9r20_bus.emit(N9R20DualPerspectiveEvent(
            session_id=event.session_id,
            perspective_A=perspective_A,
            perspective_B=perspective_B,
            tension=tension,
        ))

    def _construct_theoretical_perspective(self, query: str) -> N9R20Perspective:
        """构建理论视角（N9R20Perspective A）"""
        characteristics = self._extract_theoretical_characteristics(query)

        return N9R20Perspective(
            name="theoretical",
            characteristics=characteristics,
            key="perspective_A",
            perspective_type=N9R20PerspectiveType.THEORETICAL,
        )

    def _construct_embodied_perspective(self, query: str) -> N9R20Perspective:
        """构建具身视角（N9R20Perspective B）"""
        characteristics = self._extract_embodied_characteristics(query)

        return N9R20Perspective(
            name="embodied",
            characteristics=characteristics,
            key="perspective_B",
            perspective_type=N9R20PerspectiveType.EMBODIED,
        )

    def _generate_tension(self, A: N9R20Perspective, B: N9R20Perspective,
                          query: str) -> N9R20Tension:
        """生成 A/B 之间的张力"""
        irreconcilable = self._find_irreconcilable_points(A, B, query)

        claim_A = self._extract_claim(A, query)
        claim_B = self._extract_claim(B, query)

        tension_type = self._infer_tension_type(A, B, query)

        intensity = min(len(irreconcilable) / 5.0, 1.0)

        # Phase 3: 概念冲突检测
        self._detect_and_report_conflicts(A, B, irreconcilable, query)

        return N9R20Tension(
            perspective_A=A.name,
            perspective_B=B.name,
            claim_A=claim_A,
            claim_B=claim_B,
            irreconcilable_points=irreconcilable,
            tension_type=tension_type,
            intensity=intensity,
        )

    def _extract_theoretical_characteristics(self, query: str) -> List[str]:
        """提取理论特征 — Phase 3: 使用可配置关键词"""
        characteristics = []

        for kw in self._theoretical_keywords:
            if kw in query:
                characteristics.append(kw)

        if not characteristics:
            characteristics = ["分析", "逻辑", "抽象"]

        return characteristics

    def _extract_embodied_characteristics(self, query: str) -> List[str]:
        """提取具身特征 — Phase 3: 使用可配置关键词"""
        characteristics = []

        for kw in self._embodied_keywords:
            if kw in query:
                characteristics.append(kw)

        if not characteristics:
            characteristics = ["经验", "直觉", "具体"]

        return characteristics

    def _find_irreconcilable_points(self, A: N9R20Perspective, B: N9R20Perspective,
                                    query: str) -> List[str]:
        """识别不可调和点"""
        irreconcilable = []

        a_chars = set(A.characteristics)
        b_chars = set(B.characteristics)

        for opp_a, opp_b in self._opposition_pairs:
            if opp_a in a_chars and opp_b in b_chars:
                irreconcilable.append(f"{opp_a} vs {opp_b}")

        if not irreconcilable:
            irreconcilable = ["理论抽象 vs 经验具体"]

        return irreconcilable

    def _extract_claim(self, perspective: N9R20Perspective, query: str) -> str:
        """提取视角的主张"""
        chars = ", ".join(perspective.characteristics[:3])
        return f"从{perspective.name}视角看，{query}涉及{chars}"

    def _infer_tension_type(self, A: N9R20Perspective, B: N9R20Perspective,
                            query: str) -> str:
        """推断张力类型"""
        if A.perspective_type == N9R20PerspectiveType.THEORETICAL and \
           B.perspective_type == N9R20PerspectiveType.EMBODIED:
            return "dialectical"

        return "dialectical"

    # Phase 3: 概念冲突检测集成

    def _detect_and_report_conflicts(
        self,
        A: N9R20Perspective,
        B: N9R20Perspective,
        irreconcilable: List[str],
        query: str,
    ) -> None:
        """
        检测 A/B 视角之间的概念冲突并生成报告。

        通过 N9R20ConceptConflictDetector 检测视角冲突，
        严重度基于不可调和点的数量。
        """
        if not irreconcilable:
            return

        # 为每个不可调和点创建冲突记录
        for point in irreconcilable[:3]:  # 最多报告 3 个
            parts = point.split(" vs ")
            if len(parts) == 2:
                severity = min(0.4 + len(irreconcilable) * 0.1, 1.0)
                conflict = N9R20ConceptConflict(
                    concept_a=parts[0],
                    concept_b=parts[1],
                    conflict_type="perspective",
                    description=(
                        f"双视角推理器检测到视角冲突: {point}。"
                        f"上下文: {query[:60]}..."
                    ),
                    severity=round(severity, 2),
                )
                # 生成冲突报告（可被 production_logger 或其他模块消费）
                self._conflict_detector.report(conflict)


# 全局单例
n9r20_dual_reasoner = N9R20DualReasoner()
