"""
graph_backend.py — 概念图谱后端。
BM25 检索 + subgraph 遍历 + 概念 CRUD。
"""

import sqlite3
import json
import re
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = str(Path(__file__).resolve().parent.parent / 'storage' / 'graph.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id          TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    name        TEXT NOT NULL,
    tier1_def   TEXT DEFAULT '',
    tier2_def   TEXT DEFAULT '',
    tier3_def   TEXT DEFAULT '',
    field       TEXT DEFAULT '',
    thinker     TEXT DEFAULT '',
    work        TEXT DEFAULT '',
    usage_count INTEGER DEFAULT 0,
    weight      REAL    DEFAULT 1.0,
    created_at  TEXT,
    last_used   TEXT,
    archived    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS edges (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id     TEXT NOT NULL,
    to_id       TEXT NOT NULL,
    rel_type    TEXT NOT NULL,
    reason      TEXT DEFAULT '',
    confidence  REAL DEFAULT 1.0,
    source_work TEXT DEFAULT '',
    created_at  TEXT,
    FOREIGN KEY (from_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (to_id)   REFERENCES nodes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS thinker_years (
    thinker     TEXT PRIMARY KEY,
    birth_year  INTEGER,
    death_year  INTEGER
);

CREATE TABLE IF NOT EXISTS genealogy (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_name    TEXT NOT NULL,
    session_id      TEXT,
    source_dialogue TEXT,
    drift_vector    TEXT,
    tension_type    TEXT,
    created_at      TEXT
);
"""


# v1.5 新增列迁移 — skillbook 吸收协议
_SKILLBOOK_MIGRATIONS = [
    "ALTER TABLE nodes ADD COLUMN perspective_a TEXT DEFAULT ''",
    "ALTER TABLE nodes ADD COLUMN perspective_b TEXT DEFAULT ''",
    "ALTER TABLE nodes ADD COLUMN tension_score REAL DEFAULT 0.5",
    "ALTER TABLE nodes ADD COLUMN local_confidence REAL DEFAULT 1.0",
    "ALTER TABLE nodes ADD COLUMN is_shadow INTEGER DEFAULT 0",
    "ALTER TABLE nodes ADD COLUMN shadow_of TEXT DEFAULT ''",
]


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Ensure all tables exist (idempotent)
    for stmt in SCHEMA.split(';'):
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--'):
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError:
                pass
    # v1.5 skillbook 吸收协议 — 静默列迁移
    for stmt in _SKILLBOOK_MIGRATIONS:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return conn


def _bm25_score(query: str, text: str) -> float:
    """简易 BM25 评分。"""
    if not text:
        return 0.0
    query_terms = set(query.lower().split())
    text_lower = text.lower()
    score = 0.0
    for term in query_terms:
        if term in text_lower:
            tf = text_lower.count(term) / max(len(text_lower.split()), 1)
            score += tf * 1.5  # simplified IDF
    return score


def search_concepts_bm25(query: str, top_k: int = 6) -> List[Dict]:
    """BM25 关键词检索概念。"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, name, label, tier1_def, tier2_def, tier3_def, "
            "field, thinker, work, usage_count, weight "
            "FROM nodes WHERE archived = 0 AND label = 'Concept'"
        ).fetchall()

        scored = []
        for r in rows:
            text = f"{r['name']} {r['tier1_def']} {r['tier2_def']} {r['thinker'] or ''} {r['field'] or ''}"
            score = _bm25_score(query, text)
            if score > 0:
                scored.append((score, dict(r)))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
    finally:
        conn.close()


def get_subgraph(name: str, max_hops: int = 2) -> Dict:
    """获取以某概念为中心的子图。"""
    conn = _get_conn()
    try:
        # Find seed node
        seed = conn.execute(
            "SELECT id FROM nodes WHERE name = ? AND archived = 0 LIMIT 1",
            (name,)
        ).fetchone()

        if not seed:
            return {"found": False, "nodes": [], "edges": []}

        seed_id = seed['id']

        # BFS up to max_hops
        visited = {seed_id}
        frontier = {seed_id}
        all_edges = []

        for _ in range(max_hops):
            if not frontier:
                break
            placeholders = ','.join('?' * len(frontier))
            new_edges = conn.execute(
                f"SELECT * FROM edges WHERE from_id IN ({placeholders}) OR to_id IN ({placeholders})",
                list(frontier) * 2
            ).fetchall()

            next_frontier = set()
            for e in new_edges:
                all_edges.append(dict(e))
                if e['from_id'] not in visited:
                    next_frontier.add(e['from_id'])
                if e['to_id'] not in visited:
                    next_frontier.add(e['to_id'])

            visited.update(next_frontier)
            frontier = next_frontier

        # Fetch all visited nodes
        node_rows = []
        if visited:
            placeholders = ','.join('?' * len(visited))
            node_rows = conn.execute(
                f"SELECT id, name, label, tier1_def, thinker FROM nodes WHERE id IN ({placeholders})",
                list(visited)
            ).fetchall()

        return {
            "found": True,
            "nodes": [dict(r) for r in node_rows],
            "edges": all_edges,
        }
    finally:
        conn.close()


def expand_definition(name: str, thinker: str = "", tier: int = 1) -> str:
    """按 tier 展开概念定义。"""
    conn = _get_conn()
    try:
        if thinker:
            row = conn.execute(
                "SELECT tier1_def, tier2_def, tier3_def FROM nodes "
                "WHERE name = ? AND thinker = ? AND archived = 0 LIMIT 1",
                (name, thinker)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT tier1_def, tier2_def, tier3_def FROM nodes "
                "WHERE name = ? AND archived = 0 LIMIT 1",
                (name,)
            ).fetchone()

        if not row:
            return ""

        if tier >= 3 and row['tier3_def']:
            return row['tier3_def']
        if tier >= 2 and row['tier2_def']:
            return row['tier2_def']
        return row['tier1_def'] or row['tier2_def'] or row['tier3_def'] or name
    finally:
        conn.close()


def find_same_name_variants(name: str) -> List[Dict]:
    """查找同名概念的不同思想家版本。"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, name, thinker, tier1_def FROM nodes "
            "WHERE name = ? AND archived = 0",
            (name,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_concept(name: str, thinker: str = "") -> Optional[Dict]:
    """获取单个概念。"""
    conn = _get_conn()
    try:
        if thinker:
            row = conn.execute(
                "SELECT * FROM nodes WHERE name = ? AND thinker = ? AND archived = 0 LIMIT 1",
                (name, thinker)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM nodes WHERE name = ? AND archived = 0 LIMIT 1",
                (name,)
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_concepts_in_field(field: str) -> List[Dict]:
    """获取某领域的所有概念。"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM nodes WHERE field = ? AND archived = 0",
            (field,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_thinker_birth_year(thinker: str) -> Optional[int]:
    """获取思想家出生年份。"""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT birth_year FROM thinker_years WHERE thinker = ?",
            (thinker,)
        ).fetchone()
        return row['birth_year'] if row else None
    finally:
        conn.close()


def store_concept(
    name: str,
    tier1: str = "",
    tier2: str = "",
    tier3: str = "",
    thinker: str = "",
    work: str = "",
    field: str = "",
    perspective_a: str = "",       # v1.5 新增
    perspective_b: str = "",       # v1.5 新增
    tension_score: float = 0.5,    # v1.5 新增
    local_confidence: float = 1.0, # v1.5 新增
    is_shadow: bool = False,       # v1.5 新增
    shadow_of: str = "",           # v1.5 新增
    explicit_id: str = "",         # v1.5 新增: 覆盖自动生成的 concept_id
) -> str:
    """存储概念。返回 concept_id。"""
    conn = _get_conn()
    try:
        if explicit_id:
            concept_id = explicit_id
        else:
            concept_id = f"concept:{name}:{thinker}" if thinker else f"concept:{name}:"
        now = datetime.now().isoformat()

        existing = conn.execute("SELECT id FROM nodes WHERE id = ?", (concept_id,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE nodes SET tier1_def=?, tier2_def=?, tier3_def=?, "
                "field=?, work=?, last_used=?, "
                "perspective_a=?, perspective_b=?, tension_score=?, "
                "local_confidence=?, is_shadow=?, shadow_of=? "
                "WHERE id=?",
                (tier1, tier2, tier3, field, work, now,
                 perspective_a, perspective_b, tension_score,
                 local_confidence, int(is_shadow), shadow_of,
                 concept_id)
            )
        else:
            conn.execute(
                "INSERT INTO nodes (id, label, name, tier1_def, tier2_def, tier3_def, "
                "field, thinker, work, created_at, last_used, "
                "perspective_a, perspective_b, tension_score, "
                "local_confidence, is_shadow, shadow_of) "
                "VALUES (?, 'Concept', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (concept_id, name, tier1, tier2, tier3, field, thinker, work, now, now,
                 perspective_a, perspective_b, tension_score,
                 local_confidence, int(is_shadow), shadow_of)
            )

        conn.commit()
        return concept_id
    finally:
        conn.close()


def store_thinker(name: str, birth_year: int = 0, death_year: int = 0):
    """存储思想家的生卒年份。"""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO thinker_years (thinker, birth_year, death_year) "
            "VALUES (?, ?, ?)",
            (name, birth_year, death_year)
        )
        conn.commit()
    finally:
        conn.close()


def update_concept_weight(name: str, delta: float = 0.01):
    """更新概念使用权重。"""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE nodes SET weight = MAX(0.1, MIN(2.0, weight + ?)), "
            "usage_count = usage_count + 1, last_used = ? "
            "WHERE name = ? AND archived = 0",
            (delta, datetime.now().isoformat(), name)
        )
        conn.commit()
    finally:
        conn.close()


