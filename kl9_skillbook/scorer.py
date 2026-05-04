"""KL9-RHIZOME v1.1 — 双维度评分引擎.

trust = quality * (1 - difficulty/200)
难度评估: 启发式 LLM 代理（v1.1 用启发式替代，后续接真实 LLM API）
质量评估: 基于 ProductionRecord 的客观评分
"""
from .models import ProductionRecord, DifficultyBreakdown


# ═══════════════════════════════════════════════════════════════
# 信任计算
# ═══════════════════════════════════════════════════════════════

def calculate_trust(difficulty: float, quality: float) -> float:
    """信任公式: trust = quality * (1 - difficulty/200), 裁剪到 [0, 100].

    Args:
        difficulty: 0-100, 越高越难
        quality: 0-100, 越高越好

    Returns:
        trust score in [0, 100]
    """
    trust = quality * (1.0 - difficulty / 200.0)
    return max(0.0, min(100.0, trust))


def classify_trust_level(trust: float) -> str:
    """根据信任分返回吸收策略.

    ≥90: "full"          完整吸收
    60-90: "supplementary" 补充学习
    30-60: "selective"     选择性提取
    <30:  "reject"         拒绝
    """
    if trust >= 90:
        return "full"
    elif trust >= 60:
        return "supplementary"
    elif trust >= 30:
        return "selective"
    else:
        return "reject"


# ═══════════════════════════════════════════════════════════════
# 难度估计（启发式 LLM 代理）
# ═══════════════════════════════════════════════════════════════

def _avg_word_length(text: str) -> float:
    """平均词汇长度."""
    words = text.split()
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def _unique_word_ratio(names: list[str]) -> float:
    """概念名中独特词汇比例."""
    if not names:
        return 0.0
    all_words = " ".join(names).lower().split()
    if not all_words:
        return 0.0
    return len(set(all_words)) / len(all_words)


def estimate_difficulty(
    book_title: str,
    book_author: str,
    concept_definitions: list[str],
) -> DifficultyBreakdown:
    """伪 LLM 评分（v1.1 用启发式替代，后续接真实 LLM API）.

    - style_density: 基于 definition 平均长度和词汇复杂度
    - info_density: 基于概念数量
    - viewpoint_novelty: 基于概念名中独特词汇比例
    - citation_density: 暂返回中性值 50（需要 LLM 才能准确评估）
    - overall: 四均值
    """
    n = len(concept_definitions)

    # style_density: 平均定义长度 → 映射到 0-100
    if concept_definitions:
        avg_len = sum(len(d) for d in concept_definitions) / n
        # 200 字 → ~30, 800 字 → ~80, 1500 字 → ~95
        style_density = min(100.0, max(10.0, 15.0 + avg_len * 0.07))
    else:
        style_density = 30.0

    # info_density: 概念数量 → 映射
    # 3 con → 20, 7 con → 50, 15 con → 75, 30+ con → 95
    if n <= 2:
        info_density = 20.0
    elif n <= 5:
        info_density = 20.0 + (n - 2) * 10.0
    elif n <= 15:
        info_density = 50.0 + (n - 5) * 3.0
    else:
        info_density = min(100.0, 80.0 + (n - 15) * 1.0)

    # viewpoint_novelty: 基于定义中独特词汇的比例
    if concept_definitions:
        all_text = " ".join(concept_definitions)
        unique_ratio = _unique_word_ratio([all_text]) if all_text else 0.5
        viewpoint_novelty = min(100.0, max(15.0, unique_ratio * 100.0 * 1.2))
    else:
        viewpoint_novelty = 40.0

    # citation_density: 启发式无法可靠评估，返回中性值
    citation_density = 50.0

    overall = (style_density + info_density + viewpoint_novelty + citation_density) / 4.0

    return DifficultyBreakdown(
        style_density=round(style_density, 1),
        info_density=round(info_density, 1),
        viewpoint_novelty=round(viewpoint_novelty, 1),
        citation_density=round(citation_density, 1),
        overall=round(overall, 1),
    )


# ═══════════════════════════════════════════════════════════════
# 质量评估（基于制作记录）
# ═══════════════════════════════════════════════════════════════

def estimate_quality(production_record: ProductionRecord) -> float:
    """基于制作记录计算质量分.

    quality = min(rounds_completed * 20, 60)           # 轮数最多贡献 60 分
            + (20 if verification_method in ("full-reread","external")
               else 10 if verification_method=="spot-check" else 0)
            + min(len(counter_perspectives) * 5, 20)   # 反视角最多 20 分
    裁剪到 [0, 100]
    """
    rounds_score = min(production_record.rounds_completed * 20, 60)

    vm = production_record.verification_method
    if vm in ("full-reread", "external"):
        verify_score = 20
    elif vm == "spot-check":
        verify_score = 10
    else:
        verify_score = 0

    counter_score = min(len(production_record.counter_perspectives) * 5, 20)

    quality = rounds_score + verify_score + counter_score
    return max(0.0, min(100.0, quality))
