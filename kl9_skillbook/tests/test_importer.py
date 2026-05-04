"""Tests for KL9-RHIZOME skillbook absorption protocol v1.1."""

import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kl9_skillbook.models import ConceptNode, ConceptProvenance, CollisionReport, ProductionRecord
from kl9_skillbook.validator import validate_manifest
from kl9_skillbook.matcher import levenshtein_ratio, detect_collisions
from kl9_skillbook.merger import merge_graphs
from kl9_skillbook.tension import get_subgraph, recalculate_tension_local
from kl9_skillbook.importer import import_skill_book
from kl9_skillbook.scorer import (
    calculate_trust, classify_trust_level,
    estimate_difficulty, estimate_quality,
)


# ═══════════════════════ helpers ═══════════════════════

def _make_skillbook_json(manifest_overrides=None, concepts=None):
    manifest = {
        "skill_book_id": "test_book",
        "version": "1.1",
        "quality_tier": 4,
        "difficulty": 50.0,
        "quality_score": 60.0,
        "llm_source": "claude",
        "kl9_version": "0.1.0",
        "created_timestamp": int(time.time()),
        "book_title": "Test Book",
        "concept_count": len(concepts) if concepts else 0,
        "production_record": {
            "rounds_completed": 2,
            "verification_method": "spot-check",
            "counter_perspectives": [],
            "total_hours": 10.0,
        },
    }
    if manifest_overrides:
        manifest.update(manifest_overrides)
    return {"manifest": manifest, "concepts": concepts or {}}


def _make_skillbook_json_v10(manifest_overrides=None, concepts=None):
    """Build a v1.0 format skillbook for backward compat testing."""
    manifest = {
        "skill_book_id": "test_book",
        "version": "1.0",
        "quality_tier": 4,
        "llm_source": "claude",
        "kl9_version": "0.1.0",
        "created_timestamp": int(time.time()),
        "book_title": "Test Book",
        "concept_count": len(concepts) if concepts else 0,
    }
    if manifest_overrides:
        manifest.update(manifest_overrides)
    return {"manifest": manifest, "concepts": concepts or {}}


def _make_local_graph_json(concepts=None, meta=None):
    return {"meta": meta or {}, "concepts": concepts or {}}


def _cnode(cid, name, definition="def", p_a="pa", p_b="pb",
           tension=0.5, edges=None, local_conf=1.0,
           is_shadow=False, shadow_of=None):
    return ConceptNode(
        concept_id=cid, name=name, definition=definition,
        perspective_a=p_a, perspective_b=p_b,
        tension_score=tension, edges=edges or [],
        local_confidence=local_conf,
        is_shadow=is_shadow, shadow_of=shadow_of,
    )


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# ═══════════════════ Levenshtein ═══════════════════

class TestLevenshtein:
    def test_identical(self):
        assert levenshtein_ratio("hello", "hello") == 1.0

    def test_completely_different(self):
        assert levenshtein_ratio("abc", "xyz") < 0.5

    def test_one_char_diff(self):
        r = levenshtein_ratio("Geld", "Geldt")
        assert 0.75 < r < 1.0

    def test_empty_both(self):
        assert levenshtein_ratio("", "") == 1.0

    def test_empty_one(self):
        assert levenshtein_ratio("abc", "") == 0.0

    def test_case_sensitive(self):
        r = levenshtein_ratio("Concept", "concept")
        assert r < 1.0


# ═══════════════════ Manifest Validation ═══════════════════

