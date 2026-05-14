"""
KL9-RHIZOME 核心数据结构。
DualState / Tension / Perspective / FoldWeight / DifficultySpectrum / SuspensionAssessment
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class Perspective:
    """认知视角 — A/B 二重性的一极。"""
    name: str
    characteristics: List[str] = field(default_factory=list)
    key: str = ""
    
    def __post_init__(self):
        if not self.key:
            self.key = self.name


@dataclass
class Tension:
    """结构性张力 — 两个不可调和视角之间的裂痕。"""
    perspective_A: str = ""
    perspective_B: str = ""
    claim_A: str = ""
    claim_B: str = ""
    irreconcilable_points: List[str] = field(default_factory=list)
    tension_type: str = ""


@dataclass
class DualState:
    """二重态 — KL9-RHIZOME 的核心状态容器。
    
    A 和 B 平等且不可调和。suspended=True 是可表达的前提。
    forced=True 表示达到 max_fold_depth 仍未自然悬置。
    
    mode="translation" 时，source_text/term_bindings 参与折叠。
    """
    query: str = ""
    perspective_A: Optional[Perspective] = None
    perspective_B: Optional[Perspective] = None
    activated_dialogue: List[Dict] = field(default_factory=list)
    tension: Optional[Tension] = None
    tension_type: str = ""
    suspended: bool = False
    forced: bool = False
    fold_depth: int = 0
    max_fold_depth: int = 2
    source_skill: str = "kailejiu-orchestrator"
    mode: str = "default"
    source_text: str = ""
    target_lang: str = "zh"
    term_bindings: Dict[str, str] = field(default_factory=dict)


@dataclass
class FoldWeight:
    """二重折叠权重 — 连续可逆的权重系统。
    
    base: 基础权重 [0, 1]
    correction_vector: 修正向量，表示各维度的偏移
    reversibility: 可逆性 [0, 1]，越高表示越容易回滚
    """
    base: float = 0.5
    correction_vector: Dict[str, float] = field(default_factory=dict)
    reversibility: float = 0.8
    
    def effective_weight(self) -> float:
        """计算有效权重 = base + Σ(correction_vector)。"""
        correction = sum(self.correction_vector.values())
        raw = self.base + correction
        return max(0.0, min(1.0, raw))
    
    def fold(self, delta: float, dimension: str = "default") -> 'FoldWeight':
        """折叠：在指定维度上施加修正。"""
        new_cv = dict(self.correction_vector)
        new_cv[dimension] = new_cv.get(dimension, 0.0) + delta
        return FoldWeight(
            base=self.base,
            correction_vector=new_cv,
            reversibility=self.reversibility
        )
    
    def unfold(self, dimension: str = "default") -> 'FoldWeight':
        """展开：撤销指定维度的修正（按 reversibility 比例）。"""
        new_cv = dict(self.correction_vector)
        if dimension in new_cv:
            new_cv[dimension] *= (1.0 - self.reversibility)
        return FoldWeight(
            base=self.base,
            correction_vector=new_cv,
            reversibility=self.reversibility
        )
    
    def tension_strength(self) -> float:
        """张力强度 = |effective_weight - 0.5| * 2，越远离中性越强。"""
        return abs(self.effective_weight() - 0.5) * 2.0


@dataclass
class DifficultySpectrum:
    """连续难度谱 (0.0–1.0)，三维分解。"""
    value: float = 0.5
    tension_component: float = 0.33
    breadth_component: float = 0.33
    depth_component: float = 0.33
    
    @classmethod
    def from_fold_weights_and_graph(cls, fold_weight: FoldWeight, graph_density: float = 0.5):
        """从折叠权重和图密度计算难度谱。"""
        tension = fold_weight.tension_strength()
        breadth = graph_density
        depth = 1.0 - fold_weight.reversibility
        value = (tension + breadth + depth) / 3.0
        return cls(
            value=round(value, 4),
            tension_component=round(tension, 4),
            breadth_component=round(breadth, 4),
            depth_component=round(depth, 4)
        )


@dataclass
class SuspensionAssessment:
    """悬置评估结果。"""
    can_express: bool = False
    quality: str = "insufficient"  # "genuine" | "forced" | "insufficient" | "pressure_relaxed"
    improvement_hints: List[str] = field(default_factory=list)


def load_perspective(key: str) -> Perspective:
    """从 perspective_types 加载视角实例。
    
    key 格式: "family.subtype"，如 "temporal.human"、"existential.immediate"。
    """
    try:
        from perspective_types import PERSPECTIVE_TYPES
    except ImportError:
        return Perspective(name=key, characteristics=[key])
    
    parts = key.split(".", 1)
    if len(parts) == 2:
        family, subtype = parts
        family_data = PERSPECTIVE_TYPES.get(family, {})
        subtype_data = family_data.get(subtype, {})
        characteristics = subtype_data.get("characteristics", [key])
        return Perspective(name=key, characteristics=characteristics, key=key)
    else:
        return Perspective(name=key, characteristics=[key], key=key)
