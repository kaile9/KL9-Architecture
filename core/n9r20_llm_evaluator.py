"""
9R-2.0 RHIZOME · LLM 评估器
基于 LLM 的查询难度评估和 fold 深度分配

替代基于关键词的启发式方法，使用 LLM 进行智能评估。
"""

import json
import re
from typing import Tuple, Dict
from dataclasses import dataclass


@dataclass
class N9R20LLMEvaluation:
    """LLM 评估结果"""
    difficulty: float  # 0-1
    fold_depth: int  # 2-9
    compression_target: float  # 2.0-2.5
    is_specialized: bool
    reasoning: str
    confidence: float  # 0-1


class N9R20LLMFoldEvaluator:
    """
    LLM Fold 评估器
    
    使用 LLM 评估查询难度，动态分配 fold 深度。
    
    评估维度：
    1. 概念复杂度（抽象程度、跨学科性）
    2. 张力强度（对立概念的不可调和程度）
    3. 认知负载（需要多少层折叠才能充分展开）
    4. 压缩潜力（文本的信息密度和冗余度）
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        # 备用：基于规则的评估（当 LLM 不可用时）
        self._fallback_enabled = True
    
    def evaluate(self, query: str) -> N9R20LLMEvaluation:
        """
        评估查询并返回 fold 深度建议
        
        如果 LLM 可用，使用 LLM 评估；
        否则使用基于规则的备用方案。
        """
        if self.llm_client:
            return self._llm_evaluate(query)
        else:
            return self._fallback_evaluate(query)
    
    def _llm_evaluate(self, query: str) -> N9R20LLMEvaluation:
        """
        使用 LLM 进行评估
        
        Prompt 设计：
        - 要求 LLM 从 4 个维度评估
        - 输出结构化的 JSON
        - 包含推理过程
        """
        prompt = f"""你是一位认知架构专家。请评估以下查询的认知复杂度，并建议合适的压缩折叠深度。

查询: "{query}"

请从以下维度评估（0-1 分）：
1. 概念复杂度: 查询涉及的概念有多抽象、多跨学科？
2. 张力强度: 查询中是否包含不可调和的对立概念？
3. 认知负载: 需要多少层认知折叠才能充分展开这个查询？
4. 压缩潜力: 这个查询的信息密度和冗余度如何？

基于以上评估，请输出：
- 综合难度 (0-1)
- 建议 fold 深度 (2-9，整数)
- 目标压缩率 (2.0-2.5)
- 是否为专用文本 (true/false)
- 推理过程
- 置信度 (0-1)

请以 JSON 格式输出：
{{
    "difficulty": float,
    "fold_depth": int,
    "compression_target": float,
    "is_specialized": bool,
    "reasoning": str,
    "confidence": float
}}"""
        
        try:
            # 调用 LLM
            response = self._call_llm(prompt)
            
            # 解析 JSON
            result = self._parse_json(response)
            
            # 验证范围
            return self._validate_and_clamp(result)
            
        except Exception as e:
            # LLM 失败，回退到规则评估
            return self._fallback_evaluate(query)
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        # 这里应该调用实际的 LLM API
        # 简化实现：返回模拟响应
        if self.llm_client:
            return self.llm_client.generate(prompt)
        else:
            raise RuntimeError("LLM client not available")
    
    def _parse_json(self, response: str) -> Dict:
        """从 LLM 响应中提取 JSON"""
        # 尝试提取 JSON 块
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")
    
    def _validate_and_clamp(self, result: Dict) -> N9R20LLMEvaluation:
        """验证并限制范围"""
        difficulty = max(0.0, min(1.0, float(result.get('difficulty', 0.5))))
        fold_depth = max(2, min(9, int(result.get('fold_depth', 4))))
        compression_target = max(2.0, min(2.5, float(result.get('compression_target', 2.5))))
        is_specialized = bool(result.get('is_specialized', False))
        reasoning = str(result.get('reasoning', ''))
        confidence = max(0.0, min(1.0, float(result.get('confidence', 0.7))))
        
        return N9R20LLMEvaluation(
            difficulty=difficulty,
            fold_depth=fold_depth,
            compression_target=compression_target,
            is_specialized=is_specialized,
            reasoning=reasoning,
            confidence=confidence
        )
    
    def _fallback_evaluate(self, query: str) -> N9R20LLMEvaluation:
        """
        基于规则的备用评估
        
        当 LLM 不可用时使用。
        基于查询长度、概念密度、张力关键词等启发式规则。
        """
        # 长度因子
        length_factor = min(len(query) / 100, 1.0)  # 100 字符为满长度
        
        # 概念密度（简单统计 2-4 字词组）
        import re
        terms = re.findall(r'[\u4e00-\u9fff]{2,4}', query)
        concept_density = min(len(set(terms)) / 5, 1.0) if terms else 0.0
        
        # 张力关键词
        tension_keywords = ['矛盾', '冲突', '对立', '问题', '困难', '为什么', '如何', '是否']
        tension_count = sum(1 for kw in tension_keywords if kw in query)
        tension_factor = min(tension_count / 3, 1.0)
        
        # 综合难度
        difficulty = (length_factor * 0.3 + concept_density * 0.4 + tension_factor * 0.3)
        difficulty = round(max(0.0, min(1.0, difficulty)), 2)
        
        # 分配 fold 深度
        if difficulty < 0.2:
            fold_depth = 2
        elif difficulty < 0.4:
            fold_depth = 3
        elif difficulty < 0.6:
            fold_depth = 5
        elif difficulty < 0.8:
            fold_depth = 7
        else:
            fold_depth = 9
        
        # 目标压缩率
        if len(query) > 50:
            compression_target = 2.0
        else:
            compression_target = 2.5
        
        # 是否为专用文本
        specialized_keywords = [
            '空', '識', '緣起', '中道', '般若', '涅槃', '禪',
            '量子', '熵', '涌现', '拓扑',
            '存在', '虚无', '自由', '必然'
        ]
        is_specialized = any(kw in query for kw in specialized_keywords)
        
        return N9R20LLMEvaluation(
            difficulty=difficulty,
            fold_depth=fold_depth,
            compression_target=compression_target,
            is_specialized=is_specialized,
            reasoning=f"基于规则评估: 长度因子={length_factor:.2f}, 概念密度={concept_density:.2f}, 张力因子={tension_factor:.2f}",
            confidence=0.6
        )


# 全局单例（初始化为备用模式）
n9r20_llm_evaluator = N9R20LLMFoldEvaluator()