class TestValidateManifest:
    def test_valid(self):
        ok, m, w = validate_manifest({
            "version": "1.0", "quality_tier": 3, "llm_source": "claude",
            "skill_book_id": "b1", "kl9_version": "0.1",
            "created_timestamp": 1700000000, "book_title": "T",
            "concept_count": 5,
        })
        assert ok and m is not None and m.quality_tier == 3

    def test_valid_v11(self):
        ok, m, w = validate_manifest({
            "version": "1.1", "quality_tier": 3, "llm_source": "claude",
            "skill_book_id": "b1", "kl9_version": "0.1",
            "created_timestamp": 1700000000, "book_title": "T",
            "concept_count": 5,
            "difficulty": 60.0, "quality_score": 75.0,
            "production_record": {
                "rounds_completed": 2,
                "verification_method": "spot-check",
                "counter_perspectives": ["A", "B"],
                "total_hours": 15.0,
            },
        })
        assert ok and m is not None
        assert m.difficulty == 60.0
        assert m.quality_score == 75.0
        assert m.production_record is not None
        assert m.production_record.rounds_completed == 2

    def test_v11_missing_difficulty(self):
        ok, m, w = validate_manifest({
            "version": "1.1", "quality_tier": 3,
            "quality_score": 75.0,
        })
        assert not ok
        assert "difficulty" in w[0].lower()

    def test_v11_difficulty_out_of_range(self):
        ok, m, w = validate_manifest({
            "version": "1.1", "quality_tier": 3,
            "difficulty": 150, "quality_score": 75.0,
        })
        assert not ok

    def test_v11_missing_quality_score(self):
        ok, m, w = validate_manifest({
            "version": "1.1", "quality_tier": 3,
            "difficulty": 50.0,
        })
        assert not ok
        assert "quality_score" in w[0].lower()

    def test_v11_missing_production_record_warning(self):
        ok, m, w = validate_manifest({
            "version": "1.1", "quality_tier": 3,
            "difficulty": 50.0, "quality_score": 75.0,
        })
        assert ok
        assert any("production_record" in x.lower() for x in w)

    def test_v11_production_rounds_invalid_warning(self):
        ok, m, w = validate_manifest({
            "version": "1.1", "quality_tier": 3,
            "difficulty": 50.0, "quality_score": 75.0,
            "production_record": {
                "rounds_completed": 0,
                "verification_method": "none",
                "counter_perspectives": [],
                "total_hours": 1.0,
            },
        })
        assert ok
        assert any("rounds_completed" in x.lower() for x in w)

    def test_missing_version(self):
        ok, m, w = validate_manifest({"quality_tier": 3})
        assert not ok and "version" in w[0].lower()

    def test_version_mismatch(self):
        ok, m, w = validate_manifest({"version": "0.9", "quality_tier": 3})
        assert not ok

    def test_missing_quality_tier(self):
        ok, m, w = validate_manifest({"version": "1.0"})
        assert not ok and "quality_tier" in w[0].lower()

    def test_invalid_quality_tier(self):
        ok, m, w = validate_manifest({"version": "1.0", "quality_tier": 6})
        assert not ok

    def test_unknown_llm_source_warning(self):
        ok, m, w = validate_manifest({
            "version": "1.0", "quality_tier": 2,
            "llm_source": "skynet-9000",
        })
        assert ok and any("llm_source" in x for x in w)

    def test_missing_timestamp_warning(self):
        ok, m, w = validate_manifest({
            "version": "1.0", "quality_tier": 4,
        })
        assert ok and any("timestamp" in x.lower() for x in w)

    def test_unknown_fields_warning(self):
        ok, m, w = validate_manifest({
            "version": "1.0", "quality_tier": 1,
            "llm_source": "gpt-4", "foo_bar": 42,
        })
        assert ok and any("foo_bar" in x for x in w)


# ═══════════════════ Collision Detection ═══════════════════

