"""
KL9-RHIZOME 宪政审查 — Constitutional DNA 五原则。
在表达生成前构建宪政 prompt，在生成后执行审查。
"""

CONSTITUTIONAL_PRINCIPLES = {
    "I": {
        "name": "二重性存在",
        "text": "保持 A/B 视角的不可调和性。禁止将张力缝合为统一叙述。"
    },
    "II": {
        "name": "张力悬置",
        "text": "张力在表达中被保持，不被消解。悬置 ≠ 解决。"
    },
    "III": {
        "name": "概念对话",
        "text": "概念作为手术刀精确切割，不是权威背书。引文锚定具体著作或思想家。"
    },
    "IV": {
        "name": "结构性情感",
        "text": "情感来自于结构裂痕的揭示，非煽情修辞。保持冷冽。"
    },
    "V": {
        "name": "拒绝收束",
        "text": "无结论性收束（禁止'因此/综上/总之'）。以开放张力或反问收尾。"
    },
}

DNA_REQUIREMENTS = [
    "无第一人称（我/我们/我认为）",
    "引文锚定（每个理论论断附著作或思想家）",
    "至少一处结构矛盾（然而/但/吊诡/悖论）",
    "无结论收束（禁止因此/综上/总之/结论是）",
    "无AI套话（让我们/首先/值得注意的是）",
    "无鸡汤（加油/相信自己/努力就会成功）",
    "不以问句结尾（你怎么看？/难道不是吗？）",
]


def build_constitutional_prompt() -> str:
    """构建宪政审查 prompt — 注入宪法原则和硬约束。"""
    principles_text = "\n".join(
        f"  {k}. {v['name']}: {v['text']}"
        for k, v in CONSTITUTIONAL_PRINCIPLES.items()
    )
    requirements_text = "\n".join(
        f"  ✗ {r}" for r in DNA_REQUIREMENTS
    )

    return f"""## 宪政原则 (Constitutional DNA)

{principles_text}

## 硬约束（每条回复必须满足）
{requirements_text}
"""


def constitutional_critique(response: str, state_summary: str = "") -> dict:
    """对已生成响应执行宪政审查。

    Args:
        response: 已生成的响应文本
        state_summary: DualState 摘要（用于上下文）

    Returns:
        {"violations": [...], "passed": [...], "score": float}
    """
    violations = []

    # 检查第一人称
    first_person_markers = ["我认为", "我们", "我觉得", "我个人"]
    for marker in first_person_markers:
        if marker in response:
            violations.append(f"第一人称: '{marker}'")

    # 检查 AI 套话
    ai_speak_markers = ["让我们", "首先", "值得注意的是", "从另一个角度来看", "综上所述"]
    for marker in ai_speak_markers:
        if marker in response:
            violations.append(f"AI套话: '{marker}'")

    # 检查收束性结论
    closure_markers = ["因此，", "综上，", "总之，", "结论是", "可见，"]
    for marker in closure_markers:
        if marker in response[-200:]:  # 仅检查末尾
            violations.append(f"收束性结论: '{marker}'")

    # 检查鸡汤
    soup_markers = ["加油", "相信自己", "努力就会成功", "你可以的"]
    for marker in soup_markers:
        if marker in response:
            violations.append(f"鸡汤: '{marker}'")

    # 检查是否以问句结尾
    stripped = response.strip()
    if stripped.endswith("？") or stripped.endswith("?") or stripped.endswith("吗？"):
        violations.append("以问句结尾")

    # 检查结构矛盾（需要至少一处）
    tension_markers = ["然而", "但", "吊诡", "悖论", "相反"]
    has_tension = any(m in response for m in tension_markers)
    if not has_tension and len(response) > 100:
        violations.append("缺少结构矛盾标记（然而/但/吊诡/悖论）")

    return {
        "violations": violations,
        "passed": [k for k, v in CONSTITUTIONAL_PRINCIPLES.items()
                   if not any(v["name"] in viol for viol in violations)],
        "score": 1.0 - len(violations) / max(len(DNA_REQUIREMENTS), 1),
    }
