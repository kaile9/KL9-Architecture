"""KL9-RHIZOME v1.1 — 双维度评分引擎.

trust = quality * (1 - difficulty/200)
难度评估: 启发式 LLM 代理（v1.1 用启发式替代，后续接真实 LLM API）
质量评估: 基于 ProductionRecord 的客观评分
语言偏差: ±3% based on LLM model family and book language match
动态基准: HLE(50%) + GPQA Diamond(30%) + LongBenchV2(20%) → ceiling
"""
import re
from typing import Optional

from .models import ProductionRecord, DifficultyBreakdown


# ═══════════════════════════════════════════════════════
# 动态基准评分系统 (HLE + GPQA Diamond + LongBenchV2)
# 数据来源: llm-stats.com, benchlm.ai — 截至 2026-05-04
# ═══════════════════════════════════════════════════════

BENCHMARK_DATA = {
    # model_name: {hle, gpqa, longbench}
    # hle: Humanity's Last Exam score (0-100)
    # gpqa: GPQA Diamond score (0-100)
    # longbench: LongBenchV2 score (0-100)
    # 缺失分数用 None

    "claude-mythos-preview":     {"hle": 64.7, "gpqa": 94.5, "longbench": None},
    "claude-opus-4.7":           {"hle": 54.7, "gpqa": 94.2, "longbench": 58.0},
    "claude-opus-4.6":           {"hle": 53.1, "gpqa": 92.0, "longbench": 56.0},
    "claude-opus-4.5":           {"hle": 50.0, "gpqa": 90.0, "longbench": 55.0},
    "claude-sonnet-4.6":         {"hle": 49.0, "gpqa": 88.0, "longbench": 54.0},
    "claude-sonnet-4.5":         {"hle": 46.0, "gpqa": 83.4, "longbench": 52.0},
    "claude-haiku-4.5":          {"hle": 30.0, "gpqa": 70.0, "longbench": 40.0},

    "gpt-5.5-pro":               {"hle": 57.2, "gpqa": 94.0, "longbench": 57.0},
    "gpt-5.5":                   {"hle": 52.2, "gpqa": 93.6, "longbench": 56.0},
    "gpt-5.4":                   {"hle": 39.8, "gpqa": 88.0, "longbench": 52.0},
    "gpt-5.2":                   {"hle": 34.5, "gpqa": 86.0, "longbench": 50.0},
    "gpt-5":                     {"hle": 24.8, "gpqa": 78.0, "longbench": 45.0},

    "gemini-3.1-pro":            {"hle": 51.4, "gpqa": 94.1, "longbench": 55.0},
    "gemini-3-pro":              {"hle": 45.8, "gpqa": 91.9, "longbench": 53.0},
    "gemini-3-flash":            {"hle": 43.5, "gpqa": 85.0, "longbench": 50.0},
    "gemini-2.5-pro":            {"hle": 21.6, "gpqa": 78.0, "longbench": 45.0},

    "deepseek-v4-pro-max":       {"hle": 48.2, "gpqa": 90.0, "longbench": 55.0},
    "deepseek-v4-pro":           {"hle": 46.0, "gpqa": 88.0, "longbench": 54.0},
    "deepseek-v3.2":             {"hle": 40.8, "gpqa": 82.0, "longbench": 48.7},
    "deepseek-v3.2-speciale":    {"hle": 30.6, "gpqa": 80.0, "longbench": 50.0},
    "deepseek-v3":               {"hle": 28.0, "gpqa": 75.0, "longbench": 48.7},
    "deepseek-r1":               {"hle": 17.7, "gpqa": 71.0, "longbench": 42.0},

    "kimi-k2.5":                 {"hle": 50.2, "gpqa": 82.0, "longbench": 61.0},
    "kimi-k2.6":                 {"hle": 36.4, "gpqa": 78.0, "longbench": 56.0},
    "kimi-k2-thinking":          {"hle": 51.0, "gpqa": 80.0, "longbench": 58.0},

    "qwen3.5-397b":              {"hle": 28.7, "gpqa": 85.0, "longbench": 63.2},
    "qwen3.6-plus":              {"hle": 28.8, "gpqa": 84.0, "longbench": 62.0},
    "qwen3-max":                 {"hle": 26.2, "gpqa": 82.0, "longbench": 58.0},
    "qwen3":                     {"hle": 22.0, "gpqa": 78.0, "longbench": 55.0},

    # 后备估计
    "gpt-4o":                    {"hle": 18.0, "gpqa": 65.0, "longbench": 40.0},
    "gpt-4-turbo":               {"hle": 12.0, "gpqa": 55.0, "longbench": 35.0},
    "llama-4":                   {"hle": 22.0, "gpqa": 72.0, "longbench": 48.0},
    "llama-3":                   {"hle": 10.0, "gpqa": 50.0, "longbench": 35.0},
    "mistral":                   {"hle": 15.0, "gpqa": 55.0, "longbench": 38.0},
}

