"""N9R20Framework Adaptive Router

Text type detection, difficulty assessment, and compression budget allocation.
Routes queries to QUICK / STANDARD / DEEP / DEGRADED paths.

Academic markers (≥2 triggers DEEP):
    - 佛教 / 量子 / 哲学 / 辩证法 / 劳动过程理论 / 算法管理 / 泰勒制
"""

from typing import List, Tuple
from .n9r20_structures import FoldDepth, N9R20RoutingDecision
from typing import List

class N9R20AdaptiveRouter:
    """Adaptive routing based on academic content markers."""

    ACADEMIC_MARKERS = [
        "佛教", "量子", "哲学", "辩证法", "劳动过程", "算法管理",
        "泰勒制", "布雷弗曼", "布洛维", "霍赫希尔德", "斯尔尼塞克",
        "去技能化", "制造同意", "情感劳动", "平台资本主义",
        "黑箱", "悖论", "张力", "悬置", "连续性", "断裂",
    ]

    def __init__(self):
        self.marker_count_threshold = 2

    def detect(self, text: str) -> N9R20RoutingDecision:
        """Analyze text and return routing decision."""
        text_lower = text.lower()
        markers_found = [m for m in self.ACADEMIC_MARKERS if m in text]
        marker_count = len(markers_found)

        if len(text) <= 25 and marker_count == 0:
            return N9R20RoutingDecision(
                path="quick",
                target_fold_depth=0,
                confidence=0.9,
                academic_markers=markers_found,
                reasoning="Short query, no academic markers. Zero module overhead."
            )

        if marker_count >= self.marker_count_threshold:
            return N9R20RoutingDecision(
                path="deep",
                target_fold_depth=9,
                confidence=0.85,
                academic_markers=markers_found,
                reasoning=f"Academic markers >= {self.marker_count_threshold}: full chain activation."
            )

        return N9R20RoutingDecision(
            path="standard",
            target_fold_depth=3,
            confidence=0.7,
            academic_markers=markers_found,
            reasoning="Low academic content: single-layer expansion sufficient."
        )

    def degrade(self, decision: N9R20RoutingDecision) -> N9R20RoutingDecision:
        """Downgrade DEEP to STANDARD on failure."""
        if decision.path == "deep":
            return N9R20RoutingDecision(
                path="degraded",
                target_fold_depth=3,
                academic_markers=decision.academic_markers,
                reasoning="DEEP path failed. Fallback to STANDARD with reduced budget."
            )
        return decision

__all__ = ["N9R20AdaptiveRouter"]
