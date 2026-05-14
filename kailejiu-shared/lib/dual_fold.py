"""
KL9-RHIZOME 递归二重折叠 — dual_fold 核心操作。

从两个不可调和视角同时 transform，识别结构性张力，递归至悬置。
"""

from core_structures import DualState, Tension, Perspective, SuspensionAssessment
from suspension_evaluator import evaluate_suspension


def transform_from_perspective(query: str, perspective: Perspective, dialogues: list, state=None) -> str:
    """从指定视角 transform query。

    Args:
        query: 用户查询或原文（翻译模式）
        perspective: 视角对象
        dialogues: 激活的理论对话列表
        state: 可选 DualState，翻译模式下从中提取 term_bindings/source_text

    Returns:
        transform 文本 — 从该视角出发对 query 的重述/解读/翻译。
    """
    if perspective is None:
        return query

    chars = perspective.characteristics if perspective.characteristics else [perspective.name]
    char_str = "、".join(chars[:3])

    # ── 翻译模式 ──
    if state and state.mode == "translation":
        bindings_hint = ""
        if state.term_bindings:
            pairs = "；".join(f"{k}→{v}" for k, v in list(state.term_bindings.items())[:10])
            bindings_hint = "\n已锁定术语（必须沿用）: " + pairs + "\n"

        return f"""[翻译视角: {perspective.name}]
特征: {char_str}{bindings_hint}

原文:
{query}

要求:
- 严格以{perspective.name}的立场翻译这段文字
- 术语一致性: 已锁定术语必须使用指定译名
- 不折中: 不在两种翻译哲学间寻求妥协
- 保留该视角下特有的句法和措辞选择
- 输出仅译文，不附加解释
"""

    # ── 默认模式（理论分析） ──
    dialogue_hints = ""
    if dialogues:
        theories = [d.get("theory", d.get("name", "")) for d in dialogues[:2] if d.get("theory") or d.get("name")]
        thinkers = [d.get("thinker", "") for d in dialogues[:2] if d.get("thinker")]
        if theories:
            dialogue_hints = f"可以征用的理论资源: {', '.join(theories)}"
            if thinkers:
                dialogue_hints += f"（{', '.join(t for t in thinkers if t)}）"

    return f"""[视角: {perspective.name}]
特征: {char_str}
{dialogue_hints}

从上述视角重新审视: {query}

要求:
- 严格保持该视角的内在逻辑，不被其他视角"说服"
- 揭示该视角下特有的不可见之物
- 不缝合矛盾，不寻求折中
"""


def structural_tension(
    perspective_A: Perspective,
    perspective_B: Perspective,
    claim_A: str,
    claim_B: str,
    tension_type: str,
) -> Tension:
    """构建结构性张力对象。

    Args:
        perspective_A: A 视角
        perspective_B: B 视角
        claim_A: A 视角的核心主张
        claim_B: B 视角的核心主张
        tension_type: 张力类型标识

    Returns:
        Tension 对象
    """
    # 从两个主张中提取不可调和点
    irreconcilable = []

    a_name = perspective_A.name if perspective_A else "A"
    b_name = perspective_B.name if perspective_B else "B"

    # 基础不可调和点：两个视角本身的定义即是矛盾
    irreconcilable.append(f"{a_name} 与 {b_name} 的认知框架不可通约")

    # 若两个主张方向相反，记录
    if claim_A and claim_B:
        irreconcilable.append(f"A主张: {claim_A[:80]}... vs B主张: {claim_B[:80]}...")

    return Tension(
        perspective_A=a_name,
        perspective_B=b_name,
        claim_A=claim_A[:200] if claim_A else "",
        claim_B=claim_B[:200] if claim_B else "",
        irreconcilable_points=irreconcilable,
        tension_type=tension_type,
    )


def extract_claim(transform: str) -> str:
    """从 transform 文本中提取核心主张。"""
    if not transform:
        return ""
    # 简易提取：取 transform 的第一句实质性陈述
    lines = [l.strip() for l in transform.split("\n") if l.strip() and not l.strip().startswith("[")]
    for line in lines:
        if len(line) > 15:
            return line[:200]
    return lines[0][:200] if lines else ""


def infer_tension_type(pa_name: str, pb_name: str) -> str:
    """从两个视角名称推断张力类型。"""
    from perspective_types import FAMILY_TENSION_MAP

    # 提取 family
    pa_family = pa_name.split(".")[0] if "." in pa_name else pa_name
    pb_family = pb_name.split(".")[0] if "." in pb_name else pb_name

    return FAMILY_TENSION_MAP.get((pa_family, pb_family), "")


def dual_fold(state: DualState, depth: int = 0, max_depth: int = 3, provider=None) -> DualState:
    """递归二重折叠 — KL9-RHIZOME 的核心操作。

    v1.5 特性:
        - 折叠逻辑内聚在 DualState 操作中
        - max_depth 由 fold_depth_policy 动态决定
        - 超过 max_depth → forced=True（仍保持张力，不缝合）

    Args:
        state: 当前 DualState
        depth: 当前折叠深度
        max_depth: 最大折叠深度
        provider: LLM provider（可选，用于实际生成 transform）

    Returns:
        更新后的 DualState（suspended=True 时停止递归）
    """
    # Step 1: 从两个视角同时 transform
    transform_a = transform_from_perspective(
        state.query, state.perspective_A, state.activated_dialogue, state=state
    )
    transform_b = transform_from_perspective(
        state.query, state.perspective_B, state.activated_dialogue, state=state
    )

    # Step 2: 识别结构性张力
    tt = state.tension_type or infer_tension_type(
        state.perspective_A.name if state.perspective_A else "",
        state.perspective_B.name if state.perspective_B else ""
    )

    tension = structural_tension(
        perspective_A=state.perspective_A,
        perspective_B=state.perspective_B,
        claim_A=extract_claim(transform_a),
        claim_B=extract_claim(transform_b),
        tension_type=tt,
    )
    state.tension = tension
    state.tension_type = tt
    state.fold_depth = depth

    # Step 3: 尝试悬置
    assessment = evaluate_suspension(transform_a, transform_b, tension)

    if assessment.can_express:
        state.suspended = True
        return state

    # Step 4: 达到最大深度 → 强制悬置
    if depth >= max_depth:
        state.suspended = True
        state.forced = True
        return state

    # Step 5: 未悬置 → 细化视角，递归
    # 在当前实现中，细化视角通过向 activated_dialogue 追加更多理论实现
    new_dialogues = []
    if assessment.improvement_hints:
        for hint in assessment.improvement_hints:
            new_dialogues.append({
                "theory": hint,
                "thinker": "",
                "original_frame": hint,
                "transformed_frame": hint,
                "transformation_tension": "",
            })

    # 保持原视角不变（实际细化应由外部 LLM 调用完成）
    # 此处递归推进折叠深度
    new_state = DualState(
        query=state.query,
        perspective_A=state.perspective_A,
        perspective_B=state.perspective_B,
        activated_dialogue=state.activated_dialogue + new_dialogues,
        tension=tension,
        tension_type=tt,
        suspended=False,
        forced=False,
        fold_depth=depth + 1,
        max_fold_depth=max_depth,
        source_skill=state.source_skill,
    )

    return dual_fold(new_state, depth + 1, max_depth, provider)
