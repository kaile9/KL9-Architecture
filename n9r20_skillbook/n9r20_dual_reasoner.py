"""
9R-2.0 RHIZOME · Dual-Reasoner
双视角推理器 · 整合 reasoner + soul

职责：
1. 构建 A/B 视角 → 辩证折叠 → 生成张力
2. 统一理论视角（A）和具身视角（B）
3. 输出 N9R20Tension + 四模编码建议
"""

import time
from typing import List, Dict, Optional

from core.n9r20_structures import N9R20Perspective, N9R20Tension, N9R20PerspectiveType
from core.n9r20_tension_bus import N9R20TensionBus, n9r20_bus, N9R20CompressionTensionEvent, N9R20DualPerspectiveEvent, N9R20TensionSubscription


class N9R20DualReasoner:
    """
    双视角推理器
    
    整合 reasoner（理论视角）+ soul（具身视角）
    
    核心功能：
    1. 构建 N9R20Perspective A（理论视角）
    2. 构建 N9R20Perspective B（具身视角）
    3. 生成 A/B 之间的张力
    4. 发射到 N9R20TensionBus
    """
    
    def __init__(self):
        self.n9r20_bus = n9r20_bus
        
        # 订阅 N9R20CompressionTensionEvent
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="dual-reasoner",
            event_types=["N9R20CompressionTensionEvent"],
            callback=self.on_compression_event
        ))
    
    def on_compression_event(self, event: N9R20CompressionTensionEvent):
        """
        响应压缩事件，构建 A/B 视角
        
        流程：
        1. 构建 N9R20Perspective A（理论视角）
        2. 构建 N9R20Perspective B（具身视角）
        3. 生成张力
        4. 发射到 N9R20TensionBus
        """
        query = event.query
        
        # 1. 构建 N9R20Perspective A（理论视角）
        perspective_A = self._construct_theoretical_perspective(query)
        
        # 2. 构建 N9R20Perspective B（具身视角）
        perspective_B = self._construct_embodied_perspective(query)
        
        # 3. 生成张力
        tension = self._generate_tension(perspective_A, perspective_B, query)
        
        # 4. 发射到 N9R20TensionBus
        self.n9r20_bus.emit(N9R20DualPerspectiveEvent(
            session_id=event.session_id,
            perspective_A=perspective_A,
            perspective_B=perspective_B,
            tension=tension
        ))
    
    def _construct_theoretical_perspective(self, query: str) -> N9R20Perspective:
        """
        构建理论视角（N9R20Perspective A）
        
        从理论框架出发，提取抽象、逻辑、分析特征
        """
        # 分析 query 的理论特征
        characteristics = self._extract_theoretical_characteristics(query)
        
        return N9R20Perspective(
            name="theoretical",
            characteristics=characteristics,
            key="perspective_A",
            perspective_type=N9R20PerspectiveType.THEORETICAL
        )
    
    def _construct_embodied_perspective(self, query: str) -> N9R20Perspective:
        """
        构建具身视角（N9R20Perspective B）
        
        从具身经验出发，提取经验、直觉、具体特征
        """
        # 分析 query 的具身特征
        characteristics = self._extract_embodied_characteristics(query)
        
        return N9R20Perspective(
            name="embodied",
            characteristics=characteristics,
            key="perspective_B",
            perspective_type=N9R20PerspectiveType.EMBODIED
        )
    
    def _generate_tension(self, A: N9R20Perspective, B: N9R20Perspective, 
                          query: str) -> N9R20Tension:
        """
        生成 A/B 之间的张力
        
        识别不可调和点，生成结构性张力
        """
        # 识别不可调和点
        irreconcilable = self._find_irreconcilable_points(A, B, query)
        
        # 提取 claim
        claim_A = self._extract_claim(A, query)
        claim_B = self._extract_claim(B, query)
        
        # 推断张力类型
        tension_type = self._infer_tension_type(A, B, query)
        
        # 计算张力强度
        intensity = min(len(irreconcilable) / 5.0, 1.0)
        
        return N9R20Tension(
            perspective_A=A.name,
            perspective_B=B.name,
            claim_A=claim_A,
            claim_B=claim_B,
            irreconcilable_points=irreconcilable,
            tension_type=tension_type,
            intensity=intensity
        )
    
    def _extract_theoretical_characteristics(self, query: str) -> List[str]:
        """
        提取理论特征
        
        识别 query 中的理论、抽象、逻辑特征
        """
        characteristics = []
        
        # 理论关键词
        theoretical_keywords = [
            "理论", "概念", "抽象", "逻辑", "分析",
            "結構", "系統", "模型", "框架", "原理"
        ]
        
        for kw in theoretical_keywords:
            if kw in query:
                characteristics.append(kw)
        
        # 如果没有识别到理论特征，添加默认特征
        if not characteristics:
            characteristics = ["分析", "逻辑", "抽象"]
        
        return characteristics
    
    def _extract_embodied_characteristics(self, query: str) -> List[str]:
        """
        提取具身特征
        
        识别 query 中的经验、直觉、具体特征
        """
        characteristics = []
        
        # 具身关键词
        embodied_keywords = [
            "经验", "感受", "直觉", "具体", "实践",
            "體驗", "直觀", "現象", "情境", "個案"
        ]
        
        for kw in embodied_keywords:
            if kw in query:
                characteristics.append(kw)
        
        # 如果没有识别到具身特征，添加默认特征
        if not characteristics:
            characteristics = ["经验", "直觉", "具体"]
        
        return characteristics
    
    def _find_irreconcilable_points(self, A: N9R20Perspective, B: N9R20Perspective, 
                                    query: str) -> List[str]:
        """
        识别不可调和点
        
        找出 A 和 B 视角之间的根本性冲突
        """
        irreconcilable = []
        
        # 检查 A 和 B 的特征是否冲突
        a_chars = set(A.characteristics)
        b_chars = set(B.characteristics)
        
        # 对立特征对
        oppositions = [
            ("抽象", "具体"),
            ("逻辑", "直觉"),
            ("分析", "综合"),
            ("理论", "实践"),
            ("普遍", "特殊")
        ]
        
        for opp_a, opp_b in oppositions:
            if opp_a in a_chars and opp_b in b_chars:
                irreconcilable.append(f"{opp_a} vs {opp_b}")
        
        # 如果没有找到冲突，添加默认冲突
        if not irreconcilable:
            irreconcilable = ["理论抽象 vs 经验具体"]
        
        return irreconcilable
    
    def _extract_claim(self, perspective: N9R20Perspective, query: str) -> str:
        """
        提取视角的主张
        
        根据视角特征和 query 生成主张
        """
        # 简化实现：基于视角特征生成主张
        # 实际实现应使用 LLM 生成
        chars = ", ".join(perspective.characteristics[:3])
        return f"从{perspective.name}视角看，{query}涉及{chars}"
    
    def _infer_tension_type(self, A: N9R20Perspective, B: N9R20Perspective, 
                            query: str) -> str:
        """
        推断张力类型
        
        根据 A/B 视角的特征推断张力类型
        """
        # 理论 vs 具身 → DIALECTICAL
        if A.perspective_type == N9R20PerspectiveType.THEORETICAL and \
           B.perspective_type == N9R20PerspectiveType.EMBODIED:
            return "dialectical"
        
        # 默认
        return "dialectical"


# 全局单例
n9r20_dual_reasoner = N9R20DualReasoner()
