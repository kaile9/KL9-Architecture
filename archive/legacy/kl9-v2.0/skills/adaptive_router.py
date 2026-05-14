"""
KL9-RHIZOME v2.0 · Adaptive-Router
自适应路由器 · 动态 fold 预算分配 · 回退决策
"""

import re
import time
from typing import Tuple, List
from dataclasses import dataclass

from core.structures import RoutingDecision
from core.tension_bus import TensionBus2, bus


class AdaptiveRouter:
    """
    自适应路由器
    
    三级决策：
    1. 文本类型检测（专用 vs 通用）
    2. 难度评估（0-1 连续谱）
    3. fold 预算分配（2-9 动态）
    """
    
    def __init__(self):
        self.bus = bus
        
        # 专用文本关键词（精简核心集，15-20 个最核心概念）
        # 同时包含繁简中文以覆盖不同文本
        self.specialized_keywords = [
            # 佛教核心概念
            "空", "識", "识", "緣起", "缘起", "中道", "般若",
            "如來", "如来", "菩薩", "菩萨", "涅槃", "因果",
            # 哲学核心概念
            "存在", "本质", "辯證", "辩证",
            # 科学核心概念
            "量子", "涌现"
        ]
    
    def route(self, query: str) -> RoutingDecision:
        """
        主路由函数
        
        返回 RoutingDecision 包含：
        - path: "specialized" | "standard"
        - confidence: 专用文本检测置信度
        - difficulty: 任务难度 [0,1]
        - target_fold_depth: 动态分配的 fold 深度 [2-9]
        - target_compression_ratio: 目标压缩率
        - urgency: 紧急度 [0,1]
        """
        # Level 1: 文本类型检测
        is_specialized, confidence = self._detect_specialized_text(query)
        
        # Level 2: 难度评估
        difficulty = self._assess_difficulty(query)
        
        # Level 3: fold 预算分配
        target_fold_depth = self._allocate_fold_budget(
            query_length=len(query),
            difficulty=difficulty,
            is_specialized=is_specialized
        )
        
        # Level 4: 压缩率目标
        target_ratio = self._compute_target_ratio(
            query_length=len(query),
            difficulty=difficulty
        )
        
        # Level 5: 紧急度计算
        urgency = self._compute_urgency(difficulty, len(query))
        
        return RoutingDecision(
            path="specialized" if is_specialized else "standard",
            confidence=confidence,
            difficulty=difficulty,
            target_fold_depth=target_fold_depth,
            target_compression_ratio=target_ratio,
            urgency=urgency,
            concept_density=self._compute_concept_density(query),
            tension_factor=self._detect_tension_keywords(query),
            length_factor=min(len(query) / 1000, 1.0)
        )
    
    def _detect_specialized_text(self, query: str) -> Tuple[bool, float]:
        """
        检测专用文本 + 置信度
        
        专用文本特征：
        1. 包含高密度专业术语
        2. 概念密度高
        3. 包含对立/张力概念
        """
        # 关键词匹配（使用命中密度而非绝对比例）
        keyword_count = sum(1 for kw in self.specialized_keywords if kw in query)
        # 关键修复：使用命中密度而非除以总关键词数
        # 假设 1 个关键词命中即可触发（单术语查询如"般若"）
        keyword_score = min(keyword_count / 1.0, 1.0)
        
        # 概念密度
        concept_density = self._compute_concept_density(query)
        
        # 张力因子
        tension_factor = self._detect_tension_keywords(query)
        
        # 综合置信度（加权）
        confidence = (
            keyword_score * 0.5 +  # 提高关键词权重
            concept_density * 0.3 + 
            tension_factor * 0.2
        )
        
        # 降低阈值：0.2 即可判定为专用文本
        is_specialized = confidence > 0.2
        
        return is_specialized, round(confidence, 2)
    
    def _assess_difficulty(self, query: str) -> float:
        """
        评估任务难度（0-1 连续谱）
        
        影响因素：
        1. 长度因子（长文本通常更复杂）
        2. 概念密度因子（术语数量 / 总字数）
        3. 张力因子（是否包含对立概念）
        4. 专用文本加成（专用文本通常更难）
        """
        # 1. 长度因子（降低阈值：100字符即开始影响）
        length_factor = min(len(query) / 200, 1.0)
        
        # 2. 概念密度因子
        concept_density = self._compute_concept_density(query)
        
        # 3. 张力因子
        tension_factor = self._detect_tension_keywords(query)
        
        # 4. 专用文本检测
        is_specialized, _ = self._detect_specialized_text(query)
        specialized_factor = 0.3 if is_specialized else 0.0
        
        # 综合难度（加权）
        difficulty = (
            length_factor * 0.2 + 
            concept_density * 0.3 + 
            tension_factor * 0.2 +
            specialized_factor * 0.3
        )
        
        return round(min(max(difficulty, 0.0), 1.0), 2)
    
    def _allocate_fold_budget(self, query_length: int, 
                             difficulty: float, 
                             is_specialized: bool) -> int:
        """
        动态分配 fold 深度（2-9）
        
        分配策略（难度驱动）：
        - 难度 < 0.2: fold = 2
        - 难度 0.2-0.3: fold = 3
        - 难度 0.3-0.4: fold = 4
        - 难度 0.4-0.5: fold = 5
        - 难度 0.5-0.6: fold = 6
        - 难度 0.6-0.7: fold = 7
        - 难度 0.7-0.8: fold = 8
        - 难度 ≥ 0.8: fold = 9
        
        调整因素：
        - 长文本：+2 fold（上限 9）
        - 专用文本：-1 fold（下限 2）
        """
        # 难度 → fold 映射：降低阈值，让更多查询进入高 fold
        # 难度 0.1 -> fold 2, 难度 0.2 -> fold 3, ... 难度 0.8 -> fold 9
        if difficulty < 0.1:
            base_fold = 2
        elif difficulty < 0.2:
            base_fold = 3
        elif difficulty < 0.3:
            base_fold = 4
        elif difficulty < 0.4:
            base_fold = 5
        elif difficulty < 0.5:
            base_fold = 6
        elif difficulty < 0.6:
            base_fold = 7
        elif difficulty < 0.7:
            base_fold = 8
        else:
            base_fold = 9
        
        # 长度调整（长文本需要更多 fold）
        if query_length > 1000:
            base_fold = min(base_fold + 2, 9)
        elif query_length > 500:
            base_fold = min(base_fold + 1, 9)
        
        # 专用文本调整（专用文本压缩更高效）
        if is_specialized:
            base_fold = max(base_fold - 1, 2)
        
        return base_fold
    
    def _compute_target_ratio(self, query_length: int, 
                              difficulty: float) -> float:
        """
        动态调整目标压缩率
        
        策略：
        - 基准：2.5
        - 长文本（> 500）: 降低至 2.0（避免过度压缩）
        - 高难度（> 0.8）: 放宽至 2.2（保留更多语义）
        """
        base_ratio = 2.5
        
        if query_length > 500:
            base_ratio = 2.0
        
        if difficulty > 0.8:
            base_ratio = max(base_ratio - 0.3, 2.0)
        
        return round(base_ratio, 1)
    
    def _compute_urgency(self, difficulty: float, 
                         query_length: int) -> float:
        """
        计算紧急度 [0,1]
        
        紧急度越高，越需要快速收敛
        
        影响因素：
        - 高难度任务：紧急度较高（需要快速决断）
        - 极长文本：紧急度较高（避免 token 爆炸）
        """
        urgency = difficulty * 0.6
        
        if query_length > 2000:
            urgency += 0.4  # 提高长文本的紧急度加成
        elif query_length > 1000:
            urgency += 0.2
        elif query_length > 500:
            urgency += 0.1
        
        return round(min(max(urgency, 0.0), 1.0), 2)
    
    def _compute_concept_density(self, query: str) -> float:
        """
        计算概念密度
        
        概念密度 = 专业术语数 / 查询长度归一化因子
        
        术语定义：
        - 中文：2-4 个汉字，且必须包含至少一个专业关键词
        - 英文：仅当有中文混合时，3+ 字母且非停用词
        """
        # 中文术语提取（2-4 个汉字）
        all_terms = re.findall(r'[\u4e00-\u9fff]{2,4}', query)
        
        # 过滤：只保留包含专业关键词的术语
        # 或保留看起来"专业"的术语（通过关键词列表匹配）
        potential_terms = []
        for term in all_terms:
            # 如果术语本身在关键词列表中，保留
            if term in self.specialized_keywords:
                potential_terms.append(term)
            # 如果术语包含任何关键词，保留
            elif any(kw in term for kw in self.specialized_keywords):
                potential_terms.append(term)
        
        # 英文术语提取（仅当有中文混合时）
        english_terms = []
        if re.search(r'[\u4e00-\u9fff]', query):
            english_words = re.findall(r'[a-zA-Z]{3,}', query)
            stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'what', 'how', 'are', 'you', 'was', 'were'}
            english_terms = [w.lower() for w in english_words if w.lower() not in stop_words]
        
        # 去重
        unique_terms = list(dict.fromkeys(potential_terms + english_terms))
        
        if not unique_terms:
            return 0.0
        
        # 计算：按查询长度归一化
        # 假设每 5 个字符可以有 1 个术语为满密度
        normalized_length = max(len(query) / 5, 3)  # 最少 3 个术语基准
        density = min(len(unique_terms) / normalized_length, 1.0)
        
        return round(density, 2)
    
    def _detect_tension_keywords(self, query: str) -> float:
        """
        检测张力关键词
        
        张力关键词：对立、矛盾、冲突概念
        
        返回张力因子 [0,1]
        """
        tension_keywords = [
            # 对立概念
            "但是", "然而", "不过", "却", "反而",
            "矛盾", "冲突", "对立", "相反", "相对",
            "問題", "困難", "挑戰", "困境", "難題",
            # 疑问词
            "為什麼", "如何", "怎麼", "什麼", "是否",
            "能否", "可否", "難道", "豈非"
        ]
        
        tension_count = sum(1 for kw in tension_keywords if kw in query)
        
        # 归一化：假设 5 个张力词为满张力
        tension_factor = min(tension_count / 5, 1.0)
        
        return round(tension_factor, 2)


# 全局单例
router = AdaptiveRouter()
