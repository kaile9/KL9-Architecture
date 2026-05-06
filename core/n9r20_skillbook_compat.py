"""
9R-2.0 RHIZOME · 旧版 SkillBook 兼容层
────────────────────────────────────────────────────────
向下兼容 9R-1.5 (kaile9/KL9-Architecture) 的 SkillBook 格式。

设计原则：
  1. 完全兼容旧版 SkillBookManifest 字段
     (skill_book_id, book_title, concept_count, difficulty_breakdown)
  2. 扩展新版统计字段
     (total_calls, success_rate, average_retention, average_compression_ratio)
  3. 支持冲突检测与迁移
  4. 概念节点引入 context_variants（上下文变体），
     支持人文社科中同一概念在不同思想家/文本中的差异

核心类：
  N9R20ProductionRecord    — 制作记录（扩展字段）
  N9R20DifficultyBreakdown — 难度分解
  N9R20ConceptProvenance   — 概念来源追溯
  N9R20ConceptNode         — 概念节点（含上下文变体）
  N9R20SkillBookManifest   — 完全兼容旧版 + 扩展
  N9R20SkillBookImporter   — 导入 + 冲突检测 + 迁移
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from core.n9r20_structures import N9R20SkillBook
from core.n9r20_config import n9r20_compression_config


# ════════════════════════════════════════════════════════════════════
# § 1 · 制作记录（扩展字段）
# ════════════════════════════════════════════════════════════════════

@dataclass
class N9R20ProductionRecord:
    """
    单次制作的完整记录。

    记录一次概念/输出从产生到验证的完整过程，
    比旧版 ProductionRecord 增加了压缩率、折叠深度等字段。
    """

    # ── 旧版字段 ──────────────────────────────────────────
    concept: str = ""               # 产生的概念
    source_text: str = ""           # 来源文本
    difficulty: float = 0.5         # 制作难度 [0, 1]
    success: bool = False           # 制作是否成功

    # ── 9R-2.0 扩展字段 ───────────────────────────────────
    compression_ratio: float = 1.0       # 压缩率
    fold_depth: int = 0                  # 折叠深度
    semantic_retention: float = 1.0      # 语义保留率
    mode_sequence: List[str] = field(default_factory=list)  # 四模编码序列
    iteration_count: int = 1             # 迭代次数
    session_id: str = ""                 # 会话 ID
    timestamp: float = field(default_factory=time.time)


# ════════════════════════════════════════════════════════════════════
# § 2 · 难度分解
# ════════════════════════════════════════════════════════════════════

@dataclass
class N9R20DifficultyBreakdown:
    """
    难度分解 — 与旧版完全兼容。

    将综合难度拆解为各维度的贡献值。
    """

    overall: float = 0.5               # 综合难度 [0, 1]
    concept_complexity: float = 0.5    # 概念复杂度
    tension_intensity: float = 0.5     # 张力强度
    cognitive_load: float = 0.5        # 认知负载
    compression_potential: float = 0.5 # 压缩潜力

    def to_dict(self) -> Dict[str, float]:
        """输出为字典（与旧版序列化兼容）。"""
        return {
            "overall": self.overall,
            "concept_complexity": self.concept_complexity,
            "tension_intensity": self.tension_intensity,
            "cognitive_load": self.cognitive_load,
            "compression_potential": self.compression_potential,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "N9R20DifficultyBreakdown":
        """从字典恢复（与旧版反序列化兼容）。"""
        return cls(
            overall=data.get("overall", 0.5),
            concept_complexity=data.get("concept_complexity", 0.5),
            tension_intensity=data.get("tension_intensity", 0.5),
            cognitive_load=data.get("cognitive_load", 0.5),
            compression_potential=data.get("compression_potential", 0.5),
        )


# ════════════════════════════════════════════════════════════════════
# § 3 · 概念来源
# ════════════════════════════════════════════════════════════════════

@dataclass
class N9R20ConceptProvenance:
    """
    概念来源追溯。

    记录一个概念从哪个文本、哪个思想传统中提取，
    支持人文社科概念的多源追溯。
    """

    concept: str = ""                     # 概念名称
    source_text: str = ""                 # 来源文本
    source_tradition: str = ""            # 思想传统（如 "佛学中观"、"现象学"）
    source_thinker: str = ""              # 相关思想家（如 "龙树"、"胡塞尔"）
    context_note: str = ""                # 上下文说明
    extraction_method: str = "auto"       # 提取方式（"auto" | "manual" | "llm"）
    confidence: float = 0.7               # 提取置信度
    timestamp: float = field(default_factory=time.time)


# ════════════════════════════════════════════════════════════════════
# § 4 · 概念节点（含上下文变体）
# ════════════════════════════════════════════════════════════════════

@dataclass
class N9R20ConceptNode:
    """
    概念节点 — 支持上下文变体。

    人文社科中同一概念在不同思想家/文本中有差异化的含义。
    context_variants 字段存储这些差异定义，
    系统根据上下文独立判断使用哪个变体。

    示例：
      概念 "空" 在龙树《中论》和世亲《俱舍论》中含义不同，
      各自存储为独立的 context_variant。
    """

    # ── 核心标识 ──────────────────────────────────────────
    concept: str = ""                          # 概念名称（规范形式）
    canonical_definition: str = ""             # 规范定义

    # ── 上下文变体 ────────────────────────────────────────
    # 字典：上下文键 → 该上下文中的特定含义
    # 上下文键格式示例："龙树/中论"、"胡塞尔/观念I"
    context_variants: Dict[str, str] = field(default_factory=dict)

    # ── 元信息 ───────────────────────────────────────────
    provenance: List[N9R20ConceptProvenance] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    tension_concepts: List[str] = field(default_factory=list)  # 与此概念有张力的概念

    # ── 统计 ─────────────────────────────────────────────
    occurrence_count: int = 0                  # 出现次数
    confidence: float = 0.7                    # 置信度
    last_updated: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)

    def get_definition(self, context_key: Optional[str] = None) -> str:
        """
        获取概念定义。

        如果提供 context_key 且存在于 context_variants 中，
        返回该上下文特定定义；否则返回规范定义。

        Args:
            context_key: 上下文键（如 "龙树/中论"），None 时返回规范定义

        Returns:
            概念定义字符串
        """
        if context_key and context_key in self.context_variants:
            return self.context_variants[context_key]
        return self.canonical_definition

    def add_variant(self, context_key: str, definition: str) -> None:
        """
        添加或更新上下文变体。

        Args:
            context_key: 上下文键
            definition:  该上下文中的概念定义
        """
        self.context_variants[context_key] = definition
        self.last_updated = time.time()

    def has_conflict_with(self, other: "N9R20ConceptNode") -> bool:
        """
        检测与另一概念节点是否存在定义冲突。

        冲突判定：同名概念但规范定义不同（字符串级别简单比较）。

        Args:
            other: 另一概念节点

        Returns:
            是否存在冲突
        """
        if self.concept != other.concept:
            return False
        return self.canonical_definition != other.canonical_definition

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（兼容导出）。"""
        return {
            "concept": self.concept,
            "canonical_definition": self.canonical_definition,
            "context_variants": self.context_variants,
            "provenance": [
                {
                    "concept": p.concept,
                    "source_text": p.source_text,
                    "source_tradition": p.source_tradition,
                    "source_thinker": p.source_thinker,
                    "context_note": p.context_note,
                    "extraction_method": p.extraction_method,
                    "confidence": p.confidence,
                    "timestamp": p.timestamp,
                }
                for p in self.provenance
            ],
            "related_concepts": self.related_concepts,
            "tension_concepts": self.tension_concepts,
            "occurrence_count": self.occurrence_count,
            "confidence": self.confidence,
            "last_updated": self.last_updated,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "N9R20ConceptNode":
        """从字典恢复（兼容导入）。"""
        node = cls(
            concept=data.get("concept", ""),
            canonical_definition=data.get("canonical_definition", ""),
            context_variants=data.get("context_variants", {}),
            related_concepts=data.get("related_concepts", []),
            tension_concepts=data.get("tension_concepts", []),
            occurrence_count=data.get("occurrence_count", 0),
            confidence=data.get("confidence", 0.7),
            last_updated=data.get("last_updated", time.time()),
            created_at=data.get("created_at", time.time()),
        )
        node.provenance = [
            N9R20ConceptProvenance(**p)
            for p in data.get("provenance", [])
        ]
        return node


# ════════════════════════════════════════════════════════════════════
# § 5 · SkillBook 清单（完全兼容旧版）
# ════════════════════════════════════════════════════════════════════

@dataclass
class N9R20SkillBookManifest:
    """
    SkillBook 清单 — 完全兼容 9R-1.5 旧版格式。

    旧版字段（完全兼容）：
      skill_book_id, book_title, concept_count, difficulty_breakdown

    9R-2.0 扩展字段（新增）：
      total_calls, success_rate, average_retention,
      average_compression_ratio, concepts
    """

    # ── 旧版兼容字段 ──────────────────────────────────────
    skill_book_id: str = ""                     # 技能书唯一 ID
    book_title: str = ""                        # 书名/标题
    concept_count: int = 0                      # 包含的概念数量
    difficulty_breakdown: N9R20DifficultyBreakdown = field(
        default_factory=N9R20DifficultyBreakdown
    )

    # ── 9R-2.0 扩展字段 ──────────────────────────────────
    total_calls: int = 0                        # 总调用次数
    success_rate: float = 0.0                   # 成功率
    average_retention: float = 0.0              # 平均语义保留率
    average_compression_ratio: float = 0.0      # 平均压缩率
    last_updated: float = field(default_factory=time.time)

    # ── 扩展数据 ─────────────────────────────────────────
    concepts: List[N9R20ConceptNode] = field(default_factory=list)
    production_history: List[N9R20ProductionRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "9R-1.5"                     # 来源版本标识

    def to_old_format(self) -> Dict[str, Any]:
        """
        导出为旧版兼容的字典格式。

        Returns:
            仅包含旧版字段的字典，可直接被 9R-1.5 读取。
        """
        return {
            "skill_book_id": self.skill_book_id,
            "book_title": self.book_title,
            "concept_count": self.concept_count,
            "difficulty_breakdown": self.difficulty_breakdown.to_dict(),
        }

    def to_full_format(self) -> Dict[str, Any]:
        """
        导出为完整字典格式（含扩展字段）。

        Returns:
            包含所有字段的字典。
        """
        return {
            "skill_book_id": self.skill_book_id,
            "book_title": self.book_title,
            "concept_count": self.concept_count,
            "difficulty_breakdown": self.difficulty_breakdown.to_dict(),
            # 9R-2.0 扩展
            "total_calls": self.total_calls,
            "success_rate": self.success_rate,
            "average_retention": self.average_retention,
            "average_compression_ratio": self.average_compression_ratio,
            "last_updated": self.last_updated,
            "concepts": [c.to_dict() for c in self.concepts],
            "production_history": [
                {
                    "concept": r.concept,
                    "source_text": r.source_text,
                    "difficulty": r.difficulty,
                    "success": r.success,
                    "compression_ratio": r.compression_ratio,
                    "fold_depth": r.fold_depth,
                    "semantic_retention": r.semantic_retention,
                    "session_id": r.session_id,
                    "timestamp": r.timestamp,
                }
                for r in self.production_history
            ],
            "metadata": self.metadata,
            "version": "9R-2.0",
        }

    @classmethod
    def from_old_format(cls, data: Dict[str, Any]) -> "N9R20SkillBookManifest":
        """
        从旧版 9R-1.5 字典格式加载。

        Args:
            data: 旧版格式字典

        Returns:
            新的 N9R20SkillBookManifest 实例（扩展字段使用默认值）
        """
        breakdown_data = data.get("difficulty_breakdown", {})
        if isinstance(breakdown_data, dict):
            breakdown = N9R20DifficultyBreakdown.from_dict(breakdown_data)
        else:
            breakdown = N9R20DifficultyBreakdown()

        return cls(
            skill_book_id=data.get("skill_book_id", ""),
            book_title=data.get("book_title", ""),
            concept_count=data.get("concept_count", 0),
            difficulty_breakdown=breakdown,
            version="9R-1.5",
        )

    def sync_to_skill_book(self) -> N9R20SkillBook:
        """
        将清单中的统计信息同步到 N9R20SkillBook（运行时技能书）。

        Returns:
            N9R20SkillBook 实例
        """
        return N9R20SkillBook(
            skill_name=self.skill_book_id,
            total_calls=self.total_calls,
            success_rate=self.success_rate,
            average_retention=self.average_retention,
            average_compression_ratio=self.average_compression_ratio,
            last_updated=self.last_updated,
        )

    def sync_from_skill_book(self, book: N9R20SkillBook) -> None:
        """
        从 N9R20SkillBook 同步统计信息到清单。

        Args:
            book: 运行时技能书实例
        """
        self.total_calls = book.total_calls
        self.success_rate = book.success_rate
        self.average_retention = book.average_retention
        self.average_compression_ratio = book.average_compression_ratio
        self.last_updated = book.last_updated


# ════════════════════════════════════════════════════════════════════
# § 6 · SkillBook 导入器
# ════════════════════════════════════════════════════════════════════

class N9R20SkillBookImporter:
    """
    旧版 SkillBook 导入器。

    职责：
    1. 从 9R-1.5 格式文件导入 SkillBook
    2. 检测同名 SkillBook 的字段冲突
    3. 执行迁移（从 9R-1.5 → 9R-2.0 格式）
    4. 生成冲突报告

    冲突类型：
    - FIELD_CONFLICT: 同名字段值不同
    - VERSION_MISMATCH: 版本声明与实际数据不符
    - MISSING_FIELD: 旧版缺少必要字段
    """

    class ConflictType(Enum):
        """冲突类型枚举"""
        FIELD_CONFLICT = "field_conflict"        # 字段值冲突
        VERSION_MISMATCH = "version_mismatch"    # 版本不匹配
        MISSING_FIELD = "missing_field"          # 缺少字段
        DUPLICATE_ID = "duplicate_id"            # 重复 ID

    @dataclass
    class ConflictReport:
        """单条冲突记录"""
        conflict_type: "N9R20SkillBookImporter.ConflictType"
        skill_book_id: str
        field_name: str = ""
        old_value: Any = None
        new_value: Any = None
        resolution: str = ""  # 解决方式描述

    def __init__(self):
        self._manifest_registry: Dict[str, N9R20SkillBookManifest] = {}
        self._conflicts: List[N9R20SkillBookImporter.ConflictReport] = []

    # ── 导入接口 ────────────────────────────────────────────

    def import_from_file(self, filepath: str) -> Optional[N9R20SkillBookManifest]:
        """
        从 JSON 文件导入 SkillBook 清单。

        自动检测格式版本并执行对应迁移。

        Args:
            filepath: JSON 文件路径

        Returns:
            导入的清单（None 表示导入失败）
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self.import_from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self._conflicts.append(self.ConflictReport(
                conflict_type=self.ConflictType.MISSING_FIELD,
                skill_book_id=filepath,
                resolution=f"文件读取失败: {e}",
            ))
            return None

    def import_from_dict(self, data: Dict[str, Any]) -> N9R20SkillBookManifest:
        """
        从字典导入 SkillBook 清单。

        Args:
            data: SkillBook 字典数据

        Returns:
            导入的清单
        """
        version = data.get("version", "9R-1.5")

        if version == "9R-1.5":
            manifest = N9R20SkillBookManifest.from_old_format(data)
            return self._migrate_to_2_0(manifest, data)
        else:
            # 假定已是 9R-2.0 格式
            return self._load_2_0_manifest(data)

    def import_batch(self, manifests: List[Dict[str, Any]]) -> List[N9R20SkillBookManifest]:
        """
        批量导入 SkillBook 清单。

        Args:
            manifests: 清单字典列表

        Returns:
            成功导入的清单列表
        """
        results = []
        for data in manifests:
            try:
                manifest = self.import_from_dict(data)
                if manifest:
                    results.append(manifest)
            except Exception as e:
                self._conflicts.append(self.ConflictReport(
                    conflict_type=self.ConflictType.MISSING_FIELD,
                    skill_book_id=data.get("skill_book_id", "unknown"),
                    resolution=f"导入异常: {e}",
                ))
        return results

    # ── 冲突检测 ────────────────────────────────────────────

    def detect_conflicts(
        self,
        existing: N9R20SkillBookManifest,
        incoming: N9R20SkillBookManifest,
    ) -> List[ConflictReport]:
        """
        检测两个 SkillBook 清单之间的冲突。

        Args:
            existing: 已存在的清单
            incoming: 待导入的清单

        Returns:
            冲突报告列表
        """
        conflicts = []

        # 检测 ID 重复
        if existing.skill_book_id == incoming.skill_book_id:
            # 逐字段比较
            if existing.book_title != incoming.book_title:
                conflicts.append(self.ConflictReport(
                    conflict_type=self.ConflictType.FIELD_CONFLICT,
                    skill_book_id=existing.skill_book_id,
                    field_name="book_title",
                    old_value=existing.book_title,
                    new_value=incoming.book_title,
                    resolution="保留已有标题，新标题存入 metadata",
                ))

            if existing.concept_count != incoming.concept_count:
                conflicts.append(self.ConflictReport(
                    conflict_type=self.ConflictType.FIELD_CONFLICT,
                    skill_book_id=existing.skill_book_id,
                    field_name="concept_count",
                    old_value=existing.concept_count,
                    new_value=incoming.concept_count,
                    resolution="使用最新值",
                ))

        return conflicts

    def resolve_conflicts(
        self,
        existing: N9R20SkillBookManifest,
        incoming: N9R20SkillBookManifest,
        conflicts: List[ConflictReport],
    ) -> N9R20SkillBookManifest:
        """
        自动解决冲突并合并两个清单。

        合并策略：
        - 保留 existing 的核心标识字段
        - 统计数据使用加权平均
        - 概念列表合并去重
        - 不同的标题存入 metadata

        Args:
            existing:  已存在的清单
            incoming:  待导入的清单
            conflicts: 冲突报告列表

        Returns:
            合并后的清单
        """
        merged = N9R20SkillBookManifest(
            skill_book_id=existing.skill_book_id,
            book_title=existing.book_title or incoming.book_title,
            concept_count=max(existing.concept_count, incoming.concept_count),
            difficulty_breakdown=existing.difficulty_breakdown,
            version="9R-2.0",
        )

        # 统计数据加权平均
        total_calls = existing.total_calls + incoming.total_calls
        if total_calls > 0:
            merged.total_calls = total_calls
            merged.success_rate = (
                existing.success_rate * existing.total_calls +
                incoming.success_rate * incoming.total_calls
            ) / total_calls
            merged.average_retention = (
                existing.average_retention * existing.total_calls +
                incoming.average_retention * incoming.total_calls
            ) / total_calls
            merged.average_compression_ratio = (
                existing.average_compression_ratio * existing.total_calls +
                incoming.average_compression_ratio * incoming.total_calls
            ) / total_calls

        # 合并概念列表（按名称去重）
        existing_concepts = {c.concept: c for c in existing.concepts}
        for c in incoming.concepts:
            if c.concept in existing_concepts:
                # 冲突检测：同名概念定义不同
                if existing_concepts[c.concept].has_conflict_with(c):
                    # 将 incoming 的定义作为上下文变体存储
                    incoming_key = f"imported/{incoming.skill_book_id}"
                    existing_concepts[c.concept].add_variant(
                        incoming_key,
                        c.canonical_definition,
                    )
                    # 同时合并变体
                    for ctx_key, definition in c.context_variants.items():
                        existing_concepts[c.concept].add_variant(
                            f"{incoming_key}/{ctx_key}",
                            definition,
                        )
            else:
                existing_concepts[c.concept] = c
        merged.concepts = list(existing_concepts.values())
        merged.concept_count = len(merged.concepts)

        # 存储冲突标题信息
        if existing.book_title != incoming.book_title and incoming.book_title:
            merged.metadata["alternate_title"] = incoming.book_title
            merged.metadata["conflict_resolved"] = True

        merged.last_updated = time.time()
        return merged

    # ── 迁移 ────────────────────────────────────────────────

    def _migrate_to_2_0(
        self,
        manifest: N9R20SkillBookManifest,
        raw_data: Dict[str, Any],
    ) -> N9R20SkillBookManifest:
        """
        执行 9R-1.5 → 9R-2.0 格式迁移。

        迁移操作：
        1. 更新版本号
        2. 初始化扩展字段默认值
        3. 转换旧概念格式为新 N9R20ConceptNode

        Args:
            manifest:  旧版格式解析出的清单
            raw_data:  原始 JSON 数据（可能包含非标准字段）

        Returns:
            迁移后的清单
        """
        manifest.version = "9R-2.0"

        # 尝试从旧版数据提取概念
        if "concepts" in raw_data:
            manifest.concepts = [
                self._convert_old_concept(c)
                for c in raw_data["concepts"]
            ]
            manifest.concept_count = len(manifest.concepts)

        return manifest

    def _load_2_0_manifest(self, data: Dict[str, Any]) -> N9R20SkillBookManifest:
        """
        加载 9R-2.0 格式清单。

        Args:
            data: 9R-2.0 格式字典

        Returns:
            清单实例
        """
        breakdown_data = data.get("difficulty_breakdown", {})
        breakdown = (
            N9R20DifficultyBreakdown.from_dict(breakdown_data)
            if isinstance(breakdown_data, dict)
            else N9R20DifficultyBreakdown()
        )

        return N9R20SkillBookManifest(
            skill_book_id=data.get("skill_book_id", ""),
            book_title=data.get("book_title", ""),
            concept_count=data.get("concept_count", 0),
            difficulty_breakdown=breakdown,
            total_calls=data.get("total_calls", 0),
            success_rate=data.get("success_rate", 0.0),
            average_retention=data.get("average_retention", 0.0),
            average_compression_ratio=data.get("average_compression_ratio", 0.0),
            last_updated=data.get("last_updated", time.time()),
            concepts=[
                N9R20ConceptNode.from_dict(c)
                for c in data.get("concepts", [])
            ],
            metadata=data.get("metadata", {}),
            version=data.get("version", "9R-2.0"),
        )

    def _convert_old_concept(self, old_data: Dict[str, Any]) -> N9R20ConceptNode:
        """
        将旧版概念格式转换为 N9R20ConceptNode。

        旧版概念格式可能是简单的 {name, definition} 或
        较复杂的字典格式。

        Args:
            old_data: 旧版概念数据

        Returns:
            新的 N9R20ConceptNode
        """
        return N9R20ConceptNode(
            concept=old_data.get("name", old_data.get("concept", "")),
            canonical_definition=old_data.get("definition", old_data.get("canonical_definition", "")),
            context_variants=old_data.get("context_variants", {}),
            related_concepts=old_data.get("related_concepts", old_data.get("relations", [])),
            confidence=old_data.get("confidence", 0.7),
        )

    # ── 查询接口 ────────────────────────────────────────────

    def get_manifest(self, skill_book_id: str) -> Optional[N9R20SkillBookManifest]:
        """获取已注册的清单。"""
        return self._manifest_registry.get(skill_book_id)

    def register(self, manifest: N9R20SkillBookManifest) -> None:
        """
        注册清单，自动检测与已存在清单的冲突。

        Args:
            manifest: 待注册的清单
        """
        existing = self._manifest_registry.get(manifest.skill_book_id)
        if existing is not None:
            conflicts = self.detect_conflicts(existing, manifest)
            self._conflicts.extend(conflicts)
            # 自动合并
            merged = self.resolve_conflicts(existing, manifest, conflicts)
            self._manifest_registry[manifest.skill_book_id] = merged
        else:
            self._manifest_registry[manifest.skill_book_id] = manifest

    @property
    def conflicts(self) -> List[ConflictReport]:
        """获取所有冲突报告。"""
        return list(self._conflicts)

    def clear_conflicts(self) -> None:
        """清除冲突报告。"""
        self._conflicts.clear()

    @property
    def manifest_count(self) -> int:
        """已注册的清单数量。"""
        return len(self._manifest_registry)