class TestDetectCollisions:
    def test_all_new(self):
        local = {"a": _cnode("a", "Alpha")}
        imported = {"sb::b": _cnode("sb::b", "Beta"),
                    "sb::c": _cnode("sb::c", "Gamma")}
        r = detect_collisions(local, imported)
        assert r.nodes_added == 2
        assert len(r.exact_collisions) == 0
        assert len(r.near_identical) == 0

    def test_exact_collision(self):
        local = {"a": _cnode("a", "Money")}
        imported = {"sb::m": _cnode("sb::m", "Money")}
        r = detect_collisions(local, imported)
        assert len(r.exact_collisions) == 1
        assert r.exact_collisions[0] == ("a", "sb::m")
        assert r.nodes_bifurcated == 1

    def test_near_identical(self):
        local = {"a": _cnode("a", "Geld als Denkform Analyse")}
        imported = {"sb::g": _cnode("sb::g", "Geld als Denkform Analyse!")}
        r = detect_collisions(local, imported)
        assert len(r.near_identical) == 1
        assert r.near_identical[0][2] >= 0.95

    def test_nearby_warning(self):
        local = {"a": _cnode("a", "System Design")}
        imported = {"sb::c": _cnode("sb::c", "System Designs")}
        r = detect_collisions(local, imported)
        assert len(r.nearby_warnings) >= 1

    def test_mixed(self):
        local = {"a": _cnode("a", "Alpha"), "b": _cnode("b", "Beta")}
        imported = {
            "sb::a2": _cnode("sb::a2", "Alpha"),    # exact
            "sb::b2": _cnode("sb::b2", "Betaa"),    # nearby (0.8)
            "sb::c":  _cnode("sb::c", "Gamma"),     # new
        }
        r = detect_collisions(local, imported)
        assert len(r.exact_collisions) == 1
        assert r.nodes_added >= 1


# ═══════════════════ Merge ═══════════════════

class TestMergeGraphs:
    def _prov(self):
        return ConceptProvenance("test_book", 4, "claude", int(time.time()))

    def test_add_new_nodes(self):
        local = {"a": _cnode("a", "Alpha")}
        imported = {"sb::b": _cnode("sb::b", "Beta")}
        report = CollisionReport([], [], [], 1, 0, [])
        merged = merge_graphs(local, imported, report, self._prov())
        assert "sb::b" in merged
        assert merged["sb::b"].local_confidence == 0.8

    def test_near_identical_merge(self):
        local = {"a": _cnode("a", "Geld", definition="Def A")}
        imported = {"sb::g": _cnode("sb::g", "Geld", definition="Def B")}
        report = CollisionReport([], [("a", "sb::g", 0.97)], [], 0, 0, [])
        merged = merge_graphs(local, imported, report, self._prov())
        assert "Def A" in merged["a"].definition
        assert "Def B" in merged["a"].definition
        assert "[来自test_book]" in merged["a"].definition

    def test_exact_collision_shadow(self):
        local = {"a": _cnode("a", "Money", definition="Def Local")}
        imported = {"sb::m": _cnode("sb::m", "Money", definition="Def Import")}
        report = CollisionReport([("a", "sb::m")], [], [], 0, 1, [])
        merged = merge_graphs(local, imported, report, self._prov())
        shadow_id = "m__shadow_test_book"
        assert shadow_id in merged
        assert merged[shadow_id].is_shadow is True
        assert merged[shadow_id].shadow_of == "a"
        assert merged[shadow_id].local_confidence == 0.8
        assert shadow_id in merged["a"].edges
        assert "a" in merged[shadow_id].edges

    def test_edges_merged(self):
        local = {"a": _cnode("a", "Alpha", edges=["b"]),
                 "b": _cnode("b", "Beta")}
        imported = {"sb::c": _cnode("sb::c", "Gamma", edges=["a", "b"])}
        report = CollisionReport([], [], [], 1, 0, [])
        merged = merge_graphs(local, imported, report, self._prov())
        assert "sb::c" in merged
        for e in merged["sb::c"].edges:
            assert e in merged


# ═══════════════════ Tension ═══════════════════

