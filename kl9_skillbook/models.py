"""Data models for KL9-RHIZOME skillbook absorption protocol v1.1."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProductionRecord:
    """制作记录 — 必填字段反映学习过程的完整性."""
    rounds_completed: int           # ≥1
    verification_method: str        # "none"|"spot-check"|"full-reread"|"external"
    counter_perspectives: list[str] # 反视角列表
    total_hours: float              # 投入小时数


@dataclass
class DifficultyBreakdown:
    """难度细分 — LLM 评估的四维度."""
    style_density: float      # 0-100 风格密度
    info_density: float       # 0-100 信息密度
    viewpoint_novelty: float  # 0-100 观点创新
    citation_density: float   # 0-100 引用密度
    overall: float            # 0-100 四均值


@dataclass
class ConceptProvenance:
    source_skill_book: str
    quality_tier: int
    llm_source: str
    import_timestamp: int


@dataclass
class ConceptNode:
    concept_id: str
    name: str
    definition: str
    perspective_a: str
    perspective_b: str
    tension_score: float
    edges: list[str] = field(default_factory=list)
    provenance: Optional[ConceptProvenance] = None
    local_confidence: float = 1.0
    is_shadow: bool = False
    shadow_of: Optional[str] = None


@dataclass
class SkillBookManifest:
    skill_book_id: str
    version: str
    quality_tier: int           # deprecated v1.1, kept for backward compat
    llm_source: str
    kl9_version: str
    created_timestamp: int
    book_title: str
    concept_count: int
    extra: dict = field(default_factory=dict)

    # ── v1.1 新增字段 ──
    difficulty: float = 0.0             # 0-100 难度评分
    quality_score: float = 0.0          # 0-100 质量评分
    book_language: str = ""             # 书籍语言: "zh"/"en"/"de"/"fr"/"other"
    production_record: Optional[ProductionRecord] = None
    difficulty_breakdown: Optional[DifficultyBreakdown] = None


@dataclass
class CollisionReport:
    exact_collisions: list   # list[tuple[str, str]]
    near_identical: list     # list[tuple[str, str, float]]
    nearby_warnings: list    # list[tuple[str, str, float]]
    nodes_added: int
    nodes_bifurcated: int
    warnings: list[str]
