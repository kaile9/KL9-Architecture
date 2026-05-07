"""
9R-2.0 RHIZOME · Core Module
核心数据结构 / 事件总线 / LLM评估器 / 配置常量 / 工具函数 / SkillBook 兼容层
生产日志 / LLM压缩器 / 概念冲突检测 / 用户配置
"""

from .n9r20_structures import (
    N9R20DualState,
    N9R20Tension,
    N9R20Perspective,
    N9R20PerspectiveType,
    N9R20RoutingDecision,
    N9R20CompressedOutput,
    N9R20SkillBook,
    N9R20TermNode,
)

from .n9r20_tension_bus import (
    N9R20TensionBus,
    N9R20TensionType,
    N9R20QueryDepth,
    N9R20TensionBusEvent,
    N9R20QueryEvent,
    N9R20CompressionTensionEvent,
    N9R20CompressionCompleteEvent,
    N9R20DualPerspectiveEvent,
    N9R20ConceptClusterEvent,
    N9R20SkillBookUpdateEvent,
    N9R20TensionSubscription,
    n9r20_bus,
)

from .n9r20_llm_evaluator import (
    N9R20LLMFoldEvaluator,
    N9R20LLMEvaluation,
    n9r20_llm_evaluator,
)

from .n9r20_config import (
    N9R20RoutingConfig,
    N9R20CompressionConfig,
    N9R20MemoryConfig,
    N9R20SemanticGraphConfig,
    N9R20TensionConfig,
    n9r20_routing_config,
    n9r20_compression_config,
    n9r20_memory_config,
    n9r20_semantic_graph_config,
    n9r20_tension_config,
)

from .n9r20_utils import (
    clamp,
    extract_terms,
    compute_concept_density,
    compute_tension_factor,
    compute_difficulty,
    compute_length_factor,
    allocate_fold_budget,
    compute_target_ratio,
)

from .n9r20_skillbook_compat import (
    N9R20ProductionRecord,
    N9R20DifficultyBreakdown,
    N9R20ConceptProvenance,
    N9R20ConceptNode,
    N9R20SkillBookManifest,
    N9R20SkillBookImporter,
    N9R20SkillBookExporter,
    n9r20_skillbook_importer,
    n9r20_skillbook_exporter,
)

# ═══ Phase 2 新增模块 ═══

from .n9r20_production_logger import (
    N9R20IterationLog,
    N9R20ProductionSession,
    N9R20ProductionLogger,
    n9r20_production_logger,
)

from .n9r20_llm_compressor import (
    N9R20CompressionResult,
    N9R20LLMCompressor,
    n9r20_llm_compressor,
)

from .n9r20_concept_conflict import (
    N9R20ConflictReport,
    N9R20ConceptConflictDetector,
    n9r20_conflict_detector,
)

from .n9r20_user_config import (
    N9R20UserConfig,
    N9R20UserConfigLoader,
    n9r20_user_config,
    n9r20_user_config_loader,
)

__all__ = [
    # Structures
    "N9R20DualState",
    "N9R20Tension",
    "N9R20Perspective",
    "N9R20PerspectiveType",
    "N9R20RoutingDecision",
    "N9R20CompressedOutput",
    "N9R20SkillBook",
    "N9R20TermNode",
    # TensionBus
    "N9R20TensionBus",
    "N9R20TensionType",
    "N9R20QueryDepth",
    "N9R20TensionBusEvent",
    "N9R20QueryEvent",
    "N9R20CompressionTensionEvent",
    "N9R20CompressionCompleteEvent",
    "N9R20DualPerspectiveEvent",
    "N9R20ConceptClusterEvent",
    "N9R20SkillBookUpdateEvent",
    "N9R20TensionSubscription",
    "n9r20_bus",
    # LLM Evaluator
    "N9R20LLMFoldEvaluator",
    "N9R20LLMEvaluation",
    "n9r20_llm_evaluator",
    # Config
    "N9R20RoutingConfig",
    "N9R20CompressionConfig",
    "N9R20MemoryConfig",
    "N9R20SemanticGraphConfig",
    "N9R20TensionConfig",
    "n9r20_routing_config",
    "n9r20_compression_config",
    "n9r20_memory_config",
    "n9r20_semantic_graph_config",
    "n9r20_tension_config",
    # Utils
    "clamp",
    "extract_terms",
    "compute_concept_density",
    "compute_tension_factor",
    "compute_difficulty",
    "compute_length_factor",
    "allocate_fold_budget",
    "compute_target_ratio",
    # SkillBook Compat
    "N9R20ProductionRecord",
    "N9R20DifficultyBreakdown",
    "N9R20ConceptProvenance",
    "N9R20ConceptNode",
    "N9R20SkillBookManifest",
    "N9R20SkillBookImporter",
    "N9R20SkillBookExporter",
    "n9r20_skillbook_importer",
    "n9r20_skillbook_exporter",
    # Phase 2 — Production Logger
    "N9R20IterationLog",
    "N9R20ProductionSession",
    "N9R20ProductionLogger",
    "n9r20_production_logger",
    # Phase 2 — LLM Compressor
    "N9R20CompressionResult",
    "N9R20LLMCompressor",
    "n9r20_llm_compressor",
    # Phase 2 — Concept Conflict Detector
    "N9R20ConflictReport",
    "N9R20ConceptConflictDetector",
    "n9r20_conflict_detector",
    # Phase 2 — User Config
    "N9R20UserConfig",
    "N9R20UserConfigLoader",
    "n9r20_user_config",
    "n9r20_user_config_loader",
]
