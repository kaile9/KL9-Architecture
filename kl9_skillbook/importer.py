"""Main import pipeline — single entry point for skillbook absorption."""
import json, os, time
from typing import Any
from .models import ConceptNode, ConceptProvenance
from .validator import validate_manifest
from .matcher import detect_collisions
from .merger import merge_graphs
from .tension import recalculate_tension_local
from .scorer import calculate_trust, classify_trust_level


def _node_from_dict(cid: str, data: dict) -> ConceptNode:
    p = data.get("provenance")
    prov = ConceptProvenance(p["source_skill_book"], p["quality_tier"],
                             p["llm_source"], p["import_timestamp"]) if p else None
    return ConceptNode(
        concept_id=cid, name=data.get("name",""),
        definition=data.get("definition",""),
        perspective_a=data.get("perspective_a",""),
        perspective_b=data.get("perspective_b",""),
        tension_score=data.get("tension_score",0.5),
        edges=data.get("edges",[]), provenance=prov,
        local_confidence=data.get("local_confidence",1.0),
        is_shadow=data.get("is_shadow",False),
        shadow_of=data.get("shadow_of"),
    )


def _node_to_dict(n: ConceptNode) -> dict:
    d = dict(name=n.name, definition=n.definition,
             perspective_a=n.perspective_a, perspective_b=n.perspective_b,
             tension_score=n.tension_score, edges=n.edges,
             local_confidence=n.local_confidence,
             is_shadow=n.is_shadow, shadow_of=n.shadow_of)
    if n.provenance:
        d["provenance"] = dict(source_skill_book=n.provenance.source_skill_book,
                               quality_tier=n.provenance.quality_tier,
                               llm_source=n.provenance.llm_source,
                               import_timestamp=n.provenance.import_timestamp)
    return d


def _load_concepts(raw: dict) -> dict[str, ConceptNode]:
    return {cid: _node_from_dict(cid, data) for cid, data in raw.items()}


def import_skill_book(local_graph_path: str, skill_book_path: str,
                      current_version: str = "1.1") -> dict[str, Any]:
    """9-step pipeline: load→validate→trust→load local→namespace→detect→merge→tension→stale→persist."""
    # 1. Load skillbook
    try:
        with open(skill_book_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {"success": False, "error": f"FATAL: cannot load skillbook — {e}"}

    # 2. Validate manifest
    ok, manifest, warnings = validate_manifest(sb.get("manifest", {}), current_version)
    if not ok:
        raise ValueError(f"Manifest validation FAILED: {warnings}")

    # ── 步骤 2.5: 信任评估 (v1.1) ──
    trust = calculate_trust(manifest.difficulty, manifest.quality_score)
    trust_level = classify_trust_level(trust)

    if trust_level == "reject":
        return {
            "success": False,
            "error": f"Trust too low ({trust:.1f}%), import rejected. "
                     f"Difficulty={manifest.difficulty}, Quality={manifest.quality_score}",
            "trust": round(trust, 1),
            "trust_level": trust_level,
        }

    # 3. Load local
    if os.path.exists(local_graph_path):
        with open(local_graph_path, "r", encoding="utf-8") as f:
            lr = json.load(f)
        local = _load_concepts(lr.get("concepts", {}))
        meta = lr.get("meta", {})
    else:
        local, meta = {}, {}

    # 4. Namespace imported concepts
    imported: dict[str, ConceptNode] = {}
    now = int(time.time())
    book_id = manifest.skill_book_id or os.path.basename(skill_book_path)
    for cid, data in sb.get("concepts", {}).items():
        nid = f"sb::{cid}"
        node = _node_from_dict(nid, data)
        node.provenance = ConceptProvenance(book_id, manifest.quality_tier,
                                            manifest.llm_source, now)
        imported[nid] = node
    if manifest.concept_count != len(imported):
        warnings.append(f"WARNING: manifest concept_count={manifest.concept_count} "
                        f"but actual={len(imported)}")

    # 5. Detect collisions
    report = detect_collisions(local, imported)
    prov = ConceptProvenance(book_id, manifest.quality_tier, manifest.llm_source, now)

    # 6. Merge
    merged = merge_graphs(local, imported, report, prov)

    # 7. Recalculate tension
    affected: set[str] = set()
    for lid, iid in report.exact_collisions:
        affected.add(lid)
        sid = f"{iid[4:] if iid.startswith('sb::') else iid}__shadow_{prov.source_skill_book}"
        affected.add(sid)
    for lid, iid, _ in report.near_identical:
        affected.add(lid)
    collided = {e[1] for e in report.exact_collisions} | {n[1] for n in report.near_identical}
    for iid in imported:
        if iid not in collided:
            affected.add(iid)
    new_t = recalculate_tension_local(merged, affected)
    for nid, t in new_t.items():
        if nid in merged:
            merged[nid].tension_score = t

    # 8. Mark stale
    meta["global_tension_stale"] = True
    meta["last_import"] = {"skill_book_id": manifest.skill_book_id,
                           "timestamp": now, "version": current_version}
    # Store trust info in meta
    meta["last_trust"] = {"trust": round(trust, 1), "trust_level": trust_level,
                          "difficulty": manifest.difficulty,
                          "quality_score": manifest.quality_score}

    # 9. Persist
    out = {"meta": meta, "concepts": {cid: _node_to_dict(n) for cid, n in merged.items()}}
    with open(local_graph_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    rp = local_graph_path.replace(".json", "_collision_report.json")
    if rp == local_graph_path:
        rp = local_graph_path + ".collision_report.json"
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(dict(
            exact_collisions=report.exact_collisions,
            near_identical=[(a,b,round(s,4)) for a,b,s in report.near_identical],
            nearby_warnings=[(a,b,round(s,4)) for a,b,s in report.nearby_warnings],
            nodes_added=report.nodes_added,
            nodes_bifurcated=report.nodes_bifurcated,
            warnings=report.warnings + warnings,
            trust=round(trust, 1),
            trust_level=trust_level,
        ), f, ensure_ascii=False, indent=2)
    return dict(success=True, nodes_added=report.nodes_added,
                nodes_bifurcated=report.nodes_bifurcated,
                exact_collisions=len(report.exact_collisions),
                nearby_warnings=len(report.nearby_warnings),
                warnings=report.warnings + warnings,
                collision_report_path=rp,
                trust=round(trust, 1),
                trust_level=trust_level)
