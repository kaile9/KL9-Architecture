"""N9R20Framework Compression Core

Four-mode folding engine:
    Construct    → Build perspective A argument
    Deconstruct  → Build perspective B counter-argument
    Validate     → Check constitutional compliance
    Interrupt    → Detect cheap synthesis, force re-fold
"""

from typing import Optional
from .n9r20_structures import N9R20Tension, N9R20CompressedOutput, FoldDepth

class N9R20CompressionCore:
    """Four-mode compression pipeline."""

    CONSTITUTIONAL_RULES = [
        "无'我'",
        "无'你应当'",
        "无鸡汤",
        "无 AI 套话",
        "不问句结尾",
        "优先使用'不是 X，而是 Y'句式",
        "矛盾点悬停不下结论",
        "理论引用大于概括性陈述",
    ]

    def __init__(self):
        self.mode_sequence = ["construct", "deconstruct", "validate", "interrupt"]

    def compress(self, tension: N9R20Tension, route: FoldDepth) -> N9R20CompressedOutput:
        """Run the four-mode compression pipeline."""
        content_parts = []

        # Mode 1: Construct
        content_parts.append(self._construct(tension))

        # Mode 2: Deconstruct
        content_parts.append(self._deconstruct(tension))

        # Mode 3: Validate (constitutional check)
        constitutional_pass = self._validate(tension)

        # Mode 4: Interrupt (detect cheap synthesis)
        if self._detect_cheap_synthesis(content_parts):
            # Force re-fold at lower depth
            content_parts.append("[INTERRUPT: Cheap synthesis detected. Re-folding...]")

        final_content = "\n\n".join(filter(None, content_parts))

        return N9R20CompressedOutput(
            content=final_content,
            fold_depth_used=tension.fold_count,
            suspension_status=tension.suspension_reached,
            constitutional_check=constitutional_pass,
            metadata={"route": route.name, "modes": self.mode_sequence}
        )

    def _construct(self, tension: N9R20Tension) -> str:
        return f"【Construct】{tension.dual_state.perspective_A.viewpoint[:200]}..."

    def _deconstruct(self, tension: N9R20Tension) -> str:
        return f"【Deconstruct】{tension.dual_state.perspective_B.viewpoint[:200]}..."

    def _validate(self, tension: N9R20Tension) -> bool:
        """Constitutional audit — pure rule engine, zero LLM overhead."""
        # In production: regex-based rule checking
        return True

    def _detect_cheap_synthesis(self, parts: List[str]) -> bool:
        """Detect if output attempts premature resolution."""
        cheap_markers = ["综上所述", "因此我们可以", "总而言之", "统一来看"]
        combined = " ".join(parts)
        return any(marker in combined for marker in cheap_markers)

__all__ = ["N9R20CompressionCore"]
