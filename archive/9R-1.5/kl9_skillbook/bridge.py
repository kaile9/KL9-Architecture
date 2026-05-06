"""
Bridge between SQLite graph_backend and skillbook JSON format.

KL9-RHIZOME v1.5 — Skillbook Absorption Protocol
"""

import json
import os
import time
import sys
from pathlib import Path
from typing import Any, Optional

# 确保可以导入 kl9_core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kl9_core.graph_backend import (
    _get_conn, store_concept, create_edge, get_concept, DB_PATH,
)
from .models import ConceptNode, ConceptProvenance, SkillBookManifest, ProductionRecord
from .importer import import_skill_book as _json_import
from .importer import _load_concepts, _node_to_dict
from .merger import merge_graphs
from .matcher import detect_collisions
from .tension import recalculate_tension_local
from .scorer import estimate_difficulty, estimate_quality, calculate_trust, classify_trust_level


# ═══════════════════════════════════════════════════════════════
# Export: SQLite → Skillbook JSON
# ═══════════════════════════════════════════════════════════════

def export_graph_to_skillbook(
    output_path: str,
    manifest: dict,
    db_path: str = None,
    production_record: Optional[ProductionRecord] = None,
) -> str:
    """
    将 SQLite 图谱导出为技能书 JSON 文件。

    自动执行难度估计和质量评估（v1.1）。

    Args:
        output_path: 输出 JSON 文件路径
        manifest: 技能书 manifest，需包含:
            skill_book_id, version, quality_tier, llm_source,
            kl9_version, created_timestamp, book_title
        db_path: SQLite 数据库路径，默认使用 graph_backend.DB_PATH
        production_record: 制作记录（可选），若提供则自动计算质量分

    Returns:
        输出文件路径
    """
    # 使用指定的 db_path 或默认路径
    if db_path and db_path != DB_PATH:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    else:
        conn = _get_conn()

    try:
        # 查询所有活跃概念
        rows = conn.execute(
            "SELECT id, name, label, tier1_def, tier2_def, tier3_def, "
            "field, thinker, work, usage_count, weight, "
            "perspective_a, perspective_b, tension_score, "
            "local_confidence, is_shadow, shadow_of "
            "FROM nodes WHERE label = 'Concept' AND archived = 0"
        ).fetchall()

        # 查询所有边
        edge_rows = conn.execute(
            "SELECT from_id, to_id, rel_type, reason, confidence, source_work "
            "FROM edges"
        ).fetchall()

        # 构建边索引: from_id → [to_id, ...]
        edges_by_from: dict[str, list[str]] = {}
        for e in edge_rows:
            edges_by_from.setdefault(e["from_id"], []).append(e["to_id"])

        # 构建概念字典和定义列表（用于难度估计）
        concepts: dict[str, dict] = {}
        definitions: list[str] = []

        for r in rows:
            concept_id = r["id"]
            definition = r["tier1_def"] or ""
            concepts[concept_id] = {
                "name": r["name"],
                "definition": definition,
                "perspective_a": r["perspective_a"] or "",
                "perspective_b": r["perspective_b"] or "",
                "tension_score": r["tension_score"] or 0.5,
                "edges": edges_by_from.get(concept_id, []),
                "local_confidence": r["local_confidence"] or 1.0,
                "is_shadow": bool(r["is_shadow"]),
                "shadow_of": r["shadow_of"] or "",
            }
            if definition:
                definitions.append(definition)

        # ── v1.1: 自动难度评估 ──
        book_title = manifest.get("book_title", "Unknown")
        book_author = manifest.get("extra", {}).get("original_author",
                    manifest.get("llm_source", "Unknown"))
        diff_breakdown = estimate_difficulty(book_title, book_author, definitions)
        difficulty = diff_breakdown.overall

        # ── v1.1: 自动质量评估 ──
        if production_record:
            quality_score = estimate_quality(production_record)
        else:
            # Fallback: derive from quality_tier
            quality_score = float(manifest.get("quality_tier", 4) * 20)

        # ── v1.1: 信任计算（含语言偏差）──
        llm_source = manifest.get("llm_source", "unknown")
        book_language = manifest.get("book_language", manifest.get("extra", {}).get("book_language", ""))
        trust = calculate_trust(difficulty, quality_score, llm_source, book_language)
        trust_level = classify_trust_level(trust)

        # 构建完整技能书 manifest
        manifest_dict = {
            "skill_book_id": manifest.get("skill_book_id", ""),
            "version": "1.1",  # v1.1
            "quality_tier": manifest.get("quality_tier", 4),
            "llm_source": llm_source,
            "kl9_version": manifest.get("kl9_version", "1.5.0"),
            "created_timestamp": manifest.get("created_timestamp", int(time.time())),
            "book_title": book_title,
            "book_language": book_language,
            "concept_count": len(concepts),
            "extra": manifest.get("extra", {}),
            # v1.1 新字段
            "difficulty": round(difficulty, 1),
            "quality_score": round(quality_score, 1),
            "difficulty_breakdown": {
                "style_density": diff_breakdown.style_density,
                "info_density": diff_breakdown.info_density,
                "viewpoint_novelty": diff_breakdown.viewpoint_novelty,
                "citation_density": diff_breakdown.citation_density,
                "overall": diff_breakdown.overall,
            },
            "_trust": round(trust, 1),
            "_trust_level": trust_level,
        }

        if production_record:
            manifest_dict["production_record"] = {
                "rounds_completed": production_record.rounds_completed,
                "verification_method": production_record.verification_method,
                "counter_perspectives": production_record.counter_perspectives,
                "total_hours": production_record.total_hours,
            }

        skillbook = {
            "manifest": manifest_dict,
            "concepts": concepts,
        }

        # 写入文件
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(skillbook, f, ensure_ascii=False, indent=2)

        return str(output_path)
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# Import: Skillbook JSON → SQLite
# ═══════════════════════════════════════════════════════════════

