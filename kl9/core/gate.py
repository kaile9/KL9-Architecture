"""
9R-2.1 — Quality Gate (Rule-Engine Only)

Lightweight intermediate inspection running at each fold step.
Detects: forbidden patterns, citation density, ending validity.
NO LLM calls — pure regex + heuristics.

Separated from Validator (LLM-as-judge final check).
"""

from __future__ import annotations

from .dna import (
    detect_forbidden,
    count_citations,
    validate_ending,
    extract_tensions,
    extract_umkehrs,
)


class QualityGate:
    """Rule-based quality gate for intermediate fold steps."""

    def __init__(self):
        self.max_forbidden_for_pass = 2

    def inspect(self, content: str) -> tuple[bool, list[str], dict]:
        violations: list[str] = []
        metrics: dict = {}

        # 1. Forbidden pattern detection
        forbidden = detect_forbidden(content)
        metrics["forbidden_count"] = len(forbidden)
        for pattern, desc in forbidden:
            violations.append(f"FORBIDDEN: {desc}")

        # 2. Summary ratio check (P7: ≤5% pure summary)
        summary_ratio = self._summary_ratio(content)
        metrics["summary_ratio"] = summary_ratio
        if summary_ratio > 0.05:
            violations.append(f"SUMMARY_OVERLOAD: {summary_ratio:.1%} pure summary (>5%)")

        # 3. Ending validation
        if not validate_ending(content):
            violations.append("ENDING_VIOLATION: period ending or empty")

        # 4. Tension markers
        tensions = extract_tensions(content)
        umkehrs = extract_umkehrs(content)
        metrics["tension_count"] = len(tensions)
        metrics["umkehr_count"] = len(umkehrs)

        passed = len(violations) <= self.max_forbidden_for_pass
        return passed, violations, metrics

    @staticmethod
    def _summary_ratio(content: str) -> float:
        """Estimate pure summary ratio via sentence-level marker detection.

        Old algorithm accumulated 80-char windows per marker, causing overlap
        double-counting when multiple markers appeared close together.  The
        new approach splits into sentences and counts each sentence at most
        once.
        """
        import re as _re
        summary_markers: set[str] = {
            "综上所述", "总而言之", "由此可见", "以上分析表明",
            "总的来说", "简而言之", "一言以蔽之", "值得指出的是",
            "应当指出", "可以看出", "总的来看", "综上",
        }
        # Split into sentence-ish units (Chinese period / newline / comma)
        sentences = _re.split(r"[。\n，；;]", content)
        summary_chars = 0
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if any(m in s for m in summary_markers):
                summary_chars += len(s)
        total = max(1, len(content))
        return min(1.0, summary_chars / total)
