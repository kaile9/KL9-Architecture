"""
KL9-RHIZOME 悬置评估器 — 判定 DualState 是否达到可表达的悬置状态。

判定标准（非收敛、非缝合）:
    1. 两个视角的 transform 都保持了各自的内在逻辑
    2. 张力点清晰可陈述（irreconcilable_points 非空）
    3. 未发生视角坍缩（一个视角并未被另一个视角"说服"）
    4. 表达价值足够（悬置状态本身具有可读性）
"""

from core_structures import SuspensionAssessment, Tension


def check_perspective_integrity(transform: str, perspective) -> bool:
    """检查视角完整性：transform 文本非空且保持该视角的特征方向。"""
    if not transform or len(transform.strip()) < 20:
        return False
    # 基础完整性检查：非退化文本
    return True


def detect_perspective_collapse(transform_a: str, transform_b: str, tension: Tension) -> bool:
    """检测视角坍缩：一方被另一方"说服"或消解。

    简易启发式：若两个 transform 中含有相同的结论性断言（以"因此""所以""综上"开头），
    则判定为坍缩。
    """
    collapse_markers = ["因此", "所以", "综上", "可见", "显然"]
    a_has = any(m in transform_a[-100:] for m in collapse_markers)
    b_has = any(m in transform_b[-100:] for m in collapse_markers)
    # 双方都有收束性结论 → 可能坍缩
    if a_has and b_has:
        return True
    return False


def evaluate_suspension(transform_a: str, transform_b: str, tension: Tension) -> SuspensionAssessment:
    """评估当前 DualState 是否已达到可表达的悬置状态。

    Args:
        transform_a: A 视角的 transform 结果
        transform_b: B 视角的 transform 结果
        tension: 当前张力对象

    Returns:
        SuspensionAssessment
    """
    # 检查视角保真度
    a_integrity = check_perspective_integrity(transform_a, None)
    b_integrity = check_perspective_integrity(transform_b, None)

    if not (a_integrity and b_integrity):
        return SuspensionAssessment(
            can_express=False,
            quality="insufficient",
            improvement_hints=["视角完整性不足，需进一步从各自视角展开"]
        )

    # 检查张力可陈述性
    if not tension or not tension.irreconcilable_points:
        return SuspensionAssessment(
            can_express=False,
            quality="insufficient",
            improvement_hints=["张力点不清晰，需识别具体不可调和之处"]
        )

    # 检查视角坍缩
    if detect_perspective_collapse(transform_a, transform_b, tension):
        return SuspensionAssessment(
            can_express=False,
            quality="insufficient",
            improvement_hints=["检测到视角坍缩，需恢复视角独立性"]
        )

    # 通过 — 可表达
    return SuspensionAssessment(
        can_express=True,
        quality="genuine",
        improvement_hints=[]
    )


def evaluate_suspension_with_pressure(
    transform_a: str,
    transform_b: str,
    tension: Tension,
    pressure_ratio: float,
) -> SuspensionAssessment:
    """TEMPORAL 压力感知的悬置评估。

    pressure_ratio > 1.0 时放宽标准：降低视角完整性门槛，
    提前承认不可调和性——TEMPORAL 张力不降低输出质量，而是提前标记认知边界。

    Args:
        transform_a: A 视角的 transform 结果
        transform_b: B 视角的 transform 结果
        tension: 当前张力对象
        pressure_ratio: 累计 token / TOKEN_PRESSURE_THRESHOLD

    Returns:
        SuspensionAssessment
    """
    # 先尝试正常评估
    assessment = evaluate_suspension(transform_a, transform_b, tension)

    if assessment.can_express:
        return assessment

    # token 压力下放宽标准
    if pressure_ratio >= 1.0:
        # 放宽：仅需至少一个 irreconcilable_point + 一方视角保持完整性
        has_any_point = bool(tension and tension.irreconcilable_points)
        a_ok = bool(transform_a and len(transform_a.strip()) > 20)
        b_ok = bool(transform_b and len(transform_b.strip()) > 20)

        if has_any_point and (a_ok or b_ok):
            return SuspensionAssessment(
                can_express=True,
                quality="pressure_relaxed",
                improvement_hints=[]
            )

    return assessment