def create_edge(
    from_id: str,
    to_id: str,
    rel_type: str,
    reason: str = "",
    confidence: float = 1.0,
    source_work: str = "",
) -> int:
    """创建概念关系边。"""
    conn = _get_conn()
    try:
        now = datetime.now().isoformat()
        cursor = conn.execute(
            "INSERT INTO edges (from_id, to_id, rel_type, reason, confidence, source_work, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (from_id, to_id, rel_type, reason, confidence, source_work, now)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def consolidate():
    """归档低频概念（usage_count < 2 且 weight < 0.3）。"""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE nodes SET archived = 1 "
            "WHERE usage_count < 2 AND weight < 0.3 AND archived = 0"
        )
        conn.commit()
    finally:
        conn.close()


def get_stats() -> Dict:
    """获取图谱统计信息。"""
    conn = _get_conn()
    try:
        concepts_active = conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE label = 'Concept' AND archived = 0"
        ).fetchone()[0]
        concepts_archived = conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE label = 'Concept' AND archived = 1"
        ).fetchone()[0]
        num_edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        top_concepts = conn.execute(
            "SELECT name, weight, usage_count FROM nodes "
            "WHERE label = 'Concept' AND archived = 0 "
            "ORDER BY weight DESC LIMIT 5"
        ).fetchall()

        return {
            "concepts_active": concepts_active,
            "concepts_archived": concepts_archived,
            "edges": num_edges,
            "top_concepts": [{"name": r[0], "weight": r[1], "usage_count": r[2]} for r in top_concepts],
        }
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# KL9-RHIZOME v1.5 新增：张力共振检索 + 谱系边
# ═══════════════════════════════════════════════════════════════

