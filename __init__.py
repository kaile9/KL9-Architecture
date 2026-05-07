"""
9R-2.0 RHIZOME · 主入口
压缩涌现智能 · 通用认知架构

统一前缀版本 · 所有组件以 9R-2.0 / N9R20 为标识

使用示例：
    from n9r20 import N9R20Framework
    
    agent = N9R20Framework()
    result = agent.process("何为空性？")
    print(result.output)
"""

import time
import sys
import importlib.util
from typing import Optional

import os

_base = os.path.dirname(os.path.abspath(__file__))

# 将基础路径加入 sys.path，使子模块能正确解析相对导入
if _base not in sys.path:
    sys.path.insert(0, _base)

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# 加载核心模块
_n9r20_structures = _load_module("n9r20_structures", _base + "/core/n9r20_structures.py")
_n9r20_config = _load_module("n9r20_config", _base + "/core/n9r20_config.py")
_n9r20_tension_bus = _load_module("n9r20_tension_bus", _base + "/core/n9r20_tension_bus.py")
_n9r20_llm_evaluator = _load_module("n9r20_llm_evaluator", _base + "/core/n9r20_llm_evaluator.py")
_n9r20_utils = _load_module("n9r20_utils", _base + "/core/n9r20_utils.py")
_n9r20_skillbook_compat = _load_module("n9r20_skillbook_compat", _base + "/core/n9r20_skillbook_compat.py")

# 加载技能模块
_n9r20_adaptive_router = _load_module("n9r20_adaptive_router", _base + "/skills/n9r20_adaptive_router.py")
_n9r20_compression_core = _load_module("n9r20_compression_core", _base + "/skills/n9r20_compression_core.py")
_n9r20_dual_reasoner = _load_module("n9r20_dual_reasoner", _base + "/skills/n9r20_dual_reasoner.py")
_n9r20_semantic_graph = _load_module("n9r20_semantic_graph", _base + "/skills/n9r20_semantic_graph.py")
_n9r20_memory_learner = _load_module("n9r20_memory_learner", _base + "/skills/n9r20_memory_learner.py")

# 导出核心数据结构
N9R20DualState = _n9r20_structures.N9R20DualState
N9R20Tension = _n9r20_structures.N9R20Tension
N9R20Perspective = _n9r20_structures.N9R20Perspective
N9R20PerspectiveType = _n9r20_structures.N9R20PerspectiveType
N9R20RoutingDecision = _n9r20_structures.N9R20RoutingDecision
N9R20CompressedOutput = _n9r20_structures.N9R20CompressedOutput
N9R20SkillBook = _n9r20_structures.N9R20SkillBook
N9R20TermNode = _n9r20_structures.N9R20TermNode

# 导出配置
N9R20RoutingConfig = _n9r20_config.N9R20RoutingConfig
N9R20CompressionConfig = _n9r20_config.N9R20CompressionConfig
N9R20MemoryConfig = _n9r20_config.N9R20MemoryConfig
N9R20SemanticGraphConfig = _n9r20_config.N9R20SemanticGraphConfig
N9R20TensionConfig = _n9r20_config.N9R20TensionConfig
n9r20_routing_config = _n9r20_config.n9r20_routing_config
n9r20_compression_config = _n9r20_config.n9r20_compression_config
n9r20_memory_config = _n9r20_config.n9r20_memory_config
n9r20_semantic_graph_config = _n9r20_config.n9r20_semantic_graph_config
n9r20_tension_config = _n9r20_config.n9r20_tension_config

# 导出TensionBus
N9R20TensionBus = _n9r20_tension_bus.N9R20TensionBus
N9R20TensionSubscription = _n9r20_tension_bus.N9R20TensionSubscription
N9R20QueryEvent = _n9r20_tension_bus.N9R20QueryEvent
N9R20CompressionTensionEvent = _n9r20_tension_bus.N9R20CompressionTensionEvent
N9R20CompressionCompleteEvent = _n9r20_tension_bus.N9R20CompressionCompleteEvent
N9R20ConceptClusterEvent = _n9r20_tension_bus.N9R20ConceptClusterEvent
N9R20DualPerspectiveEvent = _n9r20_tension_bus.N9R20DualPerspectiveEvent
N9R20SkillBookUpdateEvent = _n9r20_tension_bus.N9R20SkillBookUpdateEvent

# 导出工具函数
clamp = _n9r20_utils.clamp
extract_terms = _n9r20_utils.extract_terms
compute_concept_density = _n9r20_utils.compute_concept_density
compute_tension_factor = _n9r20_utils.compute_tension_factor
compute_difficulty = _n9r20_utils.compute_difficulty