def import_skillbook_to_graph(
    skillbook_path: str,
    db_path: str = None,
) -> dict:
    """
    读取技能书 JSON，导入到 SQLite 图谱（使用 graph_backend API）。

    步骤:
    1. 加载技能书 JSON
    2. 校验 manifest (v1.1 with trust)
    3. 信任评估 → reject 则返回 error
    4. 从 SQLite 加载现有概念作为 local
    5. 碰撞检测 & 合并
    6. 对每个概念调用 store_concept() 存入 nodes 表
    7. 对每条边调用 create_edge()
    8. 返回 {success, trust, trust_level, ...}

    Args:
        skillbook_path: 技能书 JSON 文件路径
        db_path: SQLite 数据库路径，默认使用 graph_backend.DB_PATH

    Returns:
        {success, trust, trust_level, nodes_imported, nodes_bifurcated,
         exact_collisions, nearby_warnings, warnings}
    """
    from .validator import validate_manifest

    # 1. 加载技能书 JSON
    try:
        with open(skillbook_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {"success": False, "error": f"FATAL: cannot load skillbook — {e}"}

    # 2. 校验 manifest
    ok, manifest, warnings = validate_manifest(sb.get("manifest", {}), "1.1")
    if not ok:
        return {"success": False, "error": f"Manifest validation FAILED: {warnings}"}

    # ── 步骤 2.5: 信任评估 (v1.1 + 语言偏差) ──
    book_language = getattr(manifest, 'book_language', '') or manifest.extra.get('book_language', '')
    trust = calculate_trust(manifest.difficulty, manifest.quality_score,
                           manifest.llm_source, book_language)
    trust_level = classify_trust_level(trust)

    if trust_level == "reject":
        return {
            "success": False,
            "error": f"Trust too low ({trust:.1f}%), import rejected. "
                     f"Difficulty={manifest.difficulty}, Quality={manifest.quality_score}",
            "trust": round(trust, 1),
            "trust_level": trust_level,
        }

    # 3. 从 SQLite 加载现有活跃概念
    conn = _get_conn() if db_path is None else _get_conn_for_path(db_path)
    try:
        rows = conn.execute(
            "SELECT id, name, tier1_def, perspective_a, perspective_b, "
            "tension_score, local_confidence, is_shadow, shadow_of "
            "FROM nodes WHERE label = 'Concept' AND archived = 0"
        ).fetchall()

        local: dict[str, ConceptNode] = {}
        for r in rows:
            # Get edges for this node
            edge_rows = conn.execute(
                "SELECT to_id FROM edges WHERE from_id = ?", (r["id"],)
            ).fetchall()
            edges_list = [e["to_id"] for e in edge_rows]

            local[r["id"]] = ConceptNode(
                concept_id=r["id"],
                name=r["name"],
                definition=r["tier1_def"] or "",
                perspective_a=r["perspective_a"] or "",
                perspective_b=r["perspective_b"] or "",
                tension_score=r["tension_score"] or 0.5,
                edges=edges_list,
                local_confidence=r["local_confidence"] or 1.0,
                is_shadow=bool(r["is_shadow"]),
                shadow_of=r["shadow_of"] or "",
            )

        # 4. Namespace imported concepts
        imported: dict[str, ConceptNode] = {}
        now = int(time.time())
        book_id = manifest.skill_book_id or os.path.basename(skillbook_path)
        for cid, data in sb.get("concepts", {}).items():
            nid = f"sb::{cid}"
            node = _node_from_dict_for_bridge(nid, data)
            if node.provenance is None:
                node.provenance = ConceptProvenance(
                    book_id, manifest.quality_tier, manifest.llm_source, now
                )
            # 将边引用从原始 ID 映射到命名空间 ID (sb:: 前缀)
            node.edges = [
                f"sb::{e}" if not e.startswith("sb::") else e
                for e in node.edges
            ]
            imported[nid] = node

        if manifest.concept_count != len(imported):
            warnings.append(
                f"WARNING: manifest concept_count={manifest.concept_count} "
                f"but actual={len(imported)}"
            )

        # 5. 碰撞检测
        report = detect_collisions(local, imported)
        prov = ConceptProvenance(book_id, manifest.quality_tier, manifest.llm_source, now)

        # 6. 合并
        merged = merge_graphs(local, imported, report, prov)

        # 7. 张力重算
        affected: set[str] = set()
        for lid, iid in report.exact_collisions:
            affected.add(lid)
            sid = (
                f"{iid[4:] if iid.startswith('sb::') else iid}"
                f"__shadow_{prov.source_skill_book}"
            )
            affected.add(sid)
        for lid, iid, _ in report.near_identical:
            affected.add(lid)
        collided = {e[1] for e in report.exact_collisions} | {
            n[1] for n in report.near_identical
        }
        for iid in imported:
            if iid not in collided:
                affected.add(iid)

        new_t = recalculate_tension_local(merged, affected)
        for nid, t in new_t.items():
            if nid in merged:
                merged[nid].tension_score = t

        # 8. 写入 SQLite — 对 merged 中的每个概念调用 store_concept
        nodes_written = 0
        nodes_bifurcated = report.nodes_bifurcated

        # 第一遍：存储所有概念
        for nid, node in merged.items():
            is_new = nid.startswith("sb::") or nid not in local
            is_shadow_node = node.is_shadow

            if is_new or is_shadow_node or nid in affected:
                store_concept(
                    name=node.name,
                    tier1=node.definition,
                    tier2="",
                    tier3="",
                    thinker="",
                    work="",
                    field="",
                    perspective_a=node.perspective_a,
                    perspective_b=node.perspective_b,
                    tension_score=node.tension_score,
                    local_confidence=node.local_confidence,
                    is_shadow=node.is_shadow,
                    shadow_of=node.shadow_of or "",
                    explicit_id=nid,
                )
                nodes_written += 1

        # 第二遍：创建边（所有概念已确保存在）
        for nid, node in merged.items():
            for to_id in node.edges:
                if to_id in merged:
                    try:
                        create_edge(
                            from_id=nid,
                            to_id=to_id,
                            rel_type="relates_to",
                            reason=f"Imported from {book_id}",
                            confidence=node.local_confidence,
                            source_work=book_id,
                        )
                    except Exception:
                        pass

        conn.commit()
    finally:
        conn.close()

    all_warnings = report.warnings + warnings

    return {
        "success": True,
        "nodes_imported": nodes_written,
        "nodes_bifurcated": nodes_bifurcated,
        "exact_collisions": len(report.exact_collisions),
        "nearby_warnings": len(report.nearby_warnings),
        "warnings": all_warnings,
        "trust": round(trust, 1),
        "trust_level": trust_level,
    }


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _get_conn_for_path(db_path: str):
    """获取指定路径的 SQLite 连接。"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _node_from_dict_for_bridge(cid: str, data: dict) -> ConceptNode:
    """从技能书 JSON dict 构建 ConceptNode（bridge 专用）。"""
    p = data.get("provenance")
    prov = None
    if p:
        prov = ConceptProvenance(
            p["source_skill_book"],
            p["quality_tier"],
            p["llm_source"],
            p["import_timestamp"],
        )
    return ConceptNode(
        concept_id=cid,
        name=data.get("name", ""),
        definition=data.get("definition", ""),
        perspective_a=data.get("perspective_a", ""),
        perspective_b=data.get("perspective_b", ""),
        tension_score=data.get("tension_score", 0.5),
        edges=data.get("edges", []),
        provenance=prov,
        local_confidence=data.get("local_confidence", 1.0),
        is_shadow=data.get("is_shadow", False),
        shadow_of=data.get("shadow_of"),
    )
