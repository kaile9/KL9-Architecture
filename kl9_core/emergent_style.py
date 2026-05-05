"""
KL9-RHIZOME 涌现风格 — 从张力类型涌现表达风格指导。
"""

from perspective_types import TENSION_TYPES, EMERGENT_STYLE_MAP


def emergent_style(tension_type: str) -> dict:
    """从张力类型涌现表达风格指导。"""
    tt = TENSION_TYPES.get(tension_type, {"emergent_style": "analytical_juxtaposition"})
    style_key = tt.get("emergent_style", "analytical_juxtaposition")
    return EMERGENT_STYLE_MAP.get(style_key, EMERGENT_STYLE_MAP["analytical_juxtaposition"])


def emergent_style_prompt(tension_type: str) -> str:
    """生成风格注入 prompt。"""
    style = emergent_style(tension_type)
    return f"""## 涌现风格: {tension_type}
句法: {style['syntax']}
语气: {style['tone']}
收束: {style['closure']}"""