# 张力类型关键词映射 — 用于计算 resonance
TENSION_KEYWORD_MAP = {
    "eternal_vs_finite": ["永恒", "有限", "时间", "瞬间", "绵延", "不朽", "暂存"],
    "mediated_vs_real": ["中介", "直接", "表征", "本真", "符号", "真实", "拟像"],
    "freedom_vs_security": ["自由", "安全", "控制", "解放", "规训", "自主"],
    "truth_vs_slander": ["真理", "谎言", "真实", "虚构", "知识", "权力", "话语"],
    "regression_vs_growth": ["退化", "进步", "发展", "衰败", "历史"],
    "economic_vs_grotesque": ["经济", "荒诞", "异化", "商品", "身体", "消费"],
}


def _tension_resonance_score(concept_text: str, tension_type: str) -> float:
    """计算概念文本与张力类型的关键词共振度。"""
    if not tension_type or tension_type not in TENSION_KEYWORD_MAP:
        return 0.3  # 未知张力类型给低基线

    keywords = TENSION_KEYWORD_MAP[tension_type]
    text_lower = concept_text.lower()
    hits = sum(1 for kw in keywords if kw in text_lower)
    return min(hits / max(len(keywords), 1), 1.0)


def dialogical_retrieval(
    query: str,
    tension_context: Optional[Dict] = None,
    top_k: int = 6,
    include_genealogy: bool = False,
) -> Dict:
    """
    v1.5 核心：以张力共振替代 BM25 的对话式概念检索。

    检索策略:
        1. BM25 粗筛 top_k*3 个候选
        2. 根据 tension_context 计算张力共振分
        3. 综合排序：BM25 * 0.4 + tension_resonance * 0.6
        4. 若 include_genealogy=True，附谱系漂移路径

    Args:
        query: 用户查询文本
        tension_context: {'tension_type': str, 'perspective_a': str, 'perspective_b': str}
        top_k: 返回数量
        include_genealogy: 是否包含谱系漂移路径

    Returns:
        {
            'candidates': [{
                'concept_id': str,
                'name': str,
                'thinker': str,
                'definition': str,
                'tension_resonance': float,
                'resonance_source': 'keyword' | 'genealogy' | 'keyword_fallback',
                'frame_tension': str,
                'genealogy_trace': [...]  # include_genealogy=True 时
            }],
            'pool_signature': str
        }
    """
    tension_type = ""
    if tension_context:
        tension_type = tension_context.get("tension_type", "")

    # Step 1: BM25 粗筛
    bm25_results = search_concepts_bm25(query, top_k=top_k * 3)

    if not bm25_results:
        return {"candidates": [], "pool_signature": "bm25:0+resonance:0"}

    # Step 2: 计算张力共振
    candidates = []
    for c in bm25_results:
        concept_text = (
            f"{c.get('name', '')} "
            f"{c.get('tier1_def', c.get('definition', ''))} "
            f"{c.get('tier2_def', '')} "
            f"{c.get('thinker', '')} "
            f"{c.get('field', '')}"
        )
        resonance = _tension_resonance_score(concept_text, tension_type)

        candidates.append({
            "concept_id": c.get("id", ""),
            "name": c.get("name", ""),
            "thinker": c.get("thinker", ""),
            "definition": c.get("tier1_def", c.get("definition", "")),
            "tension_resonance": round(resonance, 2),
            "resonance_source": "keyword" if resonance > 0.3 else "keyword_fallback",
            "frame_tension": "",
            "genealogy_trace": [],
        })

    # Step 3: 综合排序 (BM25归一 + 张力共振加权)
    # 简化：直接按 resonance 分组，有共振的排前面
    candidates.sort(key=lambda x: x["tension_resonance"], reverse=True)

    # Step 4: 谱系增强
    if include_genealogy:
        for c in candidates[:top_k]:
            paths = get_genealogy_paths(c["name"])
            if paths:
                c["genealogy_trace"] = paths
                # 谱系数据增强共振分
                c["tension_resonance"] = min(c["tension_resonance"] + 0.15, 1.0)
                c["resonance_source"] = "genealogy"

    result = candidates[:top_k]
    pool_sig = (
        f"bm25:{len(bm25_results)}"
        f"+resonance:{sum(1 for c in result if c['resonance_source'] != 'keyword_fallback')}"
    )

    return {
        "candidates": result,
        "pool_signature": pool_sig,
    }


