"""
9R-2.0 RHIZOME · SkillBook 兼容层
──────────────────────────────────
向下兼容旧版 kl9_skillbook 格式，同时扩展为新 9R-2.0 架构。

设计原则：
    1. 完整兼容旧版 SkillBookManifest 格式（skill_book_id, book_title,
       concept_count, difficulty_breakdown）
    2. 扩展生产元数据（N9R20ProductionRecord）追踪完整制作过程
    3. 上下文感知概念节点（N9R20ConceptNode）支持变体
    4. 导入器/导出器实现双向兼容
    5. 所有类名使用 N9R20 前缀，全局变量使用 n9r20_ 前缀

兼容映射：
    旧版 SkillBookManifest  →  N9R20SkillBookManifest（兼容 + 扩展）
    旧版 ProductionRecord   →  N9R20ProductionRecord（扩展字段）
    旧版 ConceptNode        →  N9R20ConceptNode（含 context_variants）
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ════════════════════════════════════════════════════════════════════
# § 1 · N9R20ProductionRecord — 扩展生产元数据
# ════════════════════════════════════════════════════════════════════


@dataclass
class N9R20ProductionRecord:
    """
    单次生产的完整元数据记录。

    记录从 query 到 compressed_output 的完整管线参数，
    用于调试、审计和技能书传播。

    兼容旧版 ProductionRecord 的全部字段并扩展。
    """

    # ── 标识 ──
    record_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str = ""
    skill_name: str = "compression-core"

    # ── 输入特征 ──
    query_preview: str = ""  # 前 100 字符
    query_length: int = 0
    concept_density: float = 0.0
    tension_factor: float = 0.0
    difficulty: float = 0.5

    # ── 路由决策 ──
    path: str = "standard"
    target_fold_depth: int = 4
    target_compression_ratio: float = 2.5
    urgency: float = 0.5

    # ── 压缩结果 ──
    actual_fold_depth: int = 0
    actual_compression_ratio: float = 1.0
    semantic_retention: float = 1.0
    mode_sequence: List[str] = field(default_factory=list)
    decision_ready: bool = False

    # ── 成功判定 ──
    success: bool = False

    # ── 时间戳 ──
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if len(self.query_preview) > 100:
            self.query_preview = self.query_preview[:100] + "..."

    # ── 兼容旧版序列化 ──────────────────────────────────────────

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        导出为旧版 dict 格式（kl9_skillbook 兼容）。

        旧版期望字段：record_id, skill_name, success, retention,
        compression_ratio, timestamp
        """
        return {
            "record_id": self.record_id,
            "skill_name": self.skill_name,
            "success": self.success,
            "retention": self.semantic_retention,
            "compression_ratio": self.actual_compression_ratio,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_legacy_dict(cls, data: Dict[str, Any]) -> "N9R20ProductionRecord":
        """从旧版 dict 格式导入。"""
        return cls(
            record_id=data.get("record_id", uuid.uuid4().hex[:12]),
            skill_name=data.get("skill_name", "compression-core"),
            success=data.get("success", False),
            semantic_retention=data.get("retention", 1.0),
            actual_compression_ratio=data.get("compression_ratio", 1.0),
            timestamp=data.get("timestamp", time.time()),
        )


# ════════════════════════════════════════════════════════════════════
# § 2 · N9R20DifficultyBreakdown — 难度分布追踪
# ════════════════════════════════════════════════════════════════════


@dataclass
class N9R20DifficultyBreakdown:
    """
    难度分布统计。

    追踪不同难度区间的生产次数与成功/失败率，
    用于技能书性能分析。

    兼容旧版 difficulty_breakdown 格式。
    """

    # 难度区间 → (总调用次数, 成功次数)
    easy: Tuple[int, int] = (0, 0)      # difficulty < 0.3
    medium: Tuple[int, int] = (0, 0)    # 0.3 ≤ difficulty < 0.7
    hard: Tuple[int, int] = (0, 0)      # difficulty ≥ 0.7

    def record(self, difficulty: float, success: bool) -> None:
        """记录一次生产。"""
        if difficulty < 0.3:
            bucket = "easy"
        elif difficulty < 0.7:
            bucket = "medium"
        else:
            bucket = "hard"

        total, succ = getattr(self, bucket)
        setattr(self, bucket, (total + 1, succ + (1 if success else 0)))

    def success_rate(self, bucket: str) -> float:
        """获取指定难度区间的成功率。"""
        total, succ = getattr(self, bucket, (0, 0))
        return succ / max(total, 1)

    def to_legacy_dict(self) -> Dict[str, Dict[str, int]]:
        """导出为旧版 difficulty_breakdown 格式。"""
        return {
            "easy": {"total": self.easy[0], "success": self.easy[1]},
            "medium": {"total": self.medium[0], "success": self.medium[1]},
            "hard": {"total": self.hard[0], "success": self.hard[1]},
        }

    @classmethod
    def from_legacy_dict(
        cls, data: Dict[str, Dict[str, int]]
    ) -> "N9R20DifficultyBreakdown":
        """从旧版 difficulty_breakdown 格式导入。"""
        return cls(
            easy=(
                data.get("easy", {}).get("total", 0),
                data.get("easy", {}).get("success", 0),
            ),
            medium=(
                data.get("medium", {}).get("total", 0),
                data.get("medium", {}).get("success", 0),
            ),
            hard=(
                data.get("hard", {}).get("total", 0),
                data.get("hard", {}).get("success", 0),
            ),
        )


# ════════════════════════════════════════════════════════════════════
# § 3 · N9R20ConceptProvenance — 概念来源追踪
# ════════════════════════════════════════════════════════════════════


@dataclass
class N9R20ConceptProvenance:
    """
    概念来源追踪。

    记录一个概念在不同 session / 文本中的出现及上下文差异，
    支持人文社科的上下文独立判断需求。
    """

    concept: str
    sources: List[str] = field(default_factory=list)  # session_id / 文本标识
    context_variants: Dict[str, str] = field(default_factory=dict)  # source → 上下文描述
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    occurrence_count: int = 0

    def touch(self, source: str, context_hint: str = "") -> None:
        """记录一次出现。"""
        if source not in self.sources:
            self.sources.append(source)
        if context_hint:
            self.context_variants[source] = context_hint
        self.occurrence_count += 1
        self.last_seen = time.time()

    def has_divergence(self) -> bool:
        """检测：同一概念在不同来源中是否有定义/语境差异。"""
        return len(set(self.context_variants.values())) > 1

    def divergence_report(self) -> str:
        """生成概念分歧自然语言报告。"""
        if not self.has_divergence():
            return f"概念 '{self.concept}' 在各来源中一致。"
        lines = [f"概念 '{self.concept}' 存在语境分歧："]
        for source, ctx in self.context_variants.items():
            lines.append(f"  · {source}: {ctx}")
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════
# § 4 · N9R20ConceptNode — 上下文感知概念节点
# ════════════════════════════════════════════════════════════════════


@dataclass
class N9R20ConceptNode:
    """
    上下文感知的概念节点。

    与传统术语节点不同，N9R20ConceptNode：
    - 支持同一概念在不同上下文中的变体（如"空"在佛教/哲学中的差异）
    - 携带来源追踪（N9R20ConceptProvenance）
    - 支持语义边权重的动态更新

    兼容旧版 ConceptNode / N9R20TermNode 格式。
    """

    term: str
    edges: Dict[str, float] = field(default_factory=dict)  # 邻接概念 → 权重
    source_session: str = ""
    confidence: float = 0.7
    added_timestamp: float = field(default_factory=time.time)

    # ── 9R-2.0 扩展字段 ──
    context_variants: Dict[str, str] = field(
        default_factory=dict
    )  # source → context_hint
    provenance: Optional[N9R20ConceptProvenance] = None

    def __post_init__(self) -> None:
        if self.provenance is None:
            self.provenance = N9R20ConceptProvenance(concept=self.term)

    def add_edge(self, term: str, weight: float) -> None:
        """添加或更新一条语义边。"""
        self.edges[term] = weight

    def remove_edge(self, term: str) -> None:
        """移除一条语义边。"""
        self.edges.pop(term, None)

    def add_context_variant(self, source: str, context_hint: str) -> None:
        """为一个来源添加上下文描述。"""
        self.context_variants[source] = context_hint
        if self.provenance:
            self.provenance.touch(source, context_hint)

    def has_divergence(self) -> bool:
        """检测概念在不同来源中是否存在歧义/分歧。"""
        if self.provenance:
            return self.provenance.has_divergence()
        return len(set(self.context_variants.values())) > 1

    # ── 兼容旧版序列化 ──────────────────────────────────────────

    def to_legacy_dict(self) -> Dict[str, Any]:
        """导出为旧版 TermNode 格式。"""
        return {
            "term": self.term,
            "edges": dict(self.edges),
            "source_session": self.source_session,
            "confidence": self.confidence,
            "added_timestamp": self.added_timestamp,
        }

    @classmethod
    def from_legacy_dict(cls, data: Dict[str, Any]) -> "N9R20ConceptNode":
        """从旧版 TermNode 格式导入。"""
        return cls(
            term=data.get("term", ""),
            edges=data.get("edges", {}),
            source_session=data.get("source_session", ""),
            confidence=data.get("confidence", 0.7),
            added_timestamp=data.get("added_timestamp", time.time()),
        )


# ════════════════════════════════════════════════════════════════════
# § 5 · N9R20SkillBookManifest — 向后兼容的 manifest
# ════════════════════════════════════════════════════════════════════


@dataclass
class N9R20SkillBookManifest:
    """
    技能书清单 — 完全兼容旧版 SkillBookManifest + 9R-2.0 扩展。

    旧版兼容字段：
        - skill_book_id: 技能书唯一 ID
        - book_title: 书名
        - concept_count: 概念数量
        - difficulty_breakdown: 难度分布（旧版格式）

    9R-2.0 扩展字段：
        - production_history: 生产记录列表
        - concept_nodes: 上下文感知概念节点
        - metadata: 任意扩展元数据
    """

    # ── 旧版兼容字段 ──
    skill_book_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    book_title: str = ""
    concept_count: int = 0
    difficulty_breakdown: N9R20DifficultyBreakdown = field(
        default_factory=N9R20DifficultyBreakdown
    )

    # ── 9R-2.0 扩展字段 ──
    production_history: List[N9R20ProductionRecord] = field(default_factory=list)
    concept_nodes: Dict[str, N9R20ConceptNode] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ── 统计指标 ──
    total_calls: int = 0
    success_rate: float = 0.0
    average_retention: float = 0.0
    average_compression_ratio: float = 0.0
    last_updated: float = field(default_factory=time.time)

    # ── 序列化 ──────────────────────────────────────────────────

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        导出为旧版 SkillBookManifest 格式（完全兼容）。

        旧版期望字段：skill_book_id, book_title, concept_count,
        difficulty_breakdown
        """
        return {
            "skill_book_id": self.skill_book_id,
            "book_title": self.book_title,
            "concept_count": self.concept_count,
            "difficulty_breakdown": self.difficulty_breakdown.to_legacy_dict(),
        }

    @classmethod
    def from_legacy_dict(cls, data: Dict[str, Any]) -> "N9R20SkillBookManifest":
        """
        从旧版 SkillBookManifest dict 导入。

        自动处理缺失字段，填充 9R-2.0 扩展为默认值。
        """
        breakdown_data = data.get("difficulty_breakdown", {})
        breakdown = (
            N9R20DifficultyBreakdown.from_legacy_dict(breakdown_data)
            if breakdown_data
            else N9R20DifficultyBreakdown()
        )

        return cls(
            skill_book_id=data.get("skill_book_id", uuid.uuid4().hex[:16]),
            book_title=data.get("book_title", ""),
            concept_count=data.get("concept_count", 0),
            difficulty_breakdown=breakdown,
        )

    def to_json(self) -> str:
        """导出为 JSON 字符串。"""
        return json.dumps(self.to_legacy_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "N9R20SkillBookManifest":
        """从 JSON 字符串导入。"""
        return cls.from_legacy_dict(json.loads(json_str))


# ════════════════════════════════════════════════════════════════════
# § 6 · N9R20SkillBookImporter — 导入/合并/迁移旧格式
# ════════════════════════════════════════════════════════════════════


class N9R20SkillBookImporter:
    """
    旧版 SkillBook 导入器。

    职责：
    1. 从旧版 dict / JSON 导入 SkillBookManifest
    2. 冲突检测：同一 skill_book_id 已存在时的合并策略
    3. 迁移：将旧版 ProductionRecord / ConceptNode 批量转换为新版格式
    """

    @staticmethod
    def import_manifest(data: Dict[str, Any]) -> N9R20SkillBookManifest:
        """
        导入单个 manifest。

        参数：
            data: 旧版 SkillBookManifest dict 格式

        返回：
            N9R20SkillBookManifest 实例
        """
        return N9R20SkillBookManifest.from_legacy_dict(data)

    @staticmethod
    def import_manifests(
        data_list: List[Dict[str, Any]],
    ) -> List[N9R20SkillBookManifest]:
        """
        批量导入 manifest 列表。

        参数：
            data_list: 旧版 SkillBookManifest dict 列表

        返回：
            N9R20SkillBookManifest 实例列表
        """
        return [N9R20SkillBookManifest.from_legacy_dict(d) for d in data_list]

    @staticmethod
    def import_production_records(
        data_list: List[Dict[str, Any]],
    ) -> List[N9R20ProductionRecord]:
        """
        批量导入旧版 ProductionRecord。

        参数：
            data_list: 旧版 ProductionRecord dict 列表

        返回：
            N9R20ProductionRecord 实例列表
        """
        return [N9R20ProductionRecord.from_legacy_dict(d) for d in data_list]

    @staticmethod
    def import_concept_nodes(
        data_dict: Dict[str, Dict[str, Any]],
    ) -> Dict[str, N9R20ConceptNode]:
        """
        批量导入旧版 ConceptNode 映射。

        参数：
            data_dict: {term: {concept_node_dict}}

        返回：
            {term: N9R20ConceptNode} 映射
        """
        return {
            term: N9R20ConceptNode.from_legacy_dict(node_data)
            for term, node_data in data_dict.items()
        }

    @staticmethod
    def merge_manifests(
        existing: N9R20SkillBookManifest,
        incoming: N9R20SkillBookManifest,
        strategy: str = "update",
    ) -> Tuple[N9R20SkillBookManifest, List[str]]:
        """
        合并两个 manifest。

        策略：
            - "update": incoming 覆盖 existing 的非空字段
            - "keep": existing 优先，仅填充缺失字段
            - "reject": 冲突时拒绝合并，返回冲突列表

        参数：
            existing: 已有 manifest
            incoming: 新导入 manifest
            strategy: 合并策略（"update" | "keep" | "reject"）

        返回：
            (merged_manifest, conflicts_list)
            conflicts_list 描述被拒绝/冲突的字段名
        """
        conflicts: List[str] = []

        if strategy == "reject":
            # 检测冲突
            if (
                incoming.book_title
                and existing.book_title
                and incoming.book_title != existing.book_title
            ):
                conflicts.append("book_title")
            if incoming.concept_count != existing.concept_count:
                conflicts.append("concept_count")
            if conflicts:
                return existing, conflicts

        if strategy == "keep":
            # existing 优先
            merged = N9R20SkillBookManifest(
                skill_book_id=existing.skill_book_id,
                book_title=existing.book_title or incoming.book_title,
                concept_count=max(existing.concept_count, incoming.concept_count),
            )
        else:  # "update"
            merged = N9R20SkillBookManifest(
                skill_book_id=existing.skill_book_id,
                book_title=incoming.book_title or existing.book_title,
                concept_count=max(existing.concept_count, incoming.concept_count),
            )

        # 合并难度分布（累加）
        for bucket in ("easy", "medium", "hard"):
            ex_total, ex_succ = getattr(existing.difficulty_breakdown, bucket)
            in_total, in_succ = getattr(incoming.difficulty_breakdown, bucket)
            setattr(
                merged.difficulty_breakdown,
                bucket,
                (ex_total + in_total, ex_succ + in_succ),
            )

        # 合并生产历史（去重 record_id）
        existing_ids: Set[str] = {r.record_id for r in existing.production_history}
        merged.production_history = list(existing.production_history)
        for record in incoming.production_history:
            if record.record_id not in existing_ids:
                merged.production_history.append(record)

        # 合并概念节点（update 策略：incoming 覆盖同名节点）
        merged.concept_nodes = dict(existing.concept_nodes)
        merged.concept_nodes.update(incoming.concept_nodes)

        merged.total_calls = existing.total_calls + incoming.total_calls
        merged.last_updated = time.time()

        return merged, conflicts

    @staticmethod
    def migrate_from_json_str(json_str: str) -> N9R20SkillBookManifest:
        """
        从旧版 JSON 字符串一键迁移。

        自动检测并处理旧版格式的所有字段。
        """
        data = json.loads(json_str)
        return N9R20SkillBookManifest.from_legacy_dict(data)


# ════════════════════════════════════════════════════════════════════
# § 7 · N9R20SkillBookExporter — 导出到旧格式
# ════════════════════════════════════════════════════════════════════


class N9R20SkillBookExporter:
    """
    技能书导出器。

    将 9R-2.0 格式导出为旧版兼容格式，确保下游消费者无缝衔接。
    """

    @staticmethod
    def export_manifest(manifest: N9R20SkillBookManifest) -> Dict[str, Any]:
        """
        导出 manifest 为旧版 dict 格式。

        包含旧版必需字段 + 9R-2.0 扩展（嵌套为旧版子格式）。
        """
        result = manifest.to_legacy_dict()

        # 附加生产记录（旧版格式）
        result["production_history"] = [
            r.to_legacy_dict() for r in manifest.production_history
        ]

        # 附加概念节点（旧版格式）
        result["concept_nodes"] = {
            term: node.to_legacy_dict()
            for term, node in manifest.concept_nodes.items()
        }

        # 附加统计指标
        result["stats"] = {
            "total_calls": manifest.total_calls,
            "success_rate": manifest.success_rate,
            "average_retention": manifest.average_retention,
            "average_compression_ratio": manifest.average_compression_ratio,
        }

        return result

    @staticmethod
    def export_manifests(
        manifests: List[N9R20SkillBookManifest],
    ) -> List[Dict[str, Any]]:
        """批量导出 manifest 列表。"""
        return [
            N9R20SkillBookExporter.export_manifest(m) for m in manifests
        ]

    @staticmethod
    def export_to_json(manifest: N9R20SkillBookManifest, indent: int = 2) -> str:
        """
        导出为 JSON 字符串（向后兼容格式）。

        参数：
            manifest: 要导出的 manifest
            indent: JSON 缩进，默认 2

        返回：
            JSON 字符串
        """
        return json.dumps(
            N9R20SkillBookExporter.export_manifest(manifest),
            ensure_ascii=False,
            indent=indent,
        )

    @staticmethod
    def export_to_json_lines(
        manifests: List[N9R20SkillBookManifest],
    ) -> str:
        """
        批量导出为 JSON Lines 格式（每行一个 manifest）。

        参数：
            manifests: manifest 列表

        返回：
            JSON Lines 字符串
        """
        lines = [
            json.dumps(
                N9R20SkillBookExporter.export_manifest(m),
                ensure_ascii=False,
            )
            for m in manifests
        ]
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════
# § 8 · 全局单例
# ════════════════════════════════════════════════════════════════════

#: 全局导入器单例
n9r20_skillbook_importer: N9R20SkillBookImporter = N9R20SkillBookImporter()

#: 全局导出器单例
n9r20_skillbook_exporter: N9R20SkillBookExporter = N9R20SkillBookExporter()


__all__ = [
    "N9R20ProductionRecord",
    "N9R20DifficultyBreakdown",
    "N9R20ConceptProvenance",
    "N9R20ConceptNode",
    "N9R20SkillBookManifest",
    "N9R20SkillBookImporter",
    "N9R20SkillBookExporter",
    "n9r20_skillbook_importer",
    "n9r20_skillbook_exporter",
]