class TestTension:
    def test_get_subgraph(self):
        graph = {
            "a": _cnode("a", "A", edges=["b"]),
            "b": _cnode("b", "B", edges=["a", "c"]),
            "c": _cnode("c", "C", edges=["b", "d"]),
            "d": _cnode("d", "D", edges=["c", "e"]),
            "e": _cnode("e", "E", edges=["d"]),
        }
        sub = get_subgraph(graph, {"a"}, hop_radius=2)
        assert sub == {"a", "b", "c"}

    def test_recalculate_changes_tension(self):
        graph = {
            "a": _cnode("a", "A", edges=["b", "c"], tension=0.5),
            "b": _cnode("b", "B", tension=0.5),
            "c": _cnode("c", "C", tension=0.5),
        }
        result = recalculate_tension_local(graph, {"a"})
        assert result["a"] != 0.5

    def test_shadow_gets_bonus(self):
        graph = {
            "a": _cnode("a", "A", edges=[], tension=0.5, is_shadow=True, shadow_of="x"),
        }
        result = recalculate_tension_local(graph, {"a"})
        # 0.5 + 0.1*ln(1) - 0.1*1.0 + 0.15 = 0.5 - 0.1 + 0.15 = 0.55
        assert abs(result["a"] - 0.55) < 1e-9

    def test_clamp_to_range(self):
        graph = {
            "a": _cnode("a", "A", edges=[], tension=0.5, local_conf=0.0),
        }
        result = recalculate_tension_local(graph, {"a"})
        assert 0.0 <= result["a"] <= 1.0

    def test_outside_2hop_unchanged(self):
        graph = {
            "a": _cnode("a", "A", edges=["b"]),
            "b": _cnode("b", "B", edges=["a", "c"]),
            "c": _cnode("c", "C", edges=["b", "d"]),
            "d": _cnode("d", "D", edges=["c"]),
        }
        result = recalculate_tension_local(graph, {"a"}, hop_radius=2)
        assert "d" not in result


# ═══════════════════ v1.1 Scorer ═══════════════════

class TestScorer:
    def test_calculate_trust_basic(self):
        """trust = quality * (1 - difficulty/200)"""
        t = calculate_trust(50.0, 80.0)
        assert abs(t - 60.0) < 0.01  # 80 * 0.75 = 60

    def test_calculate_trust_zero_difficulty(self):
        t = calculate_trust(0.0, 100.0)
        assert abs(t - 100.0) < 0.01

    def test_calculate_trust_high_difficulty(self):
        t = calculate_trust(180.0, 100.0)
        assert t >= 0.0  # 100 * (1 - 180/200) = 100 * 0.1 = 10, clipped

    def test_calculate_trust_clamp_to_100(self):
        t = calculate_trust(0.0, 150.0)
        assert t == 100.0

    def test_calculate_trust_clamp_to_0(self):
        t = calculate_trust(200.0, 0.0)
        assert t == 0.0

    def test_classify_full(self):
        assert classify_trust_level(95.0) == "full"
        assert classify_trust_level(90.0) == "full"

    def test_classify_supplementary(self):
        assert classify_trust_level(89.9) == "supplementary"
        assert classify_trust_level(60.0) == "supplementary"

    def test_classify_selective(self):
        assert classify_trust_level(59.9) == "selective"
        assert classify_trust_level(30.0) == "selective"

    def test_classify_reject(self):
        assert classify_trust_level(29.9) == "reject"
        assert classify_trust_level(0.0) == "reject"

    def test_estimate_difficulty_returns_valid(self):
        result = estimate_difficulty(
            "Test Book", "Test Author",
            ["Definition of concept A that is somewhat long and complex.",
             "Another definition, shorter.",
             "A third concept with a very elaborate and philosophical definition."],
        )
        assert 0 <= result.style_density <= 100
        assert 0 <= result.info_density <= 100
        assert 0 <= result.viewpoint_novelty <= 100
        assert result.citation_density == 50.0  # neutral default
        assert abs(result.overall - (result.style_density + result.info_density +
                result.viewpoint_novelty + result.citation_density) / 4) < 0.1

    def test_estimate_difficulty_empty(self):
        result = estimate_difficulty("Empty", "Nobody", [])
        assert result.style_density == 30.0
        assert result.overall >= 0

    def test_estimate_quality_basic(self):
        pr = ProductionRecord(
            rounds_completed=2,
            verification_method="spot-check",
            counter_perspectives=["A", "B"],
            total_hours=15.0,
        )
        q = estimate_quality(pr)
        # rounds: 2*20=40, verify: spot-check=10, counter: 2*5=10 → 60
        assert abs(q - 60.0) < 0.01

    def test_estimate_quality_max(self):
        pr = ProductionRecord(
            rounds_completed=4,
            verification_method="full-reread",
            counter_perspectives=["A", "B", "C", "D", "E"],
            total_hours=100.0,
        )
        q = estimate_quality(pr)
        # rounds: min(4*20,60)=60, verify: full-reread=20, counter: min(5*5,20)=20 → 100
        assert abs(q - 100.0) < 0.01

    def test_estimate_quality_minimum(self):
        pr = ProductionRecord(
            rounds_completed=1,
            verification_method="none",
            counter_perspectives=[],
            total_hours=1.0,
        )
        q = estimate_quality(pr)
        # rounds: 1*20=20, verify: 0, counter: 0 → 20
        assert abs(q - 20.0) < 0.01

    def test_estimate_quality_external_verify(self):
        pr = ProductionRecord(
            rounds_completed=3,
            verification_method="external",
            counter_perspectives=["X"],
            total_hours=30.0,
        )
        q = estimate_quality(pr)
        # rounds: 3*20=60 → clipped to 60, verify: external=20, counter: 1*5=5 → 85
        assert abs(q - 85.0) < 0.01


