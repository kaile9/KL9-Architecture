"""
9R-2.0 RHIZOME · 通用工具函数
提取重复逻辑 · 统一计算口径

所有模块共享的计算逻辑集中于此，避免代码重复。
"""

import re
from typing import List, Optional


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将数值限制在 [min_val, max_val] 范围内"""
    return max(min_val, min(max_val, value))


def extract_terms(query: str, term_length_min: int = 2, term_length_max: int = 4) -> List[str]:
    """
    从查询中提取潜在术语
    
    策略：
    1. 中文：term_length_min 到 term_length_max 个汉字的 n-gram
    2. 英文：3+ 字母的词，过滤常见停用词
    3. 混合：中英混合词组
    
    返回去重后的术语列表（保持原始顺序）
    """
    terms: List[str] = []
    
    # 中文术语提取
    pattern = f'[\u4e00-\u9fff]{{{term_length_min},{term_length_max}}}'
    chinese_terms = re.findall(pattern, query)
    terms.extend(chinese_terms)
    
    # 英文术语提取（仅当查询包含中文时）
    english_terms: List[str] = []
    if re.search(r'[\u4e00-\u9fff]', query):
        english_words = re.findall(r'[a-zA-Z]{3,}', query)
        stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'what', 'how', 'are', 'you', 'was', 'were'}
        english_terms = [w.lower() for w in english_words if w.lower() not in stop_words]
        terms.extend(english_terms)
    else:
        # 纯英文文本：不提取英文停用词
        english_words = re.findall(r'[a-zA-Z]{3,}', query)
        stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'what', 'how', 'are', 'you', 'was', 'were'}
        english_terms = [w.lower() for w in english_words if w.lower() not in stop_words]
        terms.extend(english_terms)
    
    # 混合术语（仅当查询包含中文时）
    mixed_terms: List[str] = []
    if re.search(r'[\u4e00-\u9fff]', query):
        mixed = re.findall(r'[\u4e00-\u9fffa-zA-Z0-9\-_]{3,}', query)
        mixed_terms = [t for t in mixed if t not in terms and t.lower() not in stop_words]
    terms.extend(mixed_terms)
    
    # 去重并保持顺序
    seen = set()
    unique_terms: List[str] = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            unique_terms.append(t)
    
    return unique_terms


def compute_concept_density(query: str, keywords: Optional[List[str]] = None,
                            normalization_base: int = 5) -> float:
    """
    计算概念密度
    
    概念密度 = 匹配关键词的术语数 / 归一化基数
    
    参数：
        query: 输入查询
        keywords: 用于过滤的关键词列表，None 时提取所有潜在术语
        normalization_base: 归一化基数（默认 5 个术语为满密度）
    
    返回值：
        [0, 1] 范围内的概念密度
    """
    if not query:
        return 0.0
    
    all_terms = extract_terms(query)
    
    if keywords:
        # 只保留包含关键词的术语
        potential_terms = []
        for term in all_terms:
            if term in keywords or any(kw in term for kw in keywords):
                potential_terms.append(term)
    else:
        potential_terms = all_terms
    
    if not potential_terms:
        return 0.0
    
    # 去重
    unique_terms = list(dict.fromkeys(potential_terms))
    
    # 按查询长度归一化
    normalized_length = max(len(query) / normalization_base, 3)
    density = min(len(unique_terms) / normalized_length, 1.0)
    
    return round(density, 2)


def compute_tension_factor(query: str, tension_keywords: Optional[List[str]] = None,
                           normalization_count: int = 5) -> float:
    """
    计算张力因子
    
    张力因子 = 张力关键词命中数 / 归一化计数
    
    参数：
        query: 输入查询
        tension_keywords: 张力关键词列表，None 时使用默认列表
        normalization_count: 归一化基数（默认 5 个关键词为满张力）
    
    返回值：
        [0, 1] 范围内的张力因子
    """
    if not query:
        return 0.0
    
    if tension_keywords is None:
        tension_keywords = [
            "但是", "然而", "不过", "却", "反而",
            "矛盾", "冲突", "对立", "相反", "相对",
            "問題", "困難", "挑戰", "困境", "難題",
            "為什麼", "如何", "怎麼", "什麼", "是否",
            "能否", "可否", "難道", "豈非"
        ]
    
    tension_count = sum(1 for kw in tension_keywords if kw in query)
    tension_factor = min(tension_count / normalization_count, 1.0)
    
    return round(tension_factor, 2)


def compute_length_factor(query_length: int, max_length: int = 1000) -> float:
    """
    计算长度因子
    
    长度因子 = min(查询长度 / 最大长度, 1.0)
    
    参数：
        query_length: 查询字符数
        max_length: 最大归一化长度
    
    返回值：
        [0, 1] 范围内的长度因子
    """
    return min(query_length / max_length, 1.0)


def compute_difficulty(length_factor: float, concept_density: float,
                       tension_factor: float, specialized_factor: float = 0.0,
                       weights: Optional[List[float]] = None) -> float:
    """
    综合难度计算
    
    难度 = 加权求和，然后限制在 [0, 1]
    
    默认权重：
        长度因子: 0.2
        概念密度: 0.3
        张力因子: 0.2
        专用因子: 0.3
    
    参数：
        length_factor: 长度因子 [0, 1]
        concept_density: 概念密度 [0, 1]
        tension_factor: 张力因子 [0, 1]
        specialized_factor: 专用文本加成 [0, 1]
        weights: 自定义权重 [长度, 概念, 张力, 专用]
    
    返回值：
        [0, 1] 范围内的难度值
    """
    if weights is None:
        weights = [0.2, 0.3, 0.2, 0.3]
    
    difficulty = (
        length_factor * weights[0] +
        concept_density * weights[1] +
        tension_factor * weights[2] +
        specialized_factor * weights[3]
    )
    
    return round(clamp(difficulty, 0.0, 1.0), 2)


def allocate_fold_budget(difficulty: float, query_length: int,
                         is_specialized: bool = False,
                         length_threshold_1: int = 500,
                         length_threshold_2: int = 1000,
                         length_bonus_1: int = 1,
                         length_bonus_2: int = 2,
                         specialized_penalty: int = 1) -> int:
    """
    动态分配 fold 深度
    
    策略：
    - 难度 0.1 -> fold 2, 难度 0.2 -> fold 3, ... 难度 0.8+ -> fold 9
    - 长文本额外增加 fold（防止 token 爆炸）
    - 专用文本减少 fold（压缩更高效）
    
    参数：
        difficulty: 难度 [0, 1]
        query_length: 查询长度
        is_specialized: 是否为专用文本
        length_threshold_1: 长度阈值1（增加 length_bonus_1）
        length_threshold_2: 长度阈值2（增加 length_bonus_2）
        length_bonus_1: 阈值1的 fold 加成
        length_bonus_2: 阈值2的 fold 加成
        specialized_penalty: 专用文本的 fold 惩罚
    
    返回值：
        [2, 9] 范围内的 fold 深度
    """
    # 难度映射到基础 fold
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
    
    # 长度调整
    if query_length > length_threshold_2:
        base_fold = min(base_fold + length_bonus_2, 9)
    elif query_length > length_threshold_1:
        base_fold = min(base_fold + length_bonus_1, 9)
    
    # 专用文本调整
    if is_specialized:
        base_fold = max(base_fold - specialized_penalty, 2)
    
    return base_fold


def compute_target_ratio(query_length: int, difficulty: float,
                         base_ratio: float = 2.5,
                         long_text_threshold: int = 500,
                         long_text_ratio: float = 2.0,
                         high_difficulty_threshold: float = 0.8,
                         high_difficulty_adjustment: float = 0.3) -> float:
    """
    计算目标压缩率
    
    策略：
    - 基准：2.5
    - 长文本（>500字符）: 降低至 2.0（避免过度压缩）
    - 高难度（>0.8）: 放宽至 2.2（保留更多语义）
    
    返回值：
        [2.0, 2.5] 范围内的目标压缩率
    """
    ratio = base_ratio
    
    if query_length > long_text_threshold:
        ratio = long_text_ratio
    
    if difficulty > high_difficulty_threshold:
        ratio = max(ratio - high_difficulty_adjustment, 2.0)
    
    return round(ratio, 1)