# 导出 SkillBook 兼容层
N9R20ProductionRecord = _n9r20_skillbook_compat.N9R20ProductionRecord
N9R20DifficultyBreakdown = _n9r20_skillbook_compat.N9R20DifficultyBreakdown
N9R20ConceptProvenance = _n9r20_skillbook_compat.N9R20ConceptProvenance
N9R20ConceptNode = _n9r20_skillbook_compat.N9R20ConceptNode
N9R20SkillBookManifest = _n9r20_skillbook_compat.N9R20SkillBookManifest
N9R20SkillBookImporter = _n9r20_skillbook_compat.N9R20SkillBookImporter
N9R20SkillBookExporter = _n9r20_skillbook_compat.N9R20SkillBookExporter

# 导出技能
N9R20AdaptiveRouter = _n9r20_adaptive_router.N9R20AdaptiveRouter
N9R20CompressionCore = _n9r20_compression_core.N9R20CompressionCore
N9R20DynamicFoldEngine = _n9r20_compression_core.N9R20DynamicFoldEngine
N9R20DualReasoner = _n9r20_dual_reasoner.N9R20DualReasoner
N9R20SemanticGraph = _n9r20_semantic_graph.N9R20SemanticGraph
N9R20MemoryLearner = _n9r20_memory_learner.N9R20MemoryLearner
N9R20SessionMemory = _n9r20_memory_learner.N9R20SessionMemory

# 全局实例
n9r20_bus = _n9r20_tension_bus.n9r20_bus
n9r20_router = _n9r20_adaptive_router.n9r20_router
n9r20_compression_core = _n9r20_compression_core.n9r20_compression_core
n9r20_dual_reasoner = _n9r20_dual_reasoner.n9r20_dual_reasoner
n9r20_semantic_graph = _n9r20_semantic_graph.n9r20_semantic_graph
n9r20_memory_learner = _n9r20_memory_learner.n9r20_memory_learner


class N9R20Framework:
    """
    9R-2.0 RHIZOME 主入口
    
    压缩涌现智能 · 通用认知架构
    
    核心特性：
    1. 动态 fold 深度（2-9）
    2. 硬性压缩率约束（2.0-2.5x）
    3. 语义保留验证（>85%）
    4. 四模编码驱动（建破证截）
    5. 去中心化技能书传播
    """
    
    def __init__(self):
        self.n9r20_router = n9r20_router
        self.n9r20_compression_core = n9r20_compression_core
        self.n9r20_dual_reasoner = n9r20_dual_reasoner
        self.n9r20_semantic_graph = n9r20_semantic_graph
        self.n9r20_memory_learner = n9r20_memory_learner
        self.session_count = 0
    
    def process(self, query: str, 
                session_id: Optional[str] = None) -> N9R20CompressedOutput:
        if session_id is None:
            session_id = f"n9r20_{int(time.time())}_{self.session_count}"
        self.session_count += 1
        
        routing = self.n9r20_router.route(query)
        result = self.n9r20_compression_core.compress(
            query=query,
            routing=routing,
            session_id=session_id
        )
        return result
    
    def get_stats(self) -> dict:
        return {
            "session_count": self.session_count,
            "skill_books": {
                name: {
                    "total_calls": book.total_calls,
                    "success_rate": book.success_rate,
                    "average_retention": book.average_retention
                }
                for name, book in self.n9r20_memory_learner.skill_books.items()
            },
            "learned_nodes": len(self.n9r20_semantic_graph.learned_nodes),
            "core_nodes": len(self.n9r20_semantic_graph.core_network.nodes)
        }


def compress(query: str) -> str:
    agent = N9R20Framework()
    result = agent.process(query)
    return result.output


__version__ = "9R-2.0"
__author__ = "9R-2.0 RHIZOME"
__description__ = "压缩涌现智能 · 通用认知架构"

__all__ = [
    "N9R20Framework",
    "compress",
    # 核心结构
    "N9R20DualState",
    "N9R20Tension",
    "N9R20Perspective",
    "N9R20RoutingDecision",
    "N9R20CompressedOutput",
    "N9R20SkillBook",
    "N9R20TermNode",
    # 配置
    "N9R20RoutingConfig",
    "N9R20CompressionConfig",
    "N9R20MemoryConfig",
    "N9R20SemanticGraphConfig",
    "N9R20TensionConfig",
    # 事件总线
    "N9R20TensionBus",
    "N9R20TensionSubscription",
    # SkillBook 兼容层
    "N9R20ProductionRecord",
    "N9R20DifficultyBreakdown",
    "N9R20ConceptProvenance",
    "N9R20ConceptNode",
    "N9R20SkillBookManifest",
    "N9R20SkillBookImporter",
    "N9R20SkillBookExporter",
    # 全局单例
    "n9r20_router",
    "n9r20_compression_core",
    "n9r20_dual_reasoner",
    "n9r20_semantic_graph",
    "n9r20_memory_learner",
    "n9r20_bus",
    # 配置单例
    "n9r20_routing_config",
    "n9r20_compression_config",
    "n9r20_memory_config",
    "n9r20_semantic_graph_config",
    "n9r20_tension_config",
]
