"""
KL9-RHIZOME v2.0 · 核心数据结构
DualState / Tension / Perspective / RoutingDecision
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class PerspectiveType(Enum):
    """视角类型"""
    THEORETICAL = "theoretical"
    EMBODIED = "embodied"
    PRACTICAL = "practical"
    CRITICAL = "critical"


@dataclass
class Perspective:
    """认知视角 — A/B 二重性的一极"""
    name: str
    characteristics: List[str] = field(default_factory=list)
    key: str = ""
    perspective_type: PerspectiveType = PerspectiveType.THEORETICAL
    
    def __post_init__(self):
        if not self.key:
            self.key = self.name


@dataclass
class Tension:
    """结构性张力 — 两个不可调和视角之间的裂痕"""
    perspective_A: str = ""
    perspective_B: str = ""
    claim_A: str = ""
    claim_B: str = ""
    irreconcilable_points: List[str] = field(default_factory=list)
    tension_type: str = ""
    intensity: float = 0.5  # 张力强度 [0,1]


@dataclass
class DualState:
    """KL9-RHIZOME v2.0 核心状态容器
    
    设计原则：
    1. 只保留当前状态，历史移至 Memory
    2. 压缩相关字段提升为一级字段
    3. 四模编码状态显式化
    """
    # ═══ 核心字段 ═══
    query: str = ""
    session_id: str = ""
    
    # ═══ 双视角 ═══
    perspective_A: Optional[Perspective] = None
    perspective_B: Optional[Perspective] = None
    tension: Optional[Tension] = None  # A/B 之间的张力
    
    # ═══ 压缩状态 ═══
    fold_depth: int = 0  # 当前折叠深度
    target_fold_depth: int = 4  # 动态分配的目标深度 (2-9)
    compression_ratio: float = 1.0  # 当前压缩率
    target_compression_ratio: float = 2.5  # 目标压缩率 (2.0-2.5)
    semantic_retention: float = 1.0  # 语义保留率
    
    # ═══ 四模编码状态 ═══
    current_mode: str = ""  # "construct" | "deconstruct" | "validate" | "interrupt"
    mode_sequence: List[str] = field(default_factory=list)
    
    # ═══ 决断状态 ═══
    decision_ready: bool = False  # 是否可输出决断
    compressed_output: str = ""  # 压缩后的输出
    
    # ═══ 元信息 ═══
    source_skill: str = "compression-core"
    timestamp: float = 0.0
    
    def __post_init__(self):
        import time
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class RoutingDecision:
    """路由决策"""
    path: str = "standard"  # "specialized" | "standard"
    confidence: float = 0.0
    difficulty: float = 0.5
    target_fold_depth: int = 4
    target_compression_ratio: float = 2.5
    urgency: float = 0.5
    
    # ═══ 动态评估 ═══
    concept_density: float = 0.0
    tension_factor: float = 0.0
    length_factor: float = 0.0


@dataclass
class CompressedOutput:
    """压缩输出"""
    output: str = ""
    compression_ratio: float = 1.0
    semantic_retention: float = 1.0
    fold_depth: int = 0
    mode_sequence: List[str] = field(default_factory=list)
    decision_ready: bool = False
    
    # ═══ 元信息 ═══
    session_id: str = ""
    timestamp: float = 0.0
    
    def __post_init__(self):
        import time
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class SkillBook:
    """技能书"""
    skill_name: str = ""
    total_calls: int = 0
    success_rate: float = 0.0
    average_retention: float = 0.0
    average_compression_ratio: float = 0.0
    last_updated: float = 0.0
    
    def __post_init__(self):
        import time
        if self.last_updated == 0.0:
            self.last_updated = time.time()


@dataclass
class TermNode:
    """术语节点"""
    term: str = ""
    edges: Dict[str, float] = field(default_factory=dict)
    source_session: str = ""
    confidence: float = 0.7
    added_timestamp: float = 0.0
    
    def __post_init__(self):
        import time
        if self.added_timestamp == 0.0:
            self.added_timestamp = time.time()
