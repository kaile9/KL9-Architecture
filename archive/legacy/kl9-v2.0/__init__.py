"""
KL9-RHIZOME v2.0 · 主入口
压缩涌现智能 · 通用认知架构

使用示例：
    from kl9_v20 import KL9v20
    
    agent = KL9v20()
    result = agent.process("何为空性？")
    print(result.output)
    print(f"压缩率: {result.compression_ratio}")
    print(f"语义保留: {result.semantic_retention}")
"""

import time
from typing import Optional

from core.structures import CompressedOutput, RoutingDecision
from core.tension_bus import bus

from skills.adaptive_router import router
from skills.compression_core import compression_core
from skills.dual_reasoner import dual_reasoner
from skills.semantic_graph import semantic_graph
from skills.memory_learner import memory_learner


class KL9v20:
    """
    KL9-RHIZOME v2.0 主入口
    
    压缩涌现智能 · 通用认知架构
    
    核心特性：
    1. 动态 fold 深度（2-9）
    2. 硬性压缩率约束（2.0-2.5x）
    3. 语义保留验证（>85%）
    4. 四模编码驱动（建破证截）
    5. 去中心化技能书传播
    
    使用方式：
        agent = KL9v20()
        result = agent.process("你的问题")
    """
    
    def __init__(self):
        # 初始化 5 核心技能
        self.router = router
        self.compression_core = compression_core
        self.dual_reasoner = dual_reasoner
        self.semantic_graph = semantic_graph
        self.memory_learner = memory_learner
        
        # 会话计数
        self.session_count = 0
    
    def process(self, query: str, 
                session_id: Optional[str] = None) -> CompressedOutput:
        """
        处理用户查询
        
        流程：
        1. 路由决策（文本类型 + 难度 + fold 预算）
        2. 压缩核心引擎执行四模编码折叠
        3. 返回压缩决断输出
        
        Args:
            query: 用户查询文本
            session_id: 可选的会话 ID（自动分配）
        
        Returns:
            CompressedOutput: 包含压缩输出、压缩率、语义保留率等
        """
        # 分配会话 ID
        if session_id is None:
            session_id = f"kl9_{int(time.time())}_{self.session_count}"
        self.session_count += 1
        
        # Phase 1: 路由决策
        routing = self.router.route(query)
        
        # Phase 2: 压缩核心引擎执行
        result = self.compression_core.compress(
            query=query,
            routing=routing,
            session_id=session_id
        )
        
        return result
    
    def get_stats(self) -> dict:
        """
        获取系统统计信息
        
        Returns:
            dict: 包含会话数、技能书状态等
        """
        return {
            "session_count": self.session_count,
            "skill_books": {
                name: {
                    "total_calls": book.total_calls,
                    "success_rate": book.success_rate,
                    "average_retention": book.average_retention
                }
                for name, book in self.memory_learner.skill_books.items()
            },
            "learned_nodes": len(self.semantic_graph.learned_nodes),
            "core_nodes": len(self.semantic_graph.core_network.nodes)
        }


# 便捷函数
def compress(query: str) -> str:
    """
    快速压缩函数
    
    使用默认配置压缩文本，返回压缩后的字符串
    
    Args:
        query: 输入文本
    
    Returns:
        str: 压缩后的文本
    """
    agent = KL9v20()
    result = agent.process(query)
    return result.output


# 版本信息
__version__ = "2.0.0"
__author__ = "KL9-RHIZOME"
__description__ = "压缩涌现智能 · 通用认知架构"

# 导出
__all__ = [
    "KL9v20",
    "compress",
    "CompressedOutput",
    "RoutingDecision",
    "router",
    "compression_core",
    "dual_reasoner",
    "semantic_graph",
    "memory_learner",
]
