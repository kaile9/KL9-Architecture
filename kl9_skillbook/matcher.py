"""Levenshtein similarity and collision detection."""
from .models import ConceptNode, CollisionReport

def levenshtein_ratio(s1: str, s2: str) -> float:
    """Normalized Levenshtein similarity [0.0, 1.0]."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j+1]+1, curr[j]+1, prev[j]+(c1!=c2)))
        prev = curr
    return 1.0 - prev[-1] / max(len(s1), len(s2))

def detect_collisions(
    local_concepts: dict[str, ConceptNode],
    imported_concepts: dict[str, ConceptNode],
) -> CollisionReport:
    """Classify imported concepts vs local graph into collision categories."""
    exact: list[tuple[str, str]] = []
    near: list[tuple[str, str, float]] = []
    nearby: list[tuple[str, str, float]] = []
    lid_by_name = {n.name: lid for lid, n in local_concepts.items()}
    lids, lnames = list(local_concepts.keys()), [n.name for n in local_concepts.values()]
    for iid, inode in imported_concepts.items():
        if inode.name in lid_by_name:
            exact.append((lid_by_name[inode.name], iid))
            continue
        best_r, best_lid = 0.0, ""
        for lid, lname in zip(lids, lnames):
            r = levenshtein_ratio(inode.name, lname)
            if r > best_r:
                best_r, best_lid = r, lid
        if best_r >= 0.95:
            near.append((best_lid, iid, best_r))
        elif best_r >= 0.70:
            nearby.append((best_lid, iid, best_r))
    collided = {e[1] for e in exact} | {n[1] for n in near}
    added = sum(1 for iid in imported_concepts if iid not in collided)
    return CollisionReport(
        exact_collisions=exact, near_identical=near, nearby_warnings=nearby,
        nodes_added=added, nodes_bifurcated=len(exact),
        warnings=[f"nearby_warning: '{iid}' ~= '{lid}' (sim={r:.3f})"
                  for lid, iid, r in nearby],
    )
