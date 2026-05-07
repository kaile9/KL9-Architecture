"""
9R-2.0 RHIZOME · Concept Conflict Detector
───────────────────────────────────────────
上下文感知概念冲突检测 — 识别语义图谱中概念之间的定义/视角/张力冲突。

设计原则：
    1. 上下文感知：同一概念在不同语境中的含义差异被显式建模
    2. 三级冲突检测：定义冲突 / 视角冲突 / 张力冲突
    3. 自然语言报告：生成人类可读的冲突报告
    4. 与 semantic_graph 集成：使用 N9R20SemanticGraph 的术语网络和概念簇
    5. 支持增量更新：新概念加入时自动检测与已有概念的冲突

冲突类型：
    - "definition": 同一概念在不同来源中有不同定义
    - "perspective": 两个概念分属不可调和的视角（如 A/B 视角差异）
    - "tension": 两个概念之间检测到结构性张力（来自 N9R20Tension）

与 N9R20SemanticGraph 的关系：
    - 使用 semantic_graph 的术语节点和边权重作为输入
    - 使用概念簇（N9R20ConceptCluster）检测簇间张力
    - 将冲突结果写入 N9R20ConceptProvenance（来源追踪）

使用示例：
    >>> detector = N9R20ConceptConflictDetector()
    >>> conflicts = detector.detect(semantic_graph.n9r20_semantic_graph)
    >>> for conflict in conflicts:
    ...     print(conflict.to_natural_language())
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from core.n9r20_structures import N9R20ConceptConflict, N9R20TermNode


# ════════════════════════════════════════════════════════════════════
# § 1 · N9R20ConflictReport — 自然语言冲突报告
# ════════════════════════════════════════════════════════════════════


@dataclass
class N9R20ConflictReport:
    """
    概念冲突的自然语言报告。

    将 N9R20ConceptConflict 的结构化数据转化为人类可读的文本，
    包含冲突摘要、详细分析、建议的分辨策略。
    """

    conflict: N9R20ConceptConflict
    """底层冲突数据"""

    conflict_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    """报告唯一标识"""

    generated_at: float = field(default_factory=time.time)
    """生成时间戳"""

    # ── 自然语言生成 ──

    def summary(self) -> str:
        """
        生成单行冲突摘要。

        返回：
            一行摘要文本

        示例：
            >>> report.summary()
            "概念 '空' 与 '存在' 之间存在张力冲突（严重度: 0.75）"
        """
        c = self.conflict
        if c.conflict_type == "definition":
            return (
                f"概念 '{c.concept_a}' 存在定义冲突: {c.description} "
                f"（严重度: {c.severity:.2f}）"
            )
        elif c.conflict_type == "perspective":
            return (
                f"概念 '{c.concept_a}' 与 '{c.concept_b}' 分属不可调和的视角: "
                f"{c.description}（严重度: {c.severity:.2f}）"
            )
        elif c.conflict_type == "tension":
            return (
                f"概念 '{c.concept_a}' 与 '{c.concept_b}' 之间存在张力冲突: "
                f"{c.description}（严重度: {c.severity:.2f}）"
            )
        else:
            return (
                f"概念 '{c.concept_a}' 与 '{c.concept_b}' 冲突: "
                f"{c.description}（严重度: {c.severity:.2f}）"
            )

    def detailed(self) -> str:
        """
        生成详细冲突分析。

        返回：
            多行详细分析文本
        """
        c = self.conflict
        lines: List[str] = [
            "─" * 50,
            f"  冲突报告 #{self.conflict_id}",
            "─" * 50,
            "",
            f"  类型:     {self._type_label(c.conflict_type)}",
            f"  概念 A:   {c.concept_a}",
            f"  概念 B:   {c.concept_b or '(N/A)'}",
            f"  严重度:   {c.severity:.2f} ({self._severity_label(c.severity)})",
            f"  描述:     {c.description}",
            "",
            "  建议:",
        ]

        for suggestion in self._suggestions():
            lines.append(f"    · {suggestion}")

        lines.append("")
        lines.append("─" * 50)
        return "\n".join(lines)

    def to_natural_language(self) -> str:
        """
        生成完整的自然语言冲突报告（同 detailed()）。

        返回：
            完整报告文本
        """
        return self.detailed()

    # ── 内部辅助 ──

    @staticmethod
    def _type_label(conflict_type: str) -> str:
        """冲突类型 → 中文标签。"""
        labels: Dict[str, str] = {
            "definition": "定义冲突",
            "perspective": "视角冲突",
            "tension": "张力冲突",
        }
        return labels.get(conflict_type, conflict_type)

    @staticmethod
    def _severity_label(severity: float) -> str:
        """严重度 → 中文标签。"""
        if severity >= 0.8:
            return "🔴 严重"
        elif severity >= 0.5:
            return "🟡 中等"
        elif severity >= 0.3:
            return "🟢 轻微"
        else:
            return "⚪ 可忽略"

    def _suggestions(self) -> List[str]:
        """根据冲突类型和严重度生成建议。"""
        c = self.conflict
        suggestions: List[str] = []

        if c.conflict_type == "definition":
            suggestions.append(
                f"检查 '{c.concept_a}' 在不同来源中的上下文差异，"
                "确认是否存在真正的语义分歧"
            )
            suggestions.append("考虑为不同语境创建独立的术语节点")

        elif c.conflict_type == "perspective":
            suggestions.append(
                f"'{c.concept_a}' 和 '{c.concept_b}' 可能来自不同的认知视角，"
                "需在压缩时显式标注视角差异"
            )
            suggestions.append("建议通过双视角推理（dual-reasoner）桥接")

        elif c.conflict_type == "tension":
            if c.severity >= 0.7:
                suggestions.append(
                    "高张力冲突 — 建议在压缩输出中显式保留这种张力，"
                    "而非强行消解"
                )
            else:
                suggestions.append(
                    "中低张力冲突 — 可通过概念解构（deconstruct）模式尝试调和"
                )

        suggestions.append("记录此次冲突到 production_logger 以供审计")
        return suggestions


# ════════════════════════════════════════════════════════════════════
# § 2 · N9R20ConceptConflictDetector — 上下文感知冲突检测器
# ════════════════════════════════════════════════════════════════════


class N9R20ConceptConflictDetector:
    """
    上下文感知概念冲突检测器。

    检测语义图谱中概念之间的三类冲突：
    1. 定义冲突 (definition)：
       同一概念在不同来源中有不同的上下文描述
       → 例如："空"在佛教语境 vs 物理语境中的差异

    2. 视角冲突 (perspective)：
       两个概念分属不可调和的认知视角
       → 例如："理论分析" vs "实践直觉"的对立

    3. 张力冲突 (tension)：
       两个概念之间存在结构性张力（来自概念簇的张力映射）
       → 例如：高密度概念簇与低密度概念簇之间的结构张力

    检测策略：
    - 定义冲突：检查 N9R20ConceptProvenance 中的 context_variants
    - 视角冲突：基于 perspective_A / perspective_B 的 characteristics 差异
    - 张力冲突：分析概念簇间的 inter_tension 和边权重模式

    与 N9R20SemanticGraph 的集成点：
    - detect(): 主入口，接收 semantic_graph 实例，返回冲突列表
    - detect_from_nodes(): 直接从节点字典检测（无需完整 graph）
    - detect_from_clusters(): 从概念簇列表检测张力冲突

    使用示例：
        >>> detector = N9R20ConceptConflictDetector()
        >>> conflicts = detector.detect(semantic_graph.n9r20_semantic_graph)
        >>> for c in conflicts:
        ...     report = detector.report(c)
        ...     print(report.summary())
    """

    # 冲突检测阈值
    DEFINITION_CONFLICT_THRESHOLD: float = 0.3
    """定义冲突的最低严重度阈值"""

    PERSPECTIVE_CONFLICT_THRESHOLD: float = 0.4
    """视角冲突的最低严重度阈值"""

    TENSION_CONFLICT_THRESHOLD: float = 0.3
    """张力冲突的最低严重度阈值"""

    def __init__(self) -> None:
        """初始化冲突检测器。"""
        self._detected_conflicts: List[N9R20ConceptConflict] = []
        self._conflict_reports: Dict[str, N9R20ConflictReport] = {}

    # ── 公共 API ──────────────────────────────────────────────

    def detect(self, semantic_graph: Any) -> List[N9R20ConceptConflict]:
        """
        从语义图谱中检测所有概念冲突。

        参数：
            semantic_graph: N9R20SemanticGraph 实例（或其子集）

        返回：
            N9R20ConceptConflict 列表
        """
        conflicts: List[N9R20ConceptConflict] = []

        # 获取节点和边
        nodes: Dict[str, Any] = {}
        edges: Dict[Tuple[str, str], float] = {}
        clusters: List[Any] = []

        try:
            nodes = getattr(semantic_graph, "_nodes", {})
            edges = getattr(semantic_graph, "_edges", {})
            clusters = getattr(semantic_graph, "detect_clusters", lambda: [])()
        except Exception:
            pass

        # 1. 定义冲突检测
        definition_conflicts = self._detect_definition_conflicts(nodes)
        conflicts.extend(definition_conflicts)

        # 2. 视角冲突检测
        perspective_conflicts = self._detect_perspective_conflicts(nodes, edges)
        conflicts.extend(perspective_conflicts)

        # 3. 张力冲突检测
        tension_conflicts = self._detect_tension_conflicts(clusters, edges)
        conflicts.extend(tension_conflicts)

        self._detected_conflicts = conflicts
        return conflicts

    def detect_from_nodes(
        self,
        nodes: Dict[str, Any],
        edges: Optional[Dict[Tuple[str, str], float]] = None,
    ) -> List[N9R20ConceptConflict]:
        """
        从节点字典直接检测冲突（无需完整 graph）。

        参数：
            nodes: {term: N9R20ConceptNode | N9R20TermNode}
            edges: 可选的边权重字典 {(a, b): weight}

        返回：
            N9R20ConceptConflict 列表
        """
        conflicts: List[N9R20ConceptConflict] = []
        edges = edges or {}

        # 定义冲突
        conflicts.extend(self._detect_definition_conflicts(nodes))

        # 视角冲突
        conflicts.extend(self._detect_perspective_conflicts(nodes, edges))

        self._detected_conflicts = conflicts
        return conflicts

    def detect_from_clusters(
        self,
        clusters: List[Any],
        edges: Optional[Dict[Tuple[str, str], float]] = None,
    ) -> List[N9R20ConceptConflict]:
        """
        从概念簇列表检测张力冲突。

        参数：
            clusters: N9R20ConceptCluster 列表
            edges: 可选的边权重字典

        返回：
            N9R20ConceptConflict 列表
        """
        conflicts = self._detect_tension_conflicts(clusters, edges or {})
        self._detected_conflicts = conflicts
        return conflicts

    def report(self, conflict: N9R20ConceptConflict) -> N9R20ConflictReport:
        """
        为冲突生成自然语言报告。

        参数：
            conflict: 冲突对象

        返回：
            N9R20ConflictReport 实例
        """
        report = N9R20ConflictReport(conflict=conflict)
        self._conflict_reports[report.conflict_id] = report
        return report

    def report_all(self) -> str:
        """
        为所有已检测冲突生成汇总报告。

        返回：
            多冲突汇总文本
        """
        if not self._detected_conflicts:
            return "✓ 未检测到概念冲突。"

        lines: List[str] = [
            "=" * 60,
            f"  概念冲突检测汇总 — 共 {len(self._detected_conflicts)} 处冲突",
            "=" * 60,
            "",
        ]

        by_type: Dict[str, List[N9R20ConceptConflict]] = {}
        for c in self._detected_conflicts:
            by_type.setdefault(c.conflict_type, []).append(c)

        for ctype, conflicts in by_type.items():
            label = N9R20ConflictReport._type_label(ctype)
            lines.append(f"  [{label}] {len(conflicts)} 处:")
            for c in conflicts:
                report = self.report(c)
                lines.append(f"    · {report.summary()}")
            lines.append("")

        # 统计
        avg_severity = (
            sum(c.severity for c in self._detected_conflicts)
            / len(self._detected_conflicts)
        )
        high_severity = sum(
            1 for c in self._detected_conflicts if c.severity >= 0.7
        )
        lines.append(f"  平均严重度: {avg_severity:.2f}")
        lines.append(f"  高严重度 (≥0.7): {high_severity} 处")
        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def clear(self) -> None:
        """清除所有检测到的冲突和报告。"""
        self._detected_conflicts.clear()
        self._conflict_reports.clear()

    # ── 内部检测方法 ──────────────────────────────────────────

    def _detect_definition_conflicts(
        self,
        nodes: Dict[str, Any],
    ) -> List[N9R20ConceptConflict]:
        """
        检测定义冲突。

        逻辑：
        对于每个节点，检查其 context_variants 是否有分歧。
        如果同一概念在不同来源中有不同描述 → 定义冲突。

        参数：
            nodes: {term: N9R20ConceptNode | N9R20TermNode}

        返回：
            定义冲突列表
        """
        conflicts: List[N9R20ConceptConflict] = []

        for term, node in nodes.items():
            # 检查是否有 context_variants 或 provenance
            context_variants: Dict[str, str] = getattr(
                node, "context_variants", {}
            )
            provenance = getattr(node, "provenance", None)

            has_divergence = False
            variant_values: List[str] = []

            if context_variants:
                variant_values = list(context_variants.values())
                has_divergence = len(set(variant_values)) > 1

            if provenance and hasattr(provenance, "has_divergence"):
                has_divergence = provenance.has_divergence()

            if has_divergence:
                unique_variants = list(set(variant_values))
                description = (
                    f"概念 '{term}' 在 {len(context_variants)} 个来源中"
                    f"存在 {len(unique_variants)} 种不同的语境解读: "
                    + "; ".join(
                        f"'{v}'" for v in unique_variants[:3]
                    )
                )
                severity = min(
                    0.3 + len(unique_variants) * 0.2, 1.0
                )

                if severity >= self.DEFINITION_CONFLICT_THRESHOLD:
                    conflicts.append(
                        N9R20ConceptConflict(
                            concept_a=term,
                            concept_b="",
                            conflict_type="definition",
                            description=description,
                            severity=round(severity, 2),
                        )
                    )

        return conflicts

    def _detect_perspective_conflicts(
        self,
        nodes: Dict[str, Any],
        edges: Dict[Tuple[str, str], float],
    ) -> List[N9R20ConceptConflict]:
        """
        检测视角冲突。

        逻辑：
        检查节点之间是否属于不同的认知视角。
        视角差异通过以下方式推断：
        1. 节点的关键词特征（理论词 vs 实践词）
        2. 边权重模式（低权重但高共现 = 可能视角对立）

        参数：
            nodes: {term: N9R20ConceptNode | N9R20TermNode}
            edges: {(a, b): weight}

        返回：
            视角冲突列表
        """
        conflicts: List[N9R20ConceptConflict] = []

        # 理论视角标记词
        theoretical_markers: Set[str] = {
            "理论", "分析", "抽象", "逻辑", "本质", "本体",
            "认识", "形而上学", "存在", "空", "中道", "般若",
            "量子", "拓扑", "范畴", "函子", "涌现",
        }

        # 实践视角标记词
        practical_markers: Set[str] = {
            "实践", "经验", "直觉", "具体", "应用", "操作",
            "效用", "结果", "行为", "方法", "策略", "解决",
        }

        # 分类节点
        theoretical_nodes: Dict[str, Any] = {}
        practical_nodes: Dict[str, Any] = {}

        for term, node in nodes.items():
            if any(m in term for m in theoretical_markers):
                theoretical_nodes[term] = node
            elif any(m in term for m in practical_markers):
                practical_nodes[term] = node

        # 检测跨视角的边
        for t_term in theoretical_nodes:
            for p_term in practical_nodes:
                key = tuple(sorted([t_term, p_term]))
                weight = edges.get(key, 0.0)

                # 有边但权重低 → 可能视角矛盾
                if 0.05 < weight < 0.4:
                    severity = 0.4 + (0.4 - weight)  # 权重越低，严重度越高
                    severity = round(min(severity, 1.0), 2)

                    if severity >= self.PERSPECTIVE_CONFLICT_THRESHOLD:
                        description = (
                            f"概念 '{t_term}'（理论视角）与 '{p_term}'（实践视角）"
                            f"之间存在视角差异，边权重 {weight:.3f} 暗示潜在对立"
                        )
                        conflicts.append(
                            N9R20ConceptConflict(
                                concept_a=t_term,
                                concept_b=p_term,
                                conflict_type="perspective",
                                description=description,
                                severity=severity,
                            )
                        )

        return conflicts

    def _detect_tension_conflicts(
        self,
        clusters: List[Any],
        edges: Dict[Tuple[str, str], float],
    ) -> List[N9R20ConceptConflict]:
        """
        从概念簇检测张力冲突。

        逻辑：
        1. 检查每个簇的 inter_tension 映射
        2. 高张力簇对 → 报告其中心术语之间的冲突
        3. 检查边权重模式（桥接边少但权重高 = 潜在冲突点）

        参数：
            clusters: N9R20ConceptCluster 列表
            edges: 边权重字典

        返回：
            张力冲突列表
        """
        conflicts: List[N9R20ConceptConflict] = []

        if len(clusters) < 2:
            return conflicts

        for i, c1 in enumerate(clusters):
            c1_terms: Set[str] = getattr(c1, "terms", set())
            c1_centroid: str = getattr(c1, "centroid", "")
            inter_tension: Dict[str, float] = getattr(
                c1, "inter_tension", {}
            )

            for c2 in clusters[i + 1:]:
                c2_terms: Set[str] = getattr(c2, "terms", set())
                c2_centroid: str = getattr(c2, "centroid", "")
                c2_id: str = getattr(c2, "cluster_id", "")

                # 从 inter_tension 读取张力
                tension = inter_tension.get(c2_id, 0.0)

                # 如果 inter_tension 为空，从边权重计算
                if tension == 0.0:
                    tension = self._compute_cluster_pair_tension(
                        c1_terms, c2_terms, edges
                    )

                if tension >= self.TENSION_CONFLICT_THRESHOLD:
                    concept_a = c1_centroid or (
                        list(c1_terms)[0] if c1_terms else f"cluster_{i}"
                    )
                    concept_b = c2_centroid or (
                        list(c2_terms)[0] if c2_terms else f"cluster_{i+1}"
                    )

                    description = (
                        f"概念簇 '{concept_a}' 与 '{concept_b}' 之间"
                        f"存在结构性张力（{tension:.2f}），"
                        f"建议在压缩时保留这种张力而非强行消解"
                    )

                    conflicts.append(
                        N9R20ConceptConflict(
                            concept_a=concept_a,
                            concept_b=concept_b,
                            conflict_type="tension",
                            description=description,
                            severity=round(tension, 2),
                        )
                    )

        return conflicts

    @staticmethod
    def _compute_cluster_pair_tension(
        terms_a: Set[str],
        terms_b: Set[str],
        edges: Dict[Tuple[str, str], float],
    ) -> float:
        """
        计算两个概念簇之间的张力。

        基于桥接边的平均权重：
        - 桥接边少且权重低 → 高张力（语义距离远）
        - 桥接边多且权重高 → 低张力（语义相近）

        参数：
            terms_a: 簇 A 的术语集合
            terms_b: 簇 B 的术语集合
            edges: 边权重字典

        返回：
            张力值 [0, 1]
        """
        bridge_weights: List[float] = []
        for ta in terms_a:
            for tb in terms_b:
                key = tuple(sorted([ta, tb]))
                if key in edges:
                    bridge_weights.append(edges[key])

        if not bridge_weights:
            # 无桥接边 → 高张力
            return 0.7

        avg_weight = sum(bridge_weights) / len(bridge_weights)
        # 低平均权重 + 少桥接边 → 高张力
        connection_density = len(bridge_weights) / (
            len(terms_a) * len(terms_b)
        )
        tension = (1.0 - avg_weight) * 0.6 + (1.0 - connection_density) * 0.4
        return round(min(tension, 1.0), 2)


# ════════════════════════════════════════════════════════════════════
# § 3 · 全局单例
# ════════════════════════════════════════════════════════════════════

#: 全局概念冲突检测器单例
n9r20_conflict_detector: N9R20ConceptConflictDetector = (
    N9R20ConceptConflictDetector()
)


__all__ = [
    "N9R20ConflictReport",
    "N9R20ConceptConflictDetector",
    "n9r20_conflict_detector",
]
