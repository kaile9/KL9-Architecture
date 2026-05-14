"""Tests for tension marker normalization & dedup (Bug-4, Bug-5)."""
import pytest

from kl9.core.dna import normalize_tension, dedup_markers
from kl9.core.fold import FoldEngine


# ── Normalization ──

class TestNormalize:
    def test_strips_direction_prefix(self):
        # Bug-4: decomposer adds "(A->B):" but fold output doesn't —
        # both forms must canonicalize to the same key
        a = "[硬张力](A->B): X 与 Y 不可调和"
        b = "[硬张力]: X 与 Y 不可调和"
        c = "[硬张力] X 与 Y 不可调和"
        assert normalize_tension(a) == normalize_tension(b) == normalize_tension(c)

    def test_strips_soft_tension_tag(self):
        a = "[软张力]: 视角差异"
        b = "[软张力] 视角差异"
        assert normalize_tension(a) == normalize_tension(b)

    def test_collapses_whitespace(self):
        a = "[硬张力]:  A   与    B"
        b = "[硬张力]: A 与 B"
        assert normalize_tension(a) == normalize_tension(b)

    def test_case_folded(self):
        assert normalize_tension("[硬张力]: ABC") == normalize_tension("[硬张力]: abc")

    def test_chinese_colon(self):
        a = "[硬张力]：X 与 Y"
        b = "[硬张力]: X 与 Y"
        assert normalize_tension(a) == normalize_tension(b)

    def test_empty(self):
        assert normalize_tension("") == ""
        assert normalize_tension("[硬张力]") == ""

    def test_full_chinese_direction(self):
        a = "[硬张力](B -> A) ：abc"
        b = "[硬张力]: abc"
        assert normalize_tension(a) == normalize_tension(b)


# ── Dedup ──

class TestDedupMarkers:
    def test_dedups_after_normalization(self):
        markers = [
            "[硬张力](A->B): X 与 Y",
            "[硬张力]: X 与 Y",          # same kernel
            "[硬张力] X 与 Y",            # same kernel
            "[硬张力]: A 与 B",          # different
        ]
        out = dedup_markers(markers)
        assert len(out) == 2
        # First-seen winner
        assert out[0] == "[硬张力](A->B): X 与 Y"
        assert out[1] == "[硬张力]: A 与 B"

    def test_skips_empty_kernels(self):
        out = dedup_markers(["", "[硬张力]", "[硬张力]: real"])
        assert len(out) == 1
        assert out[0] == "[硬张力]: real"


# ── Fold parser dedup (Bug-5) ──

class TestFoldParserDedup:
    def test_parser_double_walk_no_longer_duplicates(self):
        engine = FoldEngine(llm=None)  # parser doesn't call llm
        content = """[视角A深化]
A的内容

[视角B深化]
B的内容

[碰撞]
[硬张力]: 重复张力
[硬张力]: 另一个张力
"""
        pa, pb, tensions, umkehrs = engine._parse_fold(content)
        # Pre-fix: parser collected each marker twice (line-scan + regex extract)
        # Post-fix: dedup_markers compresses to unique kernels
        assert len(tensions) == 2
        keys = [normalize_tension(t) for t in tensions]
        assert "重复张力" in keys[0] or "重复张力" in keys[1]
