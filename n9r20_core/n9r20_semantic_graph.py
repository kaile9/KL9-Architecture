"""N9R20Framework Semantic Graph

Concept knowledge graph with terminology node management.
Tracks academic terms as nodes and their relational edges.
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

@dataclass
class ConceptNode:
    """A concept node in the semantic graph."""
    term: str
    domain: str = ""
    definition: str = ""
    related: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)

class N9R20SemanticGraph:
    """Concept graph for academic term management."""

    def __init__(self):
        self._nodes: Dict[str, ConceptNode] = {}
        self._edges: Dict[str, Set[str]] = {}

    def add_node(self, term: str, domain: str = "", definition: str = "") -> None:
        """Add or update a concept node."""
        if term not in self._nodes:
            self._nodes[term] = ConceptNode(term=term, domain=domain, definition=definition)
            self._edges[term] = set()

    def link(self, term_a: str, term_b: str) -> None:
        """Create bidirectional edge between two terms."""
        if term_a in self._edges and term_b in self._edges:
            self._edges[term_a].add(term_b)
            self._edges[term_b].add(term_a)

    def get_related(self, term: str) -> List[str]:
        """Get terms related to the given term."""
        return list(self._edges.get(term, set()))

    def query(self, domain: str = "") -> List[ConceptNode]:
        """Query nodes by domain."""
        if not domain:
            return list(self._nodes.values())
        return [n for n in self._nodes.values() if n.domain == domain]

__all__ = ["ConceptNode", "N9R20SemanticGraph"]