# ═══════════════════ Integration: import_skill_book (v1.1) ═══════════════════

class TestImportSkillBook:
    def test_empty_local_all_imported(self, tmp_path):
        """Scenario 1: empty local, 3 imported → all added."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        sb = _make_skillbook_json(concepts={
            "c1": {"name": "Alpha", "definition": "D1", "perspective_a": "PA",
                   "perspective_b": "PB", "tension_score": 0.5, "edges": []},
            "c2": {"name": "Beta", "definition": "D2", "perspective_a": "PA",
                   "perspective_b": "PB", "tension_score": 0.5, "edges": ["c1"]},
            "c3": {"name": "Gamma", "definition": "D3", "perspective_a": "PA",
                   "perspective_b": "PB", "tension_score": 0.5, "edges": []},
        })
        _write_json(sb_path, sb)
        _write_json(local_path, {"meta": {}, "concepts": {}})

        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True
        assert result["nodes_added"] == 3
        assert result["nodes_bifurcated"] == 0
        assert "trust" in result
        assert "trust_level" in result

        with open(local_path) as f:
            saved = json.load(f)
        assert len(saved["concepts"]) == 3
        assert saved["meta"]["global_tension_stale"] is True

    def test_trust_reject(self, tmp_path):
        """Scenario: trust < 30 → import rejected."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        sb = _make_skillbook_json(
            manifest_overrides={
                "difficulty": 95.0,   # very hard
                "quality_score": 10.0, # very poor quality
            },
            concepts={
                "x": {"name": "X", "definition": "D", "perspective_a": "A",
                      "perspective_b": "B", "tension_score": 0.5, "edges": []},
            },
        )
        _write_json(sb_path, sb)
        _write_json(local_path, {"meta": {}, "concepts": {}})

        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is False
        assert "rejected" in result["error"].lower()
        assert result["trust"] < 30
        assert result["trust_level"] == "reject"

    def test_trust_full_absorption(self, tmp_path):
        """Scenario: trust >= 90 → full absorption."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        sb = _make_skillbook_json(
            manifest_overrides={
                "difficulty": 10.0,   # easy
                "quality_score": 95.0, # excellent
            },
            concepts={
                "x": {"name": "X", "definition": "D", "perspective_a": "A",
                      "perspective_b": "B", "tension_score": 0.5, "edges": []},
            },
        )
        _write_json(sb_path, sb)
        _write_json(local_path, {"meta": {}, "concepts": {}})

        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True
        assert result["trust"] >= 90
        assert result["trust_level"] == "full"

    def test_exact_collision_bifurcation(self, tmp_path):
        """Scenario 2: same name → shadow node."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        _write_json(local_path, _make_local_graph_json(concepts={
            "money": {"name": "Money", "definition": "Local def",
                      "perspective_a": "PA", "perspective_b": "PB",
                      "tension_score": 0.5, "edges": []},
        }))
        _write_json(sb_path, _make_skillbook_json(concepts={
            "money": {"name": "Money", "definition": "Imported def",
                      "perspective_a": "PA", "perspective_b": "PB",
                      "tension_score": 0.5, "edges": []},
        }))

        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True
        assert result["nodes_bifurcated"] == 1

        with open(local_path) as f:
            saved = json.load(f)
        assert len(saved["concepts"]) == 2
        shadows = [k for k in saved["concepts"] if "__shadow_" in k]
        assert len(shadows) == 1
        assert saved["concepts"][shadows[0]]["is_shadow"] is True
        assert saved["concepts"][shadows[0]]["shadow_of"] == "money"

    def test_near_identical_merge(self, tmp_path):
        """Scenario 3: near-identical names → merge definitions."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        _write_json(local_path, _make_local_graph_json(concepts={
            "geld": {"name": "Geld als Denkform Analyse", "definition": "Local def.",
                     "perspective_a": "A", "perspective_b": "B",
                     "tension_score": 0.5, "edges": []},
        }))
        _write_json(sb_path, _make_skillbook_json(concepts={
            "geld2": {"name": "Geld als Denkform Analyse!",
                      "definition": "Imported def.",
                      "perspective_a": "A", "perspective_b": "B",
                      "tension_score": 0.5, "edges": []},
        }))

        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True
        assert result["nodes_bifurcated"] == 0
        assert result["nodes_added"] == 0  # merged, not added

        with open(local_path) as f:
            saved = json.load(f)
        assert len(saved["concepts"]) == 1

    def test_fuzzy_warning_only(self, tmp_path):
        """Scenario 4: similarity 0.7-0.95 → warning, still added as new."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        _write_json(local_path, _make_local_graph_json(concepts={
            "cap": {"name": "System Design", "definition": "D1",
                    "perspective_a": "A", "perspective_b": "B",
                    "tension_score": 0.5, "edges": []},
        }))
        _write_json(sb_path, _make_skillbook_json(concepts={
            "cap2": {"name": "System Designs",
                     "definition": "D2",
                     "perspective_a": "A", "perspective_b": "B",
                     "tension_score": 0.5, "edges": []},
        }))

        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True
        assert result["nearby_warnings"] >= 1
        assert result["nodes_added"] == 1
        assert result["nodes_bifurcated"] == 0

    def test_mixed_scenario(self, tmp_path):
        """Scenario 5: 5 concepts, mixed collisions."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        _write_json(local_path, _make_local_graph_json(concepts={
            "alpha": {"name": "Alpha", "definition": "Local Alpha",
                      "perspective_a": "A", "perspective_b": "B",
                      "tension_score": 0.5, "edges": []},
            "beta": {"name": "Beta", "definition": "Local Beta",
                     "perspective_a": "A", "perspective_b": "B",
                     "tension_score": 0.5, "edges": []},
        }))
        _write_json(sb_path, _make_skillbook_json(concepts={
            "alpha": {"name": "Alpha", "definition": "Imported Alpha",
                      "perspective_a": "A", "perspective_b": "B",
                      "tension_score": 0.5, "edges": []},
            "beta!": {"name": "Beta!", "definition": "Imported Beta",
                      "perspective_a": "A", "perspective_b": "B",
                      "tension_score": 0.5, "edges": []},
            "gamma": {"name": "Gamma", "definition": "New Gamma",
                      "perspective_a": "A", "perspective_b": "B",
                      "tension_score": 0.5, "edges": []},
            "delta": {"name": "Delta", "definition": "New Delta",
                      "perspective_a": "A", "perspective_b": "B",
                      "tension_score": 0.5, "edges": []},
            "epsilon": {"name": "Epsilon", "definition": "New Epsilon",
                        "perspective_a": "A", "perspective_b": "B",
                        "tension_score": 0.5, "edges": []},
        }))

        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True
        # Beta! vs Beta → 0.8 sim → nearby_warning → added as new
        # So: Alpha bifurcated, Beta!+Gamma+Delta+Epsilon = 4 added
        assert result["nodes_added"] == 4
        assert result["nodes_bifurcated"] == 1

    def test_manifest_fatal_missing_quality(self, tmp_path):
        """Scenario 6: missing quality_tier in v1.0 → FATAL."""
        sb_path = tmp_path / "skillbook.json"
        local_path = tmp_path / "local_graph.json"
        _write_json(local_path, {"meta": {}, "concepts": {}})
        _write_json(sb_path, _make_skillbook_json_v10(
            manifest_overrides={"quality_tier": None}, concepts={}))
        with pytest.raises(ValueError, match="quality_tier"):
            import_skill_book(str(local_path), str(sb_path))

    def test_manifest_warning_unknown_llm(self, tmp_path):
        """Scenario 7: unknown llm_source → WARNING but continues."""
        sb_path = tmp_path / "skillbook.json"
        local_path = tmp_path / "local_graph.json"
        _write_json(local_path, {"meta": {}, "concepts": {}})
        _write_json(sb_path, _make_skillbook_json(
            manifest_overrides={"llm_source": "alien-ai"},
            concepts={"x": {"name": "X", "definition": "D", "perspective_a": "A",
                            "perspective_b": "B", "tension_score": 0.5, "edges": []}},
        ))
        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True
        assert any("llm_source" in w for w in result["warnings"])

    def test_tension_updated_2hop(self, tmp_path):
        """Scenario 8: tension recalculated within 2-hop, not beyond."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        _write_json(local_path, _make_local_graph_json(concepts={
            "a": {"name": "A", "definition": "D", "perspective_a": "PA",
                  "perspective_b": "PB", "tension_score": 0.5, "edges": ["b"]},
            "b": {"name": "B", "definition": "D", "perspective_a": "PA",
                  "perspective_b": "PB", "tension_score": 0.5, "edges": ["a", "c"]},
            "c": {"name": "C", "definition": "D", "perspective_a": "PA",
                  "perspective_b": "PB", "tension_score": 0.5, "edges": ["b", "d"]},
            "d": {"name": "D", "definition": "D", "perspective_a": "PA",
                  "perspective_b": "PB", "tension_score": 0.5, "edges": ["c"]},
        }))
        _write_json(sb_path, _make_skillbook_json(concepts={
            "z": {"name": "Z", "definition": "New", "perspective_a": "PA",
                  "perspective_b": "PB", "tension_score": 0.5, "edges": ["a"]},
        }))

        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True

        with open(local_path) as f:
            saved = json.load(f)
        # d is 4 hops from sb::z → outside 2-hop radius → unchanged
        assert saved["concepts"]["d"]["tension_score"] == 0.5

    def test_collision_report_generated(self, tmp_path):
        """Verify collision_report.json sidecar."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        _write_json(local_path, {"meta": {}, "concepts": {}})
        _write_json(sb_path, _make_skillbook_json(concepts={
            "x": {"name": "X", "definition": "D", "perspective_a": "A",
                  "perspective_b": "B", "tension_score": 0.5, "edges": []},
        }))

        result = import_skill_book(str(local_path), str(sb_path))
        report_path = result["collision_report_path"]
        assert os.path.exists(report_path)
        with open(report_path) as f:
            report = json.load(f)
        assert report["nodes_added"] == 1

    def test_local_file_not_exists(self, tmp_path):
        """Local graph file doesn't exist → created fresh."""
        local_path = tmp_path / "nonexistent" / "local_graph.json"
        local_path.parent.mkdir(parents=True, exist_ok=True)
        sb_path = tmp_path / "skillbook.json"
        _write_json(sb_path, _make_skillbook_json(concepts={
            "x": {"name": "X", "definition": "D", "perspective_a": "A",
                  "perspective_b": "B", "tension_score": 0.5, "edges": []},
        }))
        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True
        assert os.path.exists(local_path)

    def test_concept_count_mismatch_warning(self, tmp_path):
        """Manifest concept_count doesn't match actual → warning."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"
        _write_json(local_path, {"meta": {}, "concepts": {}})
        _write_json(sb_path, _make_skillbook_json(
            manifest_overrides={"concept_count": 99},
            concepts={"x": {"name": "X", "definition": "D", "perspective_a": "A",
                            "perspective_b": "B", "tension_score": 0.5, "edges": []}},
        ))
        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is True
        assert any("concept_count" in w for w in result["warnings"])

    def test_skillbook_not_found(self):
        """Non-existent skillbook file → error result."""
        result = import_skill_book("/tmp/nonexistent_local.json",
                                   "/tmp/nonexistent_skillbook.json")
        assert result["success"] is False
        assert "FATAL" in result.get("error", "")

    def test_skillbook_invalid_json(self, tmp_path):
        """Invalid JSON in skillbook → error result."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"
        _write_json(local_path, {"meta": {}, "concepts": {}})
        sb_path.write_text("not valid json {{{", encoding="utf-8")
        result = import_skill_book(str(local_path), str(sb_path))
        assert result["success"] is False
        assert "FATAL" in result.get("error", "")

    # ── v1.1 新测试 ──

    def test_trust_present_in_result(self, tmp_path):
        """v1.1: import result includes trust and trust_level."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        _write_json(local_path, {"meta": {}, "concepts": {}})
        _write_json(sb_path, _make_skillbook_json(concepts={
            "x": {"name": "X", "definition": "D", "perspective_a": "A",
                  "perspective_b": "B", "tension_score": 0.5, "edges": []},
        }))
        result = import_skill_book(str(local_path), str(sb_path), current_version="1.1")
        assert result["success"] is True
        assert "trust" in result
        assert "trust_level" in result

    def test_backward_compat_v10_quality_tier(self, tmp_path):
        """v1.0 quality_tier=3 maps to quality_score=60."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        _write_json(local_path, {"meta": {}, "concepts": {}})
        sb = _make_skillbook_json_v10(
            manifest_overrides={"quality_tier": 3},
            concepts={"x": {"name": "X", "definition": "D", "perspective_a": "A",
                            "perspective_b": "B", "tension_score": 0.5, "edges": []}},
        )
        _write_json(sb_path, sb)

        result = import_skill_book(str(local_path), str(sb_path), current_version="1.0")
        assert result["success"] is True
        # quality_tier=3 → quality_score=60, difficulty=0 → trust=60*(1-0/200)=60
        assert result["trust_level"] == "supplementary"  # 60 → supplementary
        assert "trust" in result

    def test_backward_compat_v10_high_quality(self, tmp_path):
        """v1.0 quality_tier=5 maps to quality_score=100 → high trust."""
        local_path = tmp_path / "local_graph.json"
        sb_path = tmp_path / "skillbook.json"

        _write_json(local_path, {"meta": {}, "concepts": {}})
        sb = _make_skillbook_json_v10(
            manifest_overrides={"quality_tier": 5},
            concepts={"x": {"name": "X", "definition": "D", "perspective_a": "A",
                            "perspective_b": "B", "tension_score": 0.5, "edges": []}},
        )
        _write_json(sb_path, sb)

        result = import_skill_book(str(local_path), str(sb_path), current_version="1.0")
        assert result["success"] is True
        # quality_tier=5 → quality_score=100, difficulty=0 → trust=100 → full
        assert result["trust_level"] == "full"
