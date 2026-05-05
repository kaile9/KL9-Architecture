"""
KL9-RHIZOME v1.5 共享基础设施层 — 统一导出
=============================================

lib/ 下模块使用平级导入（目录在 sys.path 上即可），
此文件先确保路径正确，再导出所有公共接口。

导入方式：

    import sys
    sys.path.insert(0, 'os.path.dirname(os.path.abspath(__file__))')
    from lib_init import TensionBus, DualState, GraphBackend, ...

注意：为避免包内模块的平级导入冲突，
不将 lib/ 作为 Python 包使用，而是作为脚本目录。
"""

import sys
from pathlib import Path

# 确保 lib/ 在 sys.path 首位（平级导入依赖）
_LIB_DIR = str(Path(__file__).parent)
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)


# ── 事件总线 ──────────────────────────────────
from tension_bus import (
    bus as TensionBus,
    QueryEvent,
    InitialStateEvent,
    TensionEmittedEvent,
    ConceptBatchEvent,
    SoulParamsEvent,
    ResearchFindingsEvent,
    FoldCompleteEvent,
    TensionSubscription,
)

# ── 核心数据结构 ──────────────────────────────
from core_structures import (
    DualState,
    Tension,
    Perspective,
    SuspensionAssessment,
    load_perspective,
)

# ── 视角与张力类型库 ──────────────────────────
from perspective_types import (
    PERSPECTIVE_TYPES,
    TENSION_TYPES,
    RECOMMENDED_DUALITIES,
    EMERGENT_STYLE_MAP,
)

# ── 二重折叠引擎 ──────────────────────────────
from dual_fold import (
    dual_fold,
    transform_from_perspective,
    structural_tension,
)

# ── 涌现风格 ──────────────────────────────────
from emergent_style import (
    emergent_style,
    emergent_style_prompt,
)

# ── 悬置评估 ──────────────────────────────────
from suspension_evaluator import (
    evaluate_suspension,
    evaluate_suspension_with_pressure,
)

# ── 折叠深度策略 ──────────────────────────────
from fold_depth_policy import (
    determine_max_fold_depth,
)

# ── 宪政 DNA ──────────────────────────────────
from constitutional_dna import (
    build_constitutional_prompt,
    constitutional_critique,
    CONSTITUTIONAL_PRINCIPLES,
    DNA_REQUIREMENTS,
)

# ── 路由层 ────────────────────────────────────
from routing import (
    route_query,
    detect_dual_nature,
    assess_query_depth,
    quick_response,
    evaluate_degradation_result,
    QueryDepth,
    DepthAssessment,
    DegradationDecision,
)

# ── 后端标准接口 ──────────────────────────────
from graph_backend import (
    GraphBackend,
    dialogical_retrieval,
    search_concepts_bm25,
    get_concept,
    get_subgraph,
    find_same_name_variants,
    write_genealogy_edge,
    get_genealogy_paths,
    store_concept,
    update_concept_weight,
    get_stats as graph_stats,
)

from memory import (
    MemoryBackend,
    record_session,
    record_dual_session,
    record_feedback,
    get_session,
    get_stats as memory_stats,
    inject_session_metadata,
)

from learner import (
    LearningBackend,
    process_feedback,
    get_lean_summary,
    get_learner_report,
    identify_weak_concepts,
    generate_curriculum_queries,
    extract_concepts_from_correction,
)

# ── 导出清单 ──────────────────────────────────
__all__ = [
    # TensionBus
    'TensionBus', 'QueryEvent', 'InitialStateEvent', 'TensionEmittedEvent',
    'ConceptBatchEvent', 'SoulParamsEvent', 'ResearchFindingsEvent',
    'FoldCompleteEvent', 'TensionSubscription',
    # 核心结构
    'DualState', 'Tension', 'Perspective', 'SuspensionAssessment', 'load_perspective',
    # 视角类型
    'PERSPECTIVE_TYPES', 'TENSION_TYPES', 'RECOMMENDED_DUALITIES', 'EMERGENT_STYLE_MAP',
    # 折叠引擎
    'dual_fold', 'transform_from_perspective', 'structural_tension',
    # 涌现风格
    'emergent_style', 'emergent_style_prompt',
    # 悬置评估
    'evaluate_suspension', 'evaluate_suspension_with_pressure',
    # 折叠深度
    'determine_max_fold_depth',
    # 宪政DNA
    'build_constitutional_prompt', 'constitutional_critique', 'CONSTITUTIONAL_PRINCIPLES', 'DNA_REQUIREMENTS',
    # 路由
    'route_query', 'detect_dual_nature', 'assess_query_depth', 'quick_response', 'evaluate_degradation_result',
    'QueryDepth', 'DepthAssessment', 'DegradationDecision',
    # 图谱
    'GraphBackend', 'dialogical_retrieval', 'search_concepts_bm25', 'get_concept',
    'get_subgraph', 'find_same_name_variants', 'write_genealogy_edge',
    'get_genealogy_paths', 'store_concept', 'update_concept_weight', 'graph_stats',
    # 记忆
    'MemoryBackend', 'record_session', 'record_dual_session', 'record_feedback',
    'get_session', 'memory_stats', 'inject_session_metadata',
    # 学习
    'LearningBackend', 'process_feedback', 'get_lean_summary', 'get_learner_report',
    'identify_weak_concepts', 'generate_curriculum_queries', 'extract_concepts_from_correction',
]