# 语言族映射
LLM_FAMILY = {
    "claude": "en", "gpt": "en", "gemini": "en", "gemma": "en",
    "llama": "en", "mistral": "en", "grok": "en",
    "deepseek": "zh", "qwen": "zh", "kimi": "zh",
    "glm": "zh", "ernie": "zh", "minimax": "zh",
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


# ═══════════════════════════════════════════════════════
# 模型查找 & 能力评估
# ═══════════════════════════════════════════════════════

def _normalize_name(name: str) -> str:
    """标准化模型名：小写 + 去空格 + 去连字符变体。"""
    return re.sub(r'[-_\s]+', '', name.lower().strip())


def _fuzzy_lookup(name: str) -> Optional[dict]:
    """模糊匹配 BENCHMARK_DATA。先精确匹配，再前缀匹配，再子串匹配。"""
    if not name:
        return None

    key = _normalize_name(name)

    # 1. 精确匹配（标准化后）
    normalized_bench = {_normalize_name(k): v for k, v in BENCHMARK_DATA.items()}
    if key in normalized_bench:
        return dict(normalized_bench[key])

    # 2. 前缀/包含匹配（标准化后双向包含）
    for orig_key, info in BENCHMARK_DATA.items():
        nk = _normalize_name(orig_key)
        if key in nk or nk in key:
            return dict(info)

    # 3. 原始字符串子串匹配（兜底）
    name_lower = name.lower().strip()
    for orig_key, info in BENCHMARK_DATA.items():
        if name_lower in orig_key.lower() or orig_key.lower() in name_lower:
            return dict(info)

    return None


def get_model_family(llm_name: str) -> str:
    """返回 "zh" | "en" | "neutral"。

    基于 LLM_FAMILY 前缀匹配，未知模型返回 "neutral"。
    """
    if not llm_name:
        return "neutral"

    key = llm_name.lower().strip()
    for prefix, family in LLM_FAMILY.items():
        if key.startswith(prefix):
            return family

    return "neutral"


def _compute_family_means() -> dict:
    """为插值计算每个 family 在各榜单上的均值。

    Returns: {family: {"hle": mean|None, "gpqa": mean|None, "longbench": mean|None}}
    """
    accum: dict = {}
    for model, data in BENCHMARK_DATA.items():
        family = get_model_family(model)
        if family not in accum:
            accum[family] = {"hle": [], "gpqa": [], "longbench": []}
        for k in ("hle", "gpqa", "longbench"):
            v = data.get(k)
            if v is not None:
                accum[family][k].append(v)

    result = {}
    for family, vals in accum.items():
        result[family] = {
            k: (sum(lst) / len(lst)) if lst else None
            for k, lst in vals.items()
        }
    return result


# 模块加载时预计算 family means
_FAMILY_MEANS = _compute_family_means()


def _global_mean(bench_key: str) -> float:
    """计算某榜单的全局均值（用于 family mean 也缺失时的最终兜底）。"""
    all_vals = [d[bench_key] for d in BENCHMARK_DATA.values()
                if d.get(bench_key) is not None]
    return sum(all_vals) / len(all_vals) if all_vals else 50.0


def estimate_model_ceiling(llm_name: str) -> float:
    """基于三榜单计算模型能力上限。

    1. fuzzy_lookup 查找基准数据
    2. 缺失项用同族模型均值插值
    3. combined = hle×0.50 + gpqa×0.30 + longbench×0.20
    4. ceiling = min(100, combined×1.4 + 10)
    5. 未知模型: ceiling = 50 (保守默认)
    """
    data = _fuzzy_lookup(llm_name)

    if data is None:
        return 50.0  # 保守默认

    family = get_model_family(llm_name)
    fm = _FAMILY_MEANS.get(family, {})

    def _get_val(key: str) -> float:
        v = data.get(key)
        if v is not None:
            return float(v)
        # 同族插值
        fm_val = fm.get(key)
        if fm_val is not None:
            return fm_val
        # 全局兜底
        return _global_mean(key)

    hle = _get_val("hle")
    gpqa = _get_val("gpqa")
    longbench = _get_val("longbench")

    combined = hle * 0.50 + gpqa * 0.30 + longbench * 0.20
    ceiling = min(100.0, combined * 1.4 + 10.0)
    return round(ceiling, 2)


def apply_language_bias(quality: float, llm_name: str, book_language: str) -> float:
    """对质量分应用语言偏差，使用动态 ceiling 替代静态层级。

    规则:
    - zh族模型 + 中文书 → quality * 1.03
    - zh族模型 + 其他语言 → quality * 0.97
    - en族模型 + 英文书 → quality * 1.03
    - en族模型 + 中文书 → quality * 0.97
    - 其他组合不变

    跨模型保护: 偏差调整后不能超过 estimate_model_ceiling() 计算的上限。

    Args:
        quality: 原始质量分 0-100
        llm_name: LLM 名称
        book_language: 书籍语言 ("zh"/"en"/"de"/"fr"/"other")

    Returns:
        调整后的质量分 (clamped to [0, ceiling])
    """
    if not llm_name or not book_language:
        return quality

    family = get_model_family(llm_name)

    if family == "neutral":
        return quality

    # 规范化书籍语言
    lang = book_language.lower().strip()
    if lang not in ("zh", "en"):
        lang = "other"

    bias = LANGUAGE_BIAS.get((family, lang), 0.0)
    adjusted = quality * (1.0 + bias)
    ceiling = estimate_model_ceiling(llm_name)

    # 跨模型保护
    return max(0.0, min(ceiling, adjusted))


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
