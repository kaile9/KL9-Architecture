"""
Tests for KL9-RHIZOME SQLite ↔ JSON bridge (v1.5).

Tests:
  1. Store concepts in SQLite → export to skillbook JSON → verify format
  2. Import skillbook JSON → verify nodes and edges in SQLite
  3. Empty graph export → empty concepts dict
  4. Edge relationships correctly exported and imported
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Override DB_PATH for tests — use temp files
import kl9_core.graph_backend as gb


@pytest.fixture
def temp_db(monkeypatch, tmp_path):
    """Create a temporary SQLite database for testing."""
    db_path = str(tmp_path / "test_graph.db")

    # Patch the module-level DB_PATH
    monkeypatch.setattr(gb, "DB_PATH", db_path)

    # Force schema creation
    conn = gb._get_conn()
    conn.close()

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def populated_db(temp_db, monkeypatch):
    """Populate temp DB with some concepts and edges."""
    # Store concepts
    id1 = gb.store_concept(
        name="Geld als Denkform",
        tier1="货币作为思维形式，不仅是交换媒介更是认知框架",
        thinker="Brodbeck",
        field="经济哲学",
        perspective_a="经济理性",
        perspective_b="现象学直观",
        tension_score=0.7,
    )
    id2 = gb.store_concept(
        name="Wirtschaft als Geldwirtschaft",
        tier1="经济本质上是货币经济，非物物交换的演化",
        thinker="Brodbeck",
        field="经济哲学",
        perspective_a="货币循环",
        perspective_b="实物经济",
        tension_score=0.6,
    )
    id3 = gb.store_concept(
        name="Marxsche Wertform",
        tier1="马克思价值形式分析：从简单价值形式到货币形式",
        thinker="Marx",
        field="政治经济学",
        perspective_a="价值实体",
        perspective_b="交换价值",
        tension_score=0.8,
    )

    # Create edges
    gb.create_edge(id1, id2, "relates_to", "货币思维形式 → 货币经济")
    gb.create_edge(id2, id3, "dialogues_with", "Brodbeck对话马克思价值形式")

    return {"ids": [id1, id2, id3], "db_path": temp_db}


# ═══════════════════════════════════════════════════════════════
# Test 1: Store → Export → Verify Format
# ═══════════════════════════════════════════════════════════════

class TestExportToJSON:
    def test_export_populated_graph(self, populated_db, tmp_path):
        """Store 3 concepts in SQLite → export → verify JSON structure."""
        from kl9_skillbook.bridge import export_graph_to_skillbook

        output_path = str(tmp_path / "exported.skillbook.json")
        manifest = {
            "skill_book_id": "test_export",
            "version": "1.0",
            "quality_tier": 4,
            "llm_source": "claude",
            "kl9_version": "1.5.0",
            "created_timestamp": int(time.time()),
            "book_title": "Test Export",
        }

        result = export_graph_to_skillbook(
            output_path=output_path,
            manifest=manifest,
            db_path=populated_db["db_path"],
        )

        assert os.path.exists(result)

        with open(result, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check manifest
        assert "manifest" in data
        assert data["manifest"]["skill_book_id"] == "test_export"
        assert data["manifest"]["book_title"] == "Test Export"

        # Check concepts
        assert "concepts" in data
        assert len(data["concepts"]) == 3

        # Each concept should have required fields
        for cid, cdata in data["concepts"].items():
            assert "name" in cdata
            assert "definition" in cdata
            assert "perspective_a" in cdata
            assert "perspective_b" in cdata
            assert "tension_score" in cdata
            assert "edges" in cdata

    def test_export_empty_graph(self, temp_db, tmp_path):
        """Empty graph → exported JSON has empty concepts dict."""
        from kl9_skillbook.bridge import export_graph_to_skillbook

        output_path = str(tmp_path / "empty_export.skillbook.json")
        manifest = {
            "skill_book_id": "empty",
            "version": "1.0",
            "quality_tier": 1,
            "llm_source": "unknown",
            "kl9_version": "1.5.0",
            "created_timestamp": int(time.time()),
            "book_title": "Empty",
        }

        result = export_graph_to_skillbook(
            output_path=output_path,
            manifest=manifest,
            db_path=temp_db,
        )

        with open(result, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["manifest"]["concept_count"] == 0
        assert data["concepts"] == {}

    def test_exported_concepts_have_correct_fields(self, populated_db, tmp_path):
        """Verify exported concepts retain perspective and tension fields."""
        from kl9_skillbook.bridge import export_graph_to_skillbook

        output_path = str(tmp_path / "fields_test.skillbook.json")
        manifest = {
            "skill_book_id": "fields_test",
            "version": "1.0",
            "quality_tier": 4,
            "llm_source": "claude",
            "kl9_version": "1.5.0",
            "created_timestamp": int(time.time()),
            "book_title": "Fields Test",
        }

        result = export_graph_to_skillbook(
            output_path=output_path,
            manifest=manifest,
            db_path=populated_db["db_path"],
        )

        with open(result, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Find the Geld als Denkform concept
        geld_concept = None
        for cid, cdata in data["concepts"].items():
            if "Geld" in cdata.get("name", ""):
                geld_concept = cdata
                break

        assert geld_concept is not None
        assert geld_concept["perspective_a"] == "经济理性"
        assert geld_concept["perspective_b"] == "现象学直观"
        assert abs(geld_concept["tension_score"] - 0.7) < 0.01

    def test_exported_edges_present(self, populated_db, tmp_path):
        """Verify edges are exported as concept_id lists."""
        from kl9_skillbook.bridge import export_graph_to_skillbook

        output_path = str(tmp_path / "edges_test.skillbook.json")
        manifest = {
            "skill_book_id": "edges_test",
            "version": "1.0",
            "quality_tier": 4,
            "llm_source": "claude",
            "kl9_version": "1.5.0",
            "created_timestamp": int(time.time()),
            "book_title": "Edges Test",
        }

        result = export_graph_to_skillbook(
            output_path=output_path,
            manifest=manifest,
            db_path=populated_db["db_path"],
        )

        with open(result, "r", encoding="utf-8") as f:
            data = json.load(f)

        # At least one concept should have edges
        edges_found = False
        for cid, cdata in data["concepts"].items():
            if len(cdata.get("edges", [])) > 0:
                edges_found = True
                break

        assert edges_found, "Expected at least one concept with edges"


# ═══════════════════════════════════════════════════════════════
# Test 2: Import Skillbook JSON → SQLite
# ═══════════════════════════════════════════════════════════════

class TestImportFromJSON:
    def test_import_into_empty_db(self, temp_db, tmp_path, monkeypatch):
        """Import a skillbook with 3 concepts into empty SQLite."""
        from kl9_skillbook.bridge import import_skillbook_to_graph

        # Create a skillbook JSON
        sb_path = tmp_path / "test_import.skillbook.json"
        skillbook = {
            "manifest": {
                "skill_book_id": "test_import_book",
                "version": "1.0",
                "quality_tier": 4,
                "llm_source": "claude",
                "kl9_version": "1.5.0",
                "created_timestamp": int(time.time()),
                "book_title": "Test Import Book",
                "concept_count": 3,
            },
            "concepts": {
                "c1": {
                    "name": "Alpha",
                    "definition": "Definition of Alpha",
                    "perspective_a": "PA1",
                    "perspective_b": "PB1",
                    "tension_score": 0.5,
                    "edges": ["c2"],
                },
                "c2": {
                    "name": "Beta",
                    "definition": "Definition of Beta",
                    "perspective_a": "PA2",
                    "perspective_b": "PB2",
                    "tension_score": 0.6,
                    "edges": ["c1", "c3"],
                },
                "c3": {
                    "name": "Gamma",
                    "definition": "Definition of Gamma",
                    "perspective_a": "PA3",
                    "perspective_b": "PB3",
                    "tension_score": 0.7,
                    "edges": [],
                },
            },
        }
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(skillbook, f)

        monkeypatch.setattr(gb, "DB_PATH", temp_db)

        result = import_skillbook_to_graph(str(sb_path), db_path=temp_db)
        assert result["success"] is True
        assert result["nodes_imported"] >= 3
        assert result["nodes_bifurcated"] == 0

        # Verify nodes in SQLite
        conn = gb._get_conn()
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM nodes WHERE label='Concept' AND archived=0"
            ).fetchone()[0]
            assert count >= 3
        finally:
            conn.close()

    def test_import_with_collision(self, temp_db, tmp_path, monkeypatch):
        """Import with existing same-name concept → bifurcation."""
        from kl9_skillbook.bridge import import_skillbook_to_graph

        # Pre-populate with one concept
        monkeypatch.setattr(gb, "DB_PATH", temp_db)
        gb.store_concept(
            name="Money",
            tier1="Local definition of Money",
            thinker="Marx",
            field="经济学",
            perspective_a="使用价值",
            perspective_b="交换价值",
            tension_score=0.5,
        )

        # Create skillbook with same name
        sb_path = tmp_path / "collide_test.skillbook.json"
        skillbook = {
            "manifest": {
                "skill_book_id": "collide_book",
                "version": "1.0",
                "quality_tier": 4,
                "llm_source": "deepseek-v4-pro",
                "kl9_version": "1.5.0",
                "created_timestamp": int(time.time()),
                "book_title": "Collision Test",
                "concept_count": 2,
            },
            "concepts": {
                "money": {
                    "name": "Money",
                    "definition": "Imported definition of Money",
                    "perspective_a": "价值尺度",
                    "perspective_b": "流通手段",
                    "tension_score": 0.6,
                    "edges": [],
                },
                "value": {
                    "name": "Value",
                    "definition": "Theory of value",
                    "perspective_a": "客观价值",
                    "perspective_b": "主观价值",
                    "tension_score": 0.7,
                    "edges": [],
                },
            },
        }
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(skillbook, f)

        result = import_skillbook_to_graph(str(sb_path), db_path=temp_db)
        assert result["success"] is True
        assert result["nodes_bifurcated"] >= 1

        # Verify shadow node exists
        conn = gb._get_conn()
        try:
            shadows = conn.execute(
                "SELECT COUNT(*) FROM nodes WHERE is_shadow=1 AND archived=0"
            ).fetchone()[0]
            assert shadows >= 1
        finally:
            conn.close()

    def test_import_edges_persist(self, temp_db, tmp_path, monkeypatch):
        """Import with edge definitions → edges created in SQLite."""
        from kl9_skillbook.bridge import import_skillbook_to_graph

        monkeypatch.setattr(gb, "DB_PATH", temp_db)

        sb_path = tmp_path / "edge_import.skillbook.json"
        skillbook = {
            "manifest": {
                "skill_book_id": "edge_import_book",
                "version": "1.0",
                "quality_tier": 4,
                "llm_source": "claude",
                "kl9_version": "1.5.0",
                "created_timestamp": int(time.time()),
                "book_title": "Edge Import Test",
                "concept_count": 2,
            },
            "concepts": {
                "x": {
                    "name": "X Concept",
                    "definition": "X def",
                    "perspective_a": "A",
                    "perspective_b": "B",
                    "tension_score": 0.5,
                    "edges": ["y"],
                },
                "y": {
                    "name": "Y Concept",
                    "definition": "Y def",
                    "perspective_a": "A",
                    "perspective_b": "B",
                    "tension_score": 0.5,
                    "edges": ["x"],
                },
            },
        }
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(skillbook, f)

        result = import_skillbook_to_graph(str(sb_path), db_path=temp_db)
        assert result["success"] is True

        # Verify edges in SQLite
        conn = gb._get_conn()
        try:
            edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            assert edge_count >= 2  # x→y and y→x
        finally:
            conn.close()

    def test_import_invalid_skillbook(self, temp_db, tmp_path, monkeypatch):
        """Invalid JSON skillbook → error."""
        from kl9_skillbook.bridge import import_skillbook_to_graph

        monkeypatch.setattr(gb, "DB_PATH", temp_db)

        sb_path = tmp_path / "invalid.skillbook.json"
        sb_path.write_text("this is not json {{{", encoding="utf-8")

        result = import_skillbook_to_graph(str(sb_path), db_path=temp_db)
        assert result["success"] is False
        assert "FATAL" in result.get("error", "")

    def test_import_missing_manifest(self, temp_db, tmp_path, monkeypatch):
        """Skillbook with missing quality_tier → error."""
        from kl9_skillbook.bridge import import_skillbook_to_graph

        monkeypatch.setattr(gb, "DB_PATH", temp_db)

        sb_path = tmp_path / "no_quality.skillbook.json"
        skillbook = {
            "manifest": {"version": "1.0"},
            "concepts": {},
        }
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(skillbook, f)

        result = import_skillbook_to_graph(str(sb_path), db_path=temp_db)
        assert result["success"] is False
        assert "quality_tier" in result.get("error", "").lower()


# ═══════════════════════════════════════════════════════════════
# Test 3 & 4: Round-trip and Edge Integrity
# ═══════════════════════════════════════════════════════════════

class TestRoundTrip:
    def test_round_trip_export_import(self, temp_db, tmp_path, monkeypatch):
        """Export from SQLite → re-import → verify concepts preserved."""
        from kl9_skillbook.bridge import export_graph_to_skillbook, import_skillbook_to_graph

        monkeypatch.setattr(gb, "DB_PATH", temp_db)

        # Store some concepts
        gb.store_concept(
            name="TestConcept",
            tier1="Test definition",
            thinker="TestThinker",
            field="测试",
            perspective_a="视角A",
            perspective_b="视角B",
            tension_score=0.75,
        )
        gb.store_concept(
            name="AnotherConcept",
            tier1="Another definition",
            field="测试",
            perspective_a="PA",
            perspective_b="PB",
            tension_score=0.5,
        )

        # Export
        export_path = str(tmp_path / "roundtrip.skillbook.json")
        manifest = {
            "skill_book_id": "roundtrip",
            "version": "1.0",
            "quality_tier": 4,
            "llm_source": "claude",
            "kl9_version": "1.5.0",
            "created_timestamp": int(time.time()),
            "book_title": "Roundtrip Test",
        }
        export_graph_to_skillbook(export_path, manifest, db_path=temp_db)

        # Verify export exists and has content
        with open(export_path, "r", encoding="utf-8") as f:
            exported = json.load(f)
        assert len(exported["concepts"]) >= 2

        # Create a fresh DB for re-import
        fresh_db = str(tmp_path / "fresh_test.db")
        monkeypatch.setattr(gb, "DB_PATH", fresh_db)
        # Initialize schema
        conn = gb._get_conn()
        conn.close()

        result = import_skillbook_to_graph(export_path, db_path=fresh_db)
        assert result["success"] is True
        assert result["nodes_imported"] >= 2

        # Verify concepts in fresh DB
        conn = gb._get_conn()
        try:
            rows = conn.execute(
                "SELECT name, tier1_def, perspective_a, tension_score "
                "FROM nodes WHERE label='Concept' AND archived=0"
            ).fetchall()
            names = [r["name"] for r in rows]
            assert "TestConcept" in names
            assert "AnotherConcept" in names
        finally:
            conn.close()


class TestNewFieldsInStoreConcept:
    def test_store_concept_with_new_fields(self, temp_db, monkeypatch):
        """store_concept now accepts and persists new skillbook fields."""
        monkeypatch.setattr(gb, "DB_PATH", temp_db)

        cid = gb.store_concept(
            name="NewFieldConcept",
            tier1="Definition",
            perspective_a="经济理性",
            perspective_b="现象学直观",
            tension_score=0.85,
            local_confidence=0.9,
            is_shadow=False,
            shadow_of="",
        )

        conn = gb._get_conn()
        try:
            row = conn.execute(
                "SELECT perspective_a, perspective_b, tension_score, "
                "local_confidence, is_shadow, shadow_of "
                "FROM nodes WHERE id=?",
                (cid,),
            ).fetchone()
            assert row["perspective_a"] == "经济理性"
            assert row["perspective_b"] == "现象学直观"
            assert abs(row["tension_score"] - 0.85) < 0.01
            assert abs(row["local_confidence"] - 0.9) < 0.01
            assert row["is_shadow"] == 0
        finally:
            conn.close()

    def test_store_concept_shadow(self, temp_db, monkeypatch):
        """Store a shadow concept with is_shadow=True."""
        monkeypatch.setattr(gb, "DB_PATH", temp_db)

        cid = gb.store_concept(
            name="ShadowConcept",
            tier1="Shadow def",
            is_shadow=True,
            shadow_of="concept:MasterConcept:",
            local_confidence=0.6,
        )

        conn = gb._get_conn()
        try:
            row = conn.execute(
                "SELECT is_shadow, shadow_of, local_confidence "
                "FROM nodes WHERE id=?",
                (cid,),
            ).fetchone()
            assert row["is_shadow"] == 1
            assert row["shadow_of"] == "concept:MasterConcept:"
            assert abs(row["local_confidence"] - 0.6) < 0.01
        finally:
            conn.close()

    def test_update_preserves_new_fields(self, temp_db, monkeypatch):
        """Updating existing concept preserves new v1.5 fields."""
        monkeypatch.setattr(gb, "DB_PATH", temp_db)

        # First store
        cid = gb.store_concept(
            name="UpdateTest",
            tier1="v1",
            perspective_a="orig_a",
            tension_score=0.5,
        )
        # Update
        cid2 = gb.store_concept(
            name="UpdateTest",
            tier1="v2",
            perspective_a="new_a",
            tension_score=0.9,
        )
        assert cid == cid2  # Same concept ID

        conn = gb._get_conn()
        try:
            row = conn.execute(
                "SELECT tier1_def, perspective_a, tension_score "
                "FROM nodes WHERE id=?",
                (cid,),
            ).fetchone()
            assert row["tier1_def"] == "v2"
            assert row["perspective_a"] == "new_a"
            assert abs(row["tension_score"] - 0.9) < 0.01
        finally:
            conn.close()