def write_genealogy_edge(
    concept_name: str,
    session_id: str = "",
    source_dialogue: str = "",
    drift_vector: str = "",
    tension_type: str = "",
) -> int:
    """
    v1.5 新增：谱系边写入。
    记录概念在对话式激活中的语义漂移路径。

    Args:
        concept_name: 概念名
        session_id: 会话 ID
        source_dialogue: 触发漂移的对话/理论改造描述
        drift_vector: 漂移方向（如 "从形上批判转向经验分析"）
        tension_type: 关联的张力类型

    Returns:
        genealogy 记录 ID
    """
    conn = _get_conn()
    try:
        now = datetime.now().isoformat()
        cursor = conn.execute(
            "INSERT INTO genealogy "
            "(concept_name, session_id, source_dialogue, drift_vector, tension_type, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (concept_name, session_id, source_dialogue, drift_vector, tension_type, now),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_genealogy_paths(concept_name: str, limit: int = 5) -> List[Dict]:
    """
    v1.5 新增：获取概念的谱系漂移路径。

    Args:
        concept_name: 概念名
        limit: 最大返回数

    Returns:
        [{id, source_dialogue, drift_vector, tension_type, created_at}, ...]
    """
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT id, source_dialogue, drift_vector, tension_type, created_at "
            "FROM genealogy "
            "WHERE concept_name = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (concept_name, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


# ═══════════════════════════════════════════
# GraphBackend — 标准接口包装类
# ═══════════════════════════════════════════

class GraphBackend:
    """概念图谱标准接口。

    封装 dialogical_retrieval 等图谱操作，
    供 orchestrator 和其他技能统一调用。
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def dialogical_retrieval(self, query: str, tension_context: Optional[dict] = None,
                             top_k: int = 5) -> List[dict]:
        """以张力共振替代 BM25 相关性排序的概念检索。"""
        return dialogical_retrieval(query, tension_context, top_k)

    def search_concepts(self, query: str, field: Optional[str] = None,
                        limit: int = 10) -> List[dict]:
        """BM25 fallback 概念搜索。"""
        return search_concepts_bm25(query, field, limit)

    def get_concept(self, concept_id: str) -> Optional[dict]:
        """按 ID 获取单个概念。"""
        return get_concept(concept_id)

    def get_subgraph(self, concept_id: str, depth: int = 2) -> dict:
        """获取概念子图。"""
        return get_subgraph(concept_id, depth)

    def store_concept(self, name: str, tier1_def: str, **kwargs) -> str:
        """存储新概念，返回概念 ID。"""
        return store_concept(name, tier1_def, **kwargs)

    def write_genealogy_edge(self, concept_name: str, source_dialogue: str,
                             drift_vector: Optional[dict] = None,
                             tension_type: Optional[str] = None) -> str:
        """写入谱系边。"""
        return write_genealogy_edge(concept_name, source_dialogue, drift_vector, tension_type)

    def get_genealogy_paths(self, concept_name: str, limit: int = 10) -> List[dict]:
        """获取概念谱系路径。"""
        return get_genealogy_paths(concept_name, limit)

    def update_concept_weight(self, concept_id: str, delta: float) -> None:
        """更新概念权重。"""
        update_concept_weight(concept_id, delta)

    def get_stats(self) -> dict:
        """获取图谱统计。"""
        return get_stats()
