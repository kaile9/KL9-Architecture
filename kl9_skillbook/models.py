"""Data models for KL9-RHIZOME skillbook absorption protocol v1.0."""
from dataclasses import dataclass, field
from typing import Optional

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
    quality_tier: int
    llm_source: str
    kl9_version: str
    created_timestamp: int
    book_title: str
    concept_count: int
    extra: dict = field(default_factory=dict)

@dataclass
class CollisionReport:
    exact_collisions: list   # list[tuple[str, str]]
    near_identical: list     # list[tuple[str, str, float]]
    nearby_warnings: list    # list[tuple[str, str, float]]
    nodes_added: int
    nodes_bifurcated: int
    warnings: list[str]
