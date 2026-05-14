"""
9R-2.1 — Semantic Graph + Word Frequency Statistics

Concept knowledge graph with:
- Hebbian learning (co-occurrence strengthens edges)
- Exponential decay (half-life configurable)
- Word frequency tracking (from user's representative works)
- Community detection (simplified label propagation)
- Tension mapping (inter-cluster tension calculation)

Persists to graph.db (v2 schema).
"""

from __future__ import annotations

import json
import math
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class GraphNode:
    term: str
    definition: str = ""
    domain: str = ""
    confidence: float = 0.5
    source: str = ""
    frequency: int = 1
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "term": self.term,
            "definition": self.definition,
            "domain": self.domain,
            "confidence": self.confidence,
            "frequency": self.frequency,
        }


@dataclass
class GraphEdge:
    source: str
    target: str
    relation_type: str = "related"
    weight: float = 0.5
    tension_type: str = ""
    evidence: str = ""

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "weight": self.weight,
            "tension_type": self.tension_type,
        }


class SemanticGraph:
    """Concept knowledge graph with word frequency tracking.

    Implements:
    - Hebbian learning: co-occurring concepts strengthen edge weights
    - Exponential decay: unused edges decay over time
    - Word frequency: term occurrence counting from input texts
    - Community detection: simplified label propagation
    """

    def __init__(
        self,
        db_path: str | Path | None = None,
        decay_half_life: float = 86400.0,  # 24h
        decay_threshold: float = 0.05,
        hebbian_increment: float = 0.1,
    ):
        self.db_path = str(db_path) if db_path else ":memory:"
        self.decay_half_life = decay_half_life
        self.decay_threshold = decay_threshold
        self.hebbian_increment = hebbian_increment
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._init_tables()
        return self._conn

    def _init_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS nodes_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL UNIQUE,
                definition TEXT DEFAULT '',
                domain TEXT DEFAULT '',
                confidence REAL DEFAULT 0.5,
                source TEXT DEFAULT '',
                frequency INTEGER DEFAULT 1,
                created_at REAL,
                updated_at REAL,
                access_count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS edges_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_node_id INTEGER NOT NULL,
                target_node_id INTEGER NOT NULL,
                relation_type TEXT DEFAULT 'related',
                weight REAL DEFAULT 0.5,
                tension_type TEXT DEFAULT '',
                evidence TEXT DEFAULT '',
                created_at REAL,
                FOREIGN KEY (source_node_id) REFERENCES nodes_v2(id),
                FOREIGN KEY (target_node_id) REFERENCES nodes_v2(id)
            );
            CREATE TABLE IF NOT EXISTS word_frequencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                source_doc TEXT,
                count INTEGER DEFAULT 1,
                created_at REAL,
                UNIQUE(term, source_doc)
            );
            CREATE INDEX IF NOT EXISTS idx_nodes_term ON nodes_v2(term);
            CREATE INDEX IF NOT EXISTS idx_nodes_domain ON nodes_v2(domain);
            CREATE INDEX IF NOT EXISTS idx_edges_src ON edges_v2(source_node_id);
            CREATE INDEX IF NOT EXISTS idx_edges_tgt ON edges_v2(target_node_id);
        """)
        self.conn.commit()

    # ── Node Operations ──

    def add_node(self, term: str, definition: str = "", domain: str = "",
                 confidence: float = 0.5, source: str = "") -> int:
        """Add or update a concept node. Returns node id."""
        now = time.time()
        cursor = self.conn.cursor()
        existing = cursor.execute(
            "SELECT id, frequency FROM nodes_v2 WHERE term = ?", (term,)
        ).fetchone()
        if existing:
            node_id, freq = existing
            cursor.execute(
                """UPDATE nodes_v2 SET definition = ?, domain = ?, confidence = ?,
                   source = ?, frequency = ?, updated_at = ?, access_count = access_count + 1
                   WHERE id = ?""",
                (definition or "", domain, confidence, source, freq + 1, now, node_id),
            )
        else:
            cursor.execute(
                """INSERT INTO nodes_v2 (term, definition, domain, confidence, source, frequency, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                (term, definition, domain, confidence, source, now, now),
            )
            node_id = cursor.lastrowid or 0
        self.conn.commit()
        return node_id

    def get_node(self, term: str) -> Optional[GraphNode]:
        row = self.conn.execute(
            "SELECT term, definition, domain, confidence, source, frequency FROM nodes_v2 WHERE term = ?",
            (term,),
        ).fetchone()
        if row:
            return GraphNode(
                term=row[0], definition=row[1], domain=row[2],
                confidence=row[3], source=row[4], frequency=row[5],
            )
        return None

    def get_all_nodes(self) -> list[GraphNode]:
        rows = self.conn.execute(
            "SELECT term, definition, domain, confidence, source, frequency FROM nodes_v2"
        ).fetchall()
        return [GraphNode(term=r[0], definition=r[1], domain=r[2], confidence=r[3],
                          source=r[4], frequency=r[5]) for r in rows]

    # ── Edge Operations ──

    def add_edge(self, source_term: str, target_term: str,
                 relation_type: str = "related", tension_type: str = "") -> None:
        """Add or strengthen edge between two concepts (Hebbian learning)."""
        src_node = self.conn.execute("SELECT id FROM nodes_v2 WHERE term = ?", (source_term,)).fetchone()
        tgt_node = self.conn.execute("SELECT id FROM nodes_v2 WHERE term = ?", (target_term,)).fetchone()
        if not src_node or not tgt_node:
            return

        src_id, tgt_id = src_node[0], tgt_node[0]
        now = time.time()
        existing = self.conn.execute(
            "SELECT id, weight FROM edges_v2 WHERE source_node_id = ? AND target_node_id = ?",
            (src_id, tgt_id),
        ).fetchone()
        if existing:
            new_weight = min(1.0, existing[1] + self.hebbian_increment)
            self.conn.execute(
                "UPDATE edges_v2 SET weight = ?, created_at = ? WHERE id = ?",
                (new_weight, now, existing[0]),
            )
        else:
            self.conn.execute(
                """INSERT INTO edges_v2 (source_node_id, target_node_id, relation_type, weight, tension_type, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (src_id, tgt_id, relation_type, self.hebbian_increment, tension_type, now),
            )
        self.conn.commit()

    def get_edges(self, term: str) -> list[GraphEdge]:
        """Get all edges for a concept node."""
        node = self.conn.execute("SELECT id FROM nodes_v2 WHERE term = ?", (term,)).fetchone()
        if not node:
            return []
        node_id = node[0]
        edges: list[GraphEdge] = []
        for row in self.conn.execute(
            """SELECT n1.term, n2.term, e.relation_type, e.weight, e.tension_type
               FROM edges_v2 e
               JOIN nodes_v2 n1 ON e.source_node_id = n1.id
               JOIN nodes_v2 n2 ON e.target_node_id = n2.id
               WHERE e.source_node_id = ? OR e.target_node_id = ?""",
            (node_id, node_id),
        ):
            edges.append(GraphEdge(
                source=row[0], target=row[1],
                relation_type=row[2], weight=row[3], tension_type=row[4],
            ))
        return edges

    # ── Hebbian Learning ──

    def co_activate(self, terms: list[str]) -> None:
        """Co-activate concept nodes: strengthen edges between all pairs."""
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                self.add_edge(terms[i], terms[j], relation_type="co_occurrence")

    # ── Exponential Decay ──

    def decay_edges(self) -> int:
        """Apply exponential decay to all edges. Remove below threshold. Returns removed count."""
        now = time.time()
        lambda_decay = math.log(2) / self.decay_half_life
        cursor = self.conn.cursor()
        removed = 0
        for row in cursor.execute("SELECT id, weight, created_at FROM edges_v2").fetchall():
            edge_id, weight, created_at = row
            age = now - created_at
            new_weight = weight * math.exp(-lambda_decay * age)
            if new_weight < self.decay_threshold:
                cursor.execute("DELETE FROM edges_v2 WHERE id = ?", (edge_id,))
                removed += 1
            else:
                cursor.execute("UPDATE edges_v2 SET weight = ? WHERE id = ?", (new_weight, edge_id))
        self.conn.commit()
        return removed

    # ── Word Frequency Statistics ──

    def ingest_text(self, text: str, source_doc: str = "") -> dict[str, int]:
        """Extract word frequencies from text. Returns term→count mapping."""
        # Extract terms matching known theoretical/concept vocabulary
        from .dna import StyleProfile
        profile = StyleProfile()
        all_terms = profile.theoretical_markers + profile.concept_markers

        term_counts: dict[str, int] = {}
        for term in all_terms:
            count = text.count(term)
            if count > 0:
                term_counts[term] = count

        now = time.time()
        for term, count in term_counts.items():
            existing = self.conn.execute(
                "SELECT id, count FROM word_frequencies WHERE term = ? AND source_doc = ?",
                (term, source_doc),
            ).fetchone()
            if existing:
                self.conn.execute(
                    "UPDATE word_frequencies SET count = count + ?, created_at = ? WHERE id = ?",
                    (count, now, existing[0]),
                )
            else:
                self.conn.execute(
                    "INSERT INTO word_frequencies (term, source_doc, count, created_at) VALUES (?, ?, ?, ?)",
                    (term, source_doc, count, now),
                )

            # Also update node frequency
            self.add_node(term, source=source_doc)

        self.conn.commit()
        return term_counts

    def get_frequencies(self, top_n: int = 50) -> list[tuple[str, int]]:
        """Get top N terms by total frequency across all sources."""
        rows = self.conn.execute(
            "SELECT term, SUM(count) as total FROM word_frequencies GROUP BY term ORDER BY total DESC LIMIT ?",
            (top_n,),
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def get_frequencies_by_source(self, source_doc: str) -> list[tuple[str, int]]:
        """Get term frequencies for a specific source document."""
        rows = self.conn.execute(
            "SELECT term, count FROM word_frequencies WHERE source_doc = ? ORDER BY count DESC",
            (source_doc,),
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def get_global_frequency_table(self) -> dict[str, int]:
        """Get global frequency table as dict."""
        return dict(self.get_frequencies(top_n=200))

    # ── Community Detection ──

    def detect_communities(self, max_iterations: int = 20) -> dict[str, int]:
        """Simplified label propagation for community detection."""
        nodes = self.get_all_nodes()
        if not nodes:
            return {}
        labels = {n.term: i for i, n in enumerate(nodes)}
        for _ in range(max_iterations):
            changed = False
            for node in nodes:
                edges = self.get_edges(node.term)
                if not edges:
                    continue
                neighbor_labels: Counter = Counter()
                for edge in edges:
                    neighbor = edge.target if edge.source == node.term else edge.source
                    if neighbor in labels:
                        neighbor_labels[labels[neighbor]] += edge.weight
                if neighbor_labels:
                    most_common = neighbor_labels.most_common(1)[0][0]
                    if labels[node.term] != most_common:
                        labels[node.term] = most_common
                        changed = True
            if not changed:
                break
        return labels

    # ── Tension Mapping ──

    def get_inter_cluster_tensions(self) -> list[dict]:
        """Calculate tensions between concept clusters."""
        communities = self.detect_communities()
        clusters: dict[int, list[str]] = {}
        for term, cluster_id in communities.items():
            clusters.setdefault(cluster_id, []).append(term)
        tensions: list[dict] = []
        cluster_ids = list(clusters.keys())
        for i in range(len(cluster_ids)):
            for j in range(i + 1, len(cluster_ids)):
                c1, c2 = cluster_ids[i], cluster_ids[j]
                cross_edges = 0
                tension_sum = 0.0
                for t1 in clusters[c1]:
                    for edge in self.get_edges(t1):
                        if (edge.source == t1 and edge.target in clusters[c2]) or \
                           (edge.target == t1 and edge.source in clusters[c2]):
                            cross_edges += 1
                            if edge.tension_type:
                                tension_sum += edge.weight
                if cross_edges > 0:
                    tensions.append({
                        "cluster_a": c1,
                        "cluster_b": c2,
                        "cross_edges": cross_edges,
                        "tension_score": tension_sum / cross_edges if cross_edges else 0,
                    })
        return tensions

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
