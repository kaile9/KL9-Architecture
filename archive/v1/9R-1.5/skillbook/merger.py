"""Core merge logic for concept graphs."""
from copy import deepcopy
from .models import ConceptNode, CollisionReport, ConceptProvenance

def _strip(concept_id: str) -> str:
    return concept_id[4:] if concept_id.startswith("sb::") else concept_id

def _deep_copy_node(n: ConceptNode) -> ConceptNode:
    return ConceptNode(
        concept_id=n.concept_id, name=n.name, definition=n.definition,
        perspective_a=n.perspective_a, perspective_b=n.perspective_b,
        tension_score=n.tension_score, edges=list(n.edges),
        provenance=deepcopy(n.provenance), local_confidence=n.local_confidence,
        is_shadow=n.is_shadow, shadow_of=n.shadow_of,
    )

def merge_graphs(
    local: dict[str, ConceptNode],
    imported: dict[str, ConceptNode],
    report: CollisionReport,
    provenance: ConceptProvenance,
) -> dict[str, ConceptNode]:
    """Merge imported concepts into local graph per collision report."""
    merged = {cid: _deep_copy_node(n) for cid, n in local.items()}
    near_set = {iid for _, iid, _ in report.near_identical}
    exact_set = {iid for _, iid in report.exact_collisions}
    # near_identical → merge
    for lid, iid, _sim in report.near_identical:
        ln, im = merged[lid], imported[iid]
        merged[lid] = ConceptNode(
            concept_id=ln.concept_id, name=ln.name,
            definition=ln.definition + "\n---\n[来自" + provenance.source_skill_book + "] " + im.definition,
            perspective_a=ln.perspective_a, perspective_b=ln.perspective_b,
            tension_score=ln.tension_score,
            edges=list(set(ln.edges + im.edges)),
            provenance=ln.provenance, local_confidence=ln.local_confidence,
        )
    # exact_collisions → shadow
    for lid, iid in report.exact_collisions:
        im = imported[iid]
        sid = f"{_strip(im.concept_id)}__shadow_{provenance.source_skill_book}"
        shadow = ConceptNode(
            concept_id=sid, name=im.name, definition=im.definition,
            perspective_a=im.perspective_a, perspective_b=im.perspective_b,
            tension_score=im.tension_score, edges=list(im.edges) + [lid],
            provenance=deepcopy(provenance),
            local_confidence=provenance.quality_tier / 5.0,
            is_shadow=True, shadow_of=lid,
        )
        merged[sid] = shadow
        if sid not in merged[lid].edges:
            merged[lid].edges.append(sid)
    # No-conflict → add
    handled = near_set | exact_set
    for iid, im in imported.items():
        if iid not in handled:
            merged[iid] = ConceptNode(
                concept_id=iid, name=im.name, definition=im.definition,
                perspective_a=im.perspective_a, perspective_b=im.perspective_b,
                tension_score=im.tension_score, edges=list(im.edges),
                provenance=deepcopy(provenance),
                local_confidence=provenance.quality_tier / 5.0,
            )
    # Prune dead edges
    all_ids = set(merged)
    for n in merged.values():
        n.edges = [e for e in n.edges if e in all_ids]
    return merged
