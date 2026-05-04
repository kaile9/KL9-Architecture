"""KL9-RHIZOME v1.1 — 双维度评分引擎.

trust = quality * (1 - difficulty/200)
难度评估: 启发式 LLM 代理（v1.1 用启发式替代，后续接真实 LLM API）
质量评估: 基于 ProductionRecord 的客观评分
语言偏差: ±3% based on LLM model family and book language match
"""
from .models import ProductionRecord, DifficultyBreakdown


# ═══════════════════════════════════════════════════════════════
# LLM 模型层级与语言族
# ═══════════════════════════════════════════════════════════════

LLM_TABLE = {
    # Tier 1 — 顶级
    "claude-opus-4.7":    {"tier": 1, "family": "en", "ceiling": 100},
    "claude-opus-4.5":    {"tier": 1, "family": "en", "ceiling": 98},
    "gpt-4.5":            {"tier": 1, "family": "en", "ceiling": 100},
    "gpt-4o":             {"tier": 1, "family": "en", "ceiling": 96},
    "gemini-2.5-pro":     {"tier": 1, "family": "en", "ceiling": 95},

    # Tier 2 — 强大
    "deepseek-v4-pro":    {"tier": 2, "family": "zh", "ceiling": 92},
    "deepseek-v3":        {"tier": 2, "family": "zh", "ceiling": 88},
    "claude-sonnet-4.6":  {"tier": 2, "family": "en", "ceiling": 90},
    "claude-sonnet-4.5":  {"tier": 2, "family": "en", "ceiling": 88},
    "gemini-2.0-flash":   {"tier": 2, "family": "en", "ceiling": 86},
    "qwen-3-max":         {"tier": 2, "family": "zh", "ceiling": 87},

    # Tier 3 — 良好
    "kimi-2.6":           {"tier": 3, "family": "zh", "ceiling": 82},
    "qwen-3":             {"tier": 3, "family": "zh", "ceiling": 80},
    "llama-4":            {"tier": 3, "family": "en", "ceiling": 78},
    "gpt-4o-mini":        {"tier": 3, "family": "en", "ceiling": 75},
    "claude-haiku-4.5":   {"tier": 3, "family": "en", "ceiling": 76},

    # Tier 4 — 基础
    "mistral":            {"tier": 4, "family": "en", "ceiling": 70},
    "llama-3":            {"tier": 4, "family": "en", "ceiling": 65},
}

# 语言补偿分: zh族模型读中文书+3%, 读英文0%, 读其他-3%
#              en族模型读英文书+3%, 读中文-3%, 读其他0%
LANGUAGE_BIAS = {
    ("zh", "zh"): 0.03,     # 中文模型 + 中文书
    ("zh", "en"): 0.00,     # 中文模型 + 英文书
    ("zh", "other"): -0.03,  # 中文模型 + 其他语言
    ("en", "en"): 0.03,     # 英文模型 + 英文书
    ("en", "zh"): -0.03,    # 英文模型 + 中文书
    ("en", "other"): 0.00,  # 英文模型 + 其他语言
}


def resolve_llm(llm_name: str) -> dict:
    """模糊匹配 LLM 名称到已知模型表。返回 {tier, family, ceiling}。

    匹配策略:
    1. 精确匹配 LLM_TABLE
    2. 子串匹配（如 "claude" 匹配 "claude-opus-4.7"）
    3. 基于名称前缀推断 family（含 "deepseek"/"qwen"/"kimi" → zh, 其余 → en）
    4. 无匹配 → family="neutral", tier=99, ceiling=100
    """
    if not llm_name:
        return {"tier": 99, "family": "neutral", "ceiling": 100}

    key = llm_name.lower().strip()

    # 1. 精确匹配
    if key in LLM_TABLE:
        return dict(LLM_TABLE[key])

    # 2. 子串匹配
    for known, info in LLM_TABLE.items():
        if key in known or known in key:
            return dict(info)

    # 3. 前缀推断
    zh_families = ["deepseek", "qwen", "kimi", "doubao", "ernie", "glm", "baichuan"]
    for prefix in zh_families:
        if key.startswith(prefix):
            return {"tier": 99, "family": "zh", "ceiling": 80}

    en_families = ["claude", "gpt", "gemini", "llama", "mistral", "anthropic", "openai"]
    for prefix in en_families:
        if key.startswith(prefix) or prefix in key:
            return {"tier": 99, "family": "en", "ceiling": 80}

    # 4. 无匹配
    return {"tier": 99, "family": "neutral", "ceiling": 100}


def apply_language_bias(quality: float, llm_name: str, book_language: str) -> float:
    """对质量分应用语言偏差。

    规则:
    - zh族模型 + 中文书 → quality * 1.03
    - zh族模型 + 其他语言 → quality * 0.97
    - en族模型 + 英文书 → quality * 1.03
    - en族模型 + 中文书 → quality * 0.97
    - 其他组合不变

    跨层级保护: 调整后的 quality 不能超过模型所在层级的 ceiling。
    例如 DeepSeek(ceiling=92) 即使 +3% 也不能超过 92。

    Args:
        quality: 原始质量分 0-100
        llm_name: LLM 名称（用于 resolve_llm）
        book_language: 书籍语言 ("zh"/"en"/"de"/"fr"/"other")

    Returns:
        调整后的质量分 (clamped to [0, ceiling])
    """
    if not llm_name or not book_language:
        return quality

    llm_info = resolve_llm(llm_name)
    family = llm_info["family"]
    ceiling = llm_info["ceiling"]

    if family == "neutral":
        return quality

    # 规范化书籍语言
    lang = book_language.lower().strip()
    if lang not in ("zh", "en"):
        lang = "other"

    bias = LANGUAGE_BIAS.get((family, lang), 0.0)
    adjusted = quality * (1.0 + bias)

    # 跨层级保护
    return max(0.0, min(float(ceiling), adjusted))


# ═══════════════════════════════════════════════════════════════
# 信任计算
# ═══════════════════════════════════════════════════════════════

def calculate_trust(difficulty: float, quality: float,
                    llm_name: str = "", book_language: str = "") -> float:
    """信任公式: trust = quality * (1 - difficulty/200), 裁剪到 [0, 100].

    v1.1+: 先通过 apply_language_bias 调整 quality，再计算 trust。

    Args:
        difficulty: 0-100, 越高越难
        quality: 0-100, 越高越好
        llm_name: LLM 名称（可选，用于语言偏差）
        book_language: 书籍语言（可选，"zh"/"en"/"de"/"fr"/"other"）

    Returns:
        trust score in [0, 100]
    """
    if llm_name and book_language:
        quality = apply_language_bias(quality, llm_name, book_language)

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
