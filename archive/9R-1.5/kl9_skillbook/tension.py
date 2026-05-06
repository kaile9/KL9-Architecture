"""Local tension recalculation after graph mutations."""
import math
from .models import ConceptNode

def get_subgraph(graph: dict[str, ConceptNode], seed_ids: set[str],
                 hop_radius: int = 2) -> set[str]:
    """Return all node IDs within hop_radius of any seed."""
    visited, frontier = set(seed_ids), set(seed_ids)
    for _ in range(hop_radius):
        nxt = set()
        for nid in frontier:
            node = graph.get(nid)
            if node:
                for e in node.edges:
                    if e not in visited:
                        visited.add(e); nxt.add(e)
        frontier = nxt
    return visited

def recalculate_tension_local(graph: dict[str, ConceptNode],
                              affected_node_ids: set[str],
                              hop_radius: int = 2) -> dict[str, float]:
    """Recalculate tension_score in 2-hop neighbourhood. Returns {id: new_score}."""
    sub = get_subgraph(graph, affected_node_ids, hop_radius)
    result: dict[str, float] = {}
    for nid in sub:
        node = graph.get(nid)
        if node is None:
            continue
        t = 0.5 + 0.1 * math.log(1 + len(node.edges)) - 0.1 * node.local_confidence
        if node.is_shadow:
            t += 0.15
        result[nid] = max(0.0, min(1.0, t))
    return result
