"""
KL9-RHIZOME 折叠深度策略 — 根据张力类型和 query 长度动态确定 max_fold_depth。
"""


def determine_max_fold_depth(query: str, tension_type: str = "", base_depth: int = 2) -> int:
    """根据 query 特性动态确定最大折叠深度。

    影响因素:
        - 张力类型的认知负载基数
        - query 长度（长 query 通常含更多维度）

    返回: [1, 5] 范围内的整数。
    """
    tension_depth_map = {
        "eternal_vs_finite": 3,
        "mediated_vs_real": 3,
        "regression_vs_growth": 2,
        "freedom_vs_security": 2,
        "economic_vs_grotesque": 3,
        "truth_vs_slander": 3,
        "": 1,
    }

    base = tension_depth_map.get(tension_type, 2)

    # 根据 query 长度微调
    if len(query) > 200:
        base = min(base + 1, 5)
    elif len(query) < 30:
        base = max(base - 1, 1)

    return min(max(base, 1), 5)
