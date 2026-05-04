"""Tests for KL9-RHIZOME skillbook absorption protocol v1.0."""

import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kl9_skillbook.models import ConceptNode, ConceptProvenance, CollisionReport
from kl9_skillbook.validator import validate_manifest
from kl9_skillbook.matcher import levenshtein_ratio, detect_collisions
from kl9_skillbook.merger import merge_graphs
from kl9_skillbook.tension import get_subgraph, recalculate_tension_local
from kl9_skillbook.importer import import_skill_book


# ═══════════════════════ helpers ═══════════════════════

def _make_skillbook_json(manifest_overrides=None, concepts=None):
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


# ═══════════════════ Integration: import_skill_book ═══════════════════

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

        with open(local_path) as f:
            saved = json.load(f)
        assert len(saved["concepts"]) == 3
        assert saved["meta"]["global_tension_stale"] is True

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
        """Scenario 6: missing quality_tier → FATAL."""
        sb_path = tmp_path / "skillbook.json"
        local_path = tmp_path / "local_graph.json"
        _write_json(local_path, {"meta": {}, "concepts": {}})
        _write_json(sb_path, _make_skillbook_json(
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
