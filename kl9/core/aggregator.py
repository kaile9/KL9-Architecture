"""
9R-2.1 — TensionPreservingAggregator

Assembles final output from fold chain.
Preserves all [硬张力]/[软张力] markers from every fold step.
Appends quality metadata block.
"""

from __future__ import annotations

from ..models import (
    AggregatedOutput,
    FoldChain,
    QualityScore,
)
from .dna import (
    extract_tensions,
    extract_umkehrs,
    VALID_ENDINGS,
    dedup_markers,
    strip_backstage,
)


class TensionPreservingAggregator:
    def aggregate(self, chain: FoldChain, quality: QualityScore | None = None) -> AggregatedOutput:
        """Assemble final output from fold chain with tension preservation.

        Strategy:
        - Use the last fold's B perspective content as main body
        - Append all unique [硬张力] markers from entire chain
        - If ending is invalid, append ellipsis
        - Attach quality metadata
        """
        # Get final fold content, strip architecture tags for user-facing output
        if chain.folds:
            last_fold = chain.folds[-1]
            body = strip_backstage(last_fold.raw_content)
        else:
            body = ""

        # Collect all tensions and umkehrs (deduped across the chain)
        all_tensions = dedup_markers(chain.all_tensions)
        all_umkehrs = dedup_markers(chain.all_umkehrs)

        # Ensure ending is valid
        body = self._ensure_ending(body)

        # Append tension appendix
        if all_tensions:
            body += "\n\n---\n"
            body += "\n".join(f"  {t}" for t in all_tensions[-5:])  # Last 5 tensions

        # Collect theorists and concepts
        theorists: set[str] = set()
        concepts: set[str] = set()
        for fold in chain.folds:
            theorists.update(fold.perspective_a.theorists_cited)
            theorists.update(fold.perspective_b.theorists_cited)
            concepts.update(fold.perspective_a.concepts_used)
            concepts.update(fold.perspective_b.concepts_used)

        constitutional_warning = False
        if quality and quality.constitutional_violations:
            constitutional_warning = True

        return AggregatedOutput(
            content=body,
            tension_markers=all_tensions[-5:] if all_tensions else [],
            umkehr_markers=all_umkehrs[-3:] if all_umkehrs else [],
            fold_depth=chain.fold_count,
            quality=quality,
            theorists_cited=sorted(theorists),
            concepts_used=sorted(concepts),
            token_used=chain.total_tokens,
            latency_ms=chain.total_latency_ms,
            constitutional_warning=constitutional_warning,
        )

    @staticmethod
    def _ensure_ending(text: str) -> str:
        """Ensure text ends with valid ending, not period."""
        stripped = text.rstrip()
        if not stripped:
            return text
        last = stripped[-1]
        if last == "。":
            return stripped[:-1] + "……"
        if last.isalpha() and last not in "……?？—":
            return stripped + "……"
        return stripped
