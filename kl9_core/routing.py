"""
KL9-RHIZOME v1.5 · 深度路由层
凭判断决定应答深度。短问短答，深入问深入答。
学术问题全链路激活。管道任一阶段失败则降级为简答。
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Set
import re


# ═══════════════════════════════════════════
# 类型定义
# ═══════════════════════════════════════════

class QueryDepth(Enum):
    """查询深度三级分类"""
    QUICK = auto()       # 短问短答：fold_depth=0，不走任何技能
    STANDARD = auto()    # 有二重性但非学术：有限技能 + 中等折叠
    DEEP = auto()        # 学术级：全链路 7 技能激活，最大折叠


class PipelineStage(Enum):
    """管线阶段枚举，每个阶段都可能失败"""
    DUALITY_DETECTION  = "duality_detection"    # 二重性识别
    PERSPECTIVE_LOAD   = "perspective_load"      # A/B 视角加载
    DIALOGUE_ACTIVATE  = "dialogue_activate"     # 理论对话激活
    GRAPH_RETRIEVAL    = "graph_retrieval"       # 概念图谱检索
    RESEARCH_LOOKUP    = "research_lookup"       # 外部研究检索
    DUAL_FOLD          = "dual_fold"             # 递归二重折叠
    EXPRESSION_GEN     = "expression_gen"        # 表达生成


@dataclass
class DepthAssessment:
    """深度评估结果——路由决策的完整信息"""
    depth: QueryDepth
    max_fold_depth: int              # 0=casual, 1-5=折叠
    full_pipeline: bool              # True=激活全部 7 技能
    activated_skills: List[str]      # 本次需激活的技能名列表
    tension_type: Optional[str]      # 识别的张力类型
    confidence: float                # 分类置信度 [0, 1]
    reasoning: str                   # 分类理由（可调试）


@dataclass
class StageResult:
    """单个管线阶段的执行结果"""
    stage: PipelineStage
    success: bool
    error: Optional[str] = None
    fallback_used: bool = False


@dataclass
class DegradationDecision:
    """降级决策"""
    degraded: bool
    original_depth: QueryDepth
    target_depth: QueryDepth
    target_fold_depth: int
    reason: str
    failed_stages: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════
# 检测模式库
# ═══════════════════════════════════════════

# 注意：中文不能使用 \b（\b 仅匹配 \w 与 \W 的边界，中文属于 \W）
# 中文模式使用零宽断言 (?<![^\W]) 或直接无边界匹配，依赖唯一性防止误触发

ACADEMIC_MARKERS = [
    # ── 哲学术语（中文：无边界 / 英文：\b） ──
    r'(?:本体论|认识论|方法论|范式|谱系学|现象学|解构|后结构主义|后现代|现代性|后现代性'
    r'|存在论|知识论|辩证法|否定之否定|扬弃|异化|物化|商品拜物教|规训|治理术|生命政治'
    r'|拟像|超真实|内爆|延异|踪迹|增补|药|档案|知识型|认识型|话语形构)',
    r'\b(?:ontology|epistemology|methodology|paradigm|genealogy|phenomenology|deconstruction'
    r'|post-structuralism|postmodern|modernity|biopolitics|governmentality|simulacrum'
    r'|hyperreality|différance|episteme|discursive)\b',
    # ── 引文/引用标记 ──
    r'[""「」""]',                       # 引号（含中日文）
    r'（[^）]*\d{4}[^）]*）',           # 括号内年份引用
    r'\b(?:1[89]\d{2}|20[012]\d)\b',    # 年份 1800-2029
    # ── 思想家（中文：无边界匹配） ──
    r'(?:福柯|德里达|德勒兹|鲍德里亚|哈贝马斯|阿多诺|海德格尔|萨特|尼采|康德|黑格尔|马克思'
    r'|拉康|巴特|齐泽克|阿甘本|韦伯|涂尔干|布迪厄|拉图尔|巴特勒|斯皮瓦克|萨义德'
    r'|维特根斯坦|罗尔斯|诺齐克|施密特|本雅明|阿伦特|列维纳斯|梅洛-庞蒂|柏格森'
    r'|霍克海默|马尔库塞|阿尔都塞|葛兰西|卢卡奇|弗洛姆|荣格|弗洛伊德)',
    # ── 思想家（英文：\b 边界） ──
    r'\b(?:Foucault|Derrida|Deleuze|Baudrillard|Habermas|Adorno|Heidegger|Sartre|Nietzsche|Kant'
    r'|Hegel|Marx|Lacan|Barthes|Žižek|Agamben|Weber|Durkheim|Bourdieu|Latour|Butler'
    r'|Wittgenstein|Rawls|Schmitt|Benjamin|Arendt|Levinas|Merleau-Ponty'
    r'|Horkheimer|Marcuse|Althusser|Gramsci|Lukács|Freud|Jung)\b',
    # ── 学术格式 ──
    r'(?:参见|引自|出处|参考文献)',
    r'\b(?:cf\.|ibid\.|op\.\s*cit\.|et\s+al\.|i\.e\.|e\.g\.)\b',
    # ── 理论框架（中文：无边界） ──
    r'(?:理论框架|分析框架|批判理论|文化研究|媒介研究|话语分析|精神分析|符号学'
    r'|结构主义|后殖民|女性主义|酷儿理论|批判种族理论|生态批评|动物研究)',
    # ── 著作名模式 ──
    r'《[^》]+》',                       # 中文书名号
    # ── 学术问法（中文：无边界） ──
    r'(?:如何理解|如何定义|怎样看待|试论|浅析|论析|考辨|辨析|商榷|述评)',
]

QUICK_MARKERS = [
    # ── 问候 ──
    r'^(你好|嗨|早|晚上好|晚安|再见|谢谢|抱歉|嗯|哦|哈|好|行|ok|okay|对|是的|明白)',
    r'^(hello|hi|hey|bye|thanks|ok|okay|yes|no|got it)$',
    # ── 简单事实查询 ──
    r'^(今天|明天|昨天|现在|几[点时]|什么[时候间]|天气|日期|时间)',
    r'^(什么是|who is|what is) [^?？]{1,15}[?？]?$',
    # ── 纯工具指令 ──
    r'^(帮我|请帮我|能不能|可以帮我|能帮|帮我查|查一下)',
    # ── 单字/单表情 ──
    r'^[😀-🙏👀-🙌🚀-🛸]{1,3}$',
]

# 二重性信号词：暗示需要辩证看待
DUALITY_SIGNALS = [
    # 中文二重性信号词（无边界，依赖唯一性）
    r'(?:但是|然而|可是|不过|虽然|却|但|矛盾|两难|悖论|对立|张力'
    r'|一方面|另一方面|既是|又是|既非|又非|未必|不一定|未必如此)',
    # 哲学判断句结构（暗含二重性）
    r'(?:先于|优先于|更重要|根本上|本质上|到底是|究竟)',
    # 对比问法 / 结构性张力
    r'(?:与\w{1,4}之间|区别|差异|分歧|对立|冲突|不可调和|不可通约'
    r'|之间.*张力|vs\.?|versus|相对|相对于)',
    r'\b(?:but|however|although|yet|paradox|tension|contradiction|dilemma'
    r'|vs\.?|versus|on one hand|on the other hand)\b',
]


# ═══════════════════════════════════════════
# 核心：三步深度分类器
# ═══════════════════════════════════════════

def assess_query_depth(
    query: str,
    has_duality: bool,
    tension_type: Optional[str] = None,
) -> DepthAssessment:
    """
    三步深度分类器 —— 路由决策的核心。

    流程:
        Step 1: Quick 检测 → 短问短答
        Step 2: Academic 检测 → 全链路激活  
        Step 3: Standard fallback → 中等深度

    返回 DepthAssessment 供 orchestrator 消费。
    """

    query_len = len(query)
    academic_score = _count_markers(query, ACADEMIC_MARKERS)
    quick_score = _count_markers(query, QUICK_MARKERS)
    duality_score = _count_markers(query, DUALITY_SIGNALS)

    # ── Step 1: Quick 检测 ──
    # 条件：快速标记命中 + 短文本（≤25字），或无二重性信号
    if (quick_score >= 1 and query_len <= 25) or (not has_duality and academic_score == 0):
        confidence = 0.95 if quick_score >= 1 else 0.80
        return DepthAssessment(
            depth=QueryDepth.QUICK,
            max_fold_depth=0,
            full_pipeline=False,
            activated_skills=[],
            tension_type=None,
            confidence=confidence,
            reasoning=f"快速标记={quick_score}, 学术标记={academic_score}, 长度={query_len} → QUICK"
        )

    # ── Step 2: Academic 检测 ──
    # 强学术信号 ≥2 → DEEP 全链路
    if academic_score >= 2:
        fold_depth = min(3 + academic_score // 2, 5)
        return DepthAssessment(
            depth=QueryDepth.DEEP,
            max_fold_depth=fold_depth,
            full_pipeline=True,
            activated_skills=[
                "core", "reasoner", "graph", "research",
                "soul", "memory", "learner"
            ],
            tension_type=tension_type,
            confidence=min(0.70 + academic_score * 0.05, 0.98),
            reasoning=f"学术标记={academic_score} ≥ 2 → DEEP 全链路, fold_depth={fold_depth}"
        )

    # 弱学术信号 = 1 → STANDARD 上限
    if academic_score == 1:
        fold_depth = min(2 + query_len // 100, 4)
        return DepthAssessment(
            depth=QueryDepth.STANDARD,
            max_fold_depth=fold_depth,
            full_pipeline=False,
            activated_skills=["core", "reasoner", "graph"],
            tension_type=tension_type,
            confidence=0.65,
            reasoning=f"学术标记=1, 长度={query_len} → STANDARD(学术上限), fold_depth={fold_depth}"
        )

    # ── Step 3: Standard ──
    # 有二重性但无学术标记 → 按 query 长度定折叠深度
    fold_depth = 1
    if query_len > 50:
        fold_depth = 2
    if query_len > 150:
        fold_depth = 3
    # 显式二重性信号词提升深度
    if duality_score >= 2:
        fold_depth = min(fold_depth + 1, 4)

    skills = ["core", "reasoner"] if fold_depth >= 2 else ["core"]

    return DepthAssessment(
        depth=QueryDepth.STANDARD,
        max_fold_depth=fold_depth,
        full_pipeline=False,
        activated_skills=skills,
        tension_type=tension_type,
        confidence=0.70,
        reasoning=f"无学术信号, 长度={query_len}, 二重性信号={duality_score} → STANDARD fold_depth={fold_depth}"
    )


# ═══════════════════════════════════════════
# 管线失败 → 降级逻辑
# ═══════════════════════════════════════════

# 阶段失败严重度：哪些阶段失败会导致强制降级
_CRITICAL_STAGES: Set[PipelineStage] = {
    PipelineStage.DUALITY_DETECTION,
    PipelineStage.DUAL_FOLD,
}
# DEEP 才关心的阶段：失败不致命但标记降级
_DEEP_ONLY_STAGES: Set[PipelineStage] = {
    PipelineStage.RESEARCH_LOOKUP,
}

def evaluate_degradation(
    original_depth: QueryDepth,
    stage_results: List[StageResult],
) -> DegradationDecision:
    """
    根据管线阶段执行结果决定是否降级、降到哪一级。

    降级规则:
        DEEP:
          - 关键阶段（duality/dualfold）失败 → QUICK（降两级）
          - 仅研究/图谱失败 → STANDARD（降一级，保留已完成阶段）
        STANDARD:
          - 二重性检测失败 → QUICK
          - 其他非关键失败 → 保持 STANDARD
        QUICK:
          - 不降级（已是最低）
    """
    failures = [r for r in stage_results if not r.success]

    if not failures:
        return DegradationDecision(
            degraded=False,
            original_depth=original_depth,
            target_depth=original_depth,
            target_fold_depth=_depth_to_fold(original_depth),
            reason="全部阶段成功"
        )

    failed_stages = {r.stage for r in failures}
    failed_names = [r.stage.value for r in failures]

    if original_depth == QueryDepth.DEEP:
        # 关键阶段失败 → QUICK
        if failed_stages & _CRITICAL_STAGES:
            return DegradationDecision(
                degraded=True,
                original_depth=QueryDepth.DEEP,
                target_depth=QueryDepth.QUICK,
                target_fold_depth=0,
                reason=f"关键阶段失败: {[s.value for s in (failed_stages & _CRITICAL_STAGES)]} → QUICK",
                failed_stages=failed_names,
            )
        # 仅研究/图谱失败 → STANDARD
        return DegradationDecision(
            degraded=True,
            original_depth=QueryDepth.DEEP,
            target_depth=QueryDepth.STANDARD,
            target_fold_depth=2,
            reason=f"非关键阶段失败: {failed_names} → STANDARD",
            failed_stages=failed_names,
        )

    if original_depth == QueryDepth.STANDARD:
        if failed_stages & {PipelineStage.DUALITY_DETECTION}:
            return DegradationDecision(
                degraded=True,
                original_depth=QueryDepth.STANDARD,
                target_depth=QueryDepth.QUICK,
                target_fold_depth=0,
                reason=f"二重性检测失败 → QUICK",
                failed_stages=failed_names,
            )
        # 其余失败保持 STANDARD
        return DegradationDecision(
            degraded=True,
            original_depth=QueryDepth.STANDARD,
            target_depth=QueryDepth.STANDARD,
            target_fold_depth=2,
            reason=f"非关键阶段失败: {failed_names} → 保持 STANDARD（降级标记）",
            failed_stages=failed_names,
        )

    # QUICK 不降级
    return DegradationDecision(
        degraded=False,
        original_depth=QueryDepth.QUICK,
        target_depth=QueryDepth.QUICK,
        target_fold_depth=0,
        reason="已是 QUICK，不降级",
        failed_stages=failed_names,
    )


# ═══════════════════════════════════════════
# 快捷响应生成（QUICK 路径）
# ═══════════════════════════════════════════

QUICK_TEMPLATES = {
    "greeting":  ["嗯。", "说。"],
    "thanks":    ["不必。"],
    "bye":       ["走。", "再见。"],
    "fact":      ["无实时数据。需要工具支持。"],
    "agree":     ["是。"],
    "tool":      ["需要更具体的指令。"],

    # 对有微弱二重性但被路由到 QUICK 的回复：
    # 仍然保持并置而非缝合——这是 Constitutional DNA I 的底线
    "weak_duality": [
        "取决于视角。展开说？",
    ],
}

def quick_response(query: str, has_weak_duality: bool = False) -> str:
    """生成 QUICK 模式的极简回复。

    仍然遵循 Constitutional DNA 禁止第一人称、禁止呼告、禁止鸡汤的底线。
    """
    import random

    q = query.strip().lower()

    # 分类匹配
    if re.search(r'^(你好|嗨|hello|hi)\b', q):
        return random.choice(QUICK_TEMPLATES["greeting"])
    if re.search(r'^(谢谢|thanks?|thank)\b', q):
        return random.choice(QUICK_TEMPLATES["thanks"])
    if re.search(r'^(再见|bye|晚安)\b', q):
        return random.choice(QUICK_TEMPLATES["bye"])
    if re.search(r'^(好|行|ok|okay|对|是的|明白|got)\b', q):
        return random.choice(QUICK_TEMPLATES["agree"])
    if re.search(r'^[😀-🙏👀-🙌🚀-🛸]+$', q):
        return "…"

    # 弱二重性（detect_dual_nature 命中了但学术标记不够）
    if has_weak_duality:
        return random.choice(QUICK_TEMPLATES["weak_duality"])

    # 默认
    if len(q) <= 10:
        return "…？"
    return "无足够信息做出有意义的回应。"


# ═══════════════════════════════════════════
# 辅助
# ═══════════════════════════════════════════

def _count_markers(text: str, patterns: List[str]) -> int:
    """对一组正则模式计数命中次数（不重复计数同一位置）"""
    count = 0
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        count += len(matches)
    return count


def _depth_to_fold(depth: QueryDepth) -> int:
    """深度枚举 → fold_depth 数值"""
    return {
        QueryDepth.QUICK: 0,
        QueryDepth.STANDARD: 2,
        QueryDepth.DEEP: 5,
    }[depth]


# ═══════════════════════════════════════════
# 顶层路由入口 — 供 orchestrator 直接调用
# ═══════════════════════════════════════════

def detect_dual_nature(query: str) -> tuple:
    """
    检测 query 的二重性。

    Returns:
        (has_duality: bool, tension_type: Optional[str], duality_score: int)
    """
    duality_score = _count_markers(query, DUALITY_SIGNALS)

    # 基本判断：二重性信号 >= 1
    has_duality = duality_score >= 1

    # 尝试推断张力类型
    tension_type = None
    if has_duality:
        tension_type = _infer_tension_type(query)

    return has_duality, tension_type, duality_score


def _infer_tension_type(query: str) -> Optional[str]:
    """从 query 文本推断张力类型。"""
    q = query.lower()

    # 时间性
    if re.search(r'时间|过去|未来|现在|永恒|瞬间|线性|循环|历史', q):
        return 'temporal'

    # 存在性
    if re.search(r'存在|意义|虚无|荒谬|死亡|自由|选择|孤独|本质', q):
        return 'existential'

    # 社会性
    if re.search(r'社会|制度|规范|权力|身份|阶层|关系|他人|公共', q):
        return 'social'

    # 政治性
    if re.search(r'政治|权力|治理|正义|平等|压迫|解放|革命|意识形态', q):
        return 'political'

    # 经济怪诞
    if re.search(r'资本|商品|消费|市场|货币|价值|劳动|异化|拜物教', q):
        return 'economic_grotesque'

    # 真理构建
    if re.search(r'真理|知识|话语|叙事|建构|真|假|事实|虚构|表象|现实', q):
        return 'truth_construction'

    return None


def route_query(query: str) -> 'DepthAssessment':
    """路由入口：一站式二重性检测 + 深度评估。"""
    has_duality, tension_type, _ = detect_dual_nature(query)
    return assess_query_depth(query, has_duality, tension_type)


def evaluate_degradation_result(stage: str, error: Optional[str] = None) -> 'DegradationDecision':
    """评估管线阶段失败后的降级决策。"""
    return evaluate_degradation(stage, error)
