"""
memory.py — 持久记忆后端。
会话记录 / 反馈 / 书目检索 / 睡眠巩固。
"""

import sqlite3
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# ── op_count & consolidate 自动触发 ─────────────────────────────────────────────────
# 每 100 次写操作自动触发 graph_backend.consolidate（后台线程）
# ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄

OP_COUNT_PATH = Path(__file__).resolve().parent.parent / 'storage' / '.op_count'
_CONSOLIDATE_LOCK = threading.Lock()


def _increment_op_count() -> int:
    """原子性递增 op_count，返回新值。"""
    try:
        OP_COUNT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not OP_COUNT_PATH.exists():
            OP_COUNT_PATH.write_text("0")
        # 简单的文件锁定保护（单进程多线程环境下足够）
        with _CONSOLIDATE_LOCK:
            val = int(OP_COUNT_PATH.read_text().strip() or "0")
            val += 1
            OP_COUNT_PATH.write_text(str(val))
            return val
    except Exception:
        return 0


def _maybe_trigger_consolidate():
    """检查 op_count，达到 100 的倍数时后台触发 consolidate。"""
    count = _increment_op_count()
    if count > 0 and count % 100 == 0:
        try:
            import graph_backend as _gb
            # 后台线程执行，避免阻塞主流程
            threading.Thread(
                target=_gb.consolidate,
                name=f"consolidate-bg-{count}",
                daemon=True,
            ).start()
        except Exception:
            pass  # consolidate 失败不影响主流程


DB_PATH = str(Path(__file__).resolve().parent.parent / 'storage' / 'memory.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def record_session(
    session_id: str,
    query: str,
    response: str,
    concepts_used: List[str],
    field: str = "",
    reasoning_type: str = "",
) -> None:
    """记录一次会话。"""
    conn = _get_conn()
    try:
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO sessions "
            "(session_id, query, response, concepts_used, field, reasoning_type, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, query, response, json.dumps(concepts_used, ensure_ascii=False),
             field, reasoning_type, now)
        )
        conn.commit()
    finally:
        conn.close()
    _maybe_trigger_consolidate()


def get_session(session_id: str) -> Optional[Dict]:
    """获取会话记录。"""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def search_reading_list(query: str, top_k: int = 3) -> List[Dict]:
    """检索相关书目。"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT title, author, field, year, impact_note, related_models "
            "FROM reading_list ORDER BY temporal_weight DESC"
        ).fetchall()

        scored = []
        query_lower = query.lower()
        for r in rows:
            text = f"{r['title']} {r['author']} {r['field'] or ''} {r['impact_note'] or ''} {r['related_models'] or ''}"
            score = sum(1 for w in query_lower.split() if w in text.lower())
            if score > 0:
                scored.append((score, dict(r)))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
    finally:
        conn.close()


def record_feedback(
    session_id: str,
    feedback_type: str,
    score: float,
    text: str = "",
    corrected_data: Optional[Dict] = None,
) -> None:
    """记录用户反馈。"""
    conn = _get_conn()
    try:
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO feedback (session_id, feedback_type, score, text, corrected_data, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, feedback_type, score, text,
             json.dumps(corrected_data, ensure_ascii=False) if corrected_data else None,
             now)
        )
        conn.commit()
    finally:
        conn.close()
    _maybe_trigger_consolidate()


def get_stats() -> Dict:
    """获取记忆统计信息。"""
    conn = _get_conn()
    try:
        sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        books = conn.execute("SELECT COUNT(*) FROM reading_list").fetchone()[0]
        feedback_count = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        return {
            "sessions": sessions,
            "books_in_reading_list": books,
            "feedback_count": feedback_count,
        }
    finally:
        conn.close()


# ── KL9-RHIZOME v1.5 扩展接口 ──────────────────────────────────────

def record_dual_session(
    session_id: str,
    query: str,
    dual_state,
    response: str,
    suspension_quality: str = "genuine",
) -> None:
    """记录二重态会话。"""
    tension_type = getattr(dual_state, 'tension_type', 'unknown') if dual_state else 'unknown'
    return record_session(
        session_id=session_id,
        query=query,
        response=response,
        concepts_used=[],
        field=tension_type,
        reasoning_type="dual_fold",
    )


def inject_session_metadata(session_id: str, metadata: Dict) -> None:
    """注入会话元数据。零 token 开销。"""
    # 存储到 fold_feedback 表作为元数据
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO fold_feedback (session_id, fold_depth, dna_score, suspension_quality, weight_update) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, 0, 0.0, "metadata_injected", 0.0)
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
    _maybe_trigger_consolidate()


def retrieve_by_tension_context(
    query: str,
    tension_type: str,
    top_k: int = 5,
) -> List[Dict]:
    """张力上下文驱动检索（共振度排序，非权重衰减）。

    Args:
        query: 当前查询文本
        tension_type: 当前张力类型（如 "eternal_vs_finite"）
        top_k: 返回条数

    Returns:
        List[Dict] 按共振度降序的历史会话摘要列表，
        每项含 session_id, query, response_preview, tension_type, fold_depth, timestamp
    """
    import math
    from datetime import datetime as dt

    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT session_id, query, response, field, reasoning_type, timestamp "
            "FROM sessions ORDER BY timestamp DESC LIMIT 200"
        ).fetchall()

        now = dt.now()
        scored = []
        for r in rows:
            record_tension = r["field"] or ""
            record_type = r["reasoning_type"] or ""

            # 1) 张力类型共振度：同类型 > 部分匹配
            if record_tension == tension_type:
                tension_resonance = 1.0
            elif tension_type and record_tension and (
                tension_type in record_tension or record_tension in tension_type
            ):
                tension_resonance = 0.5
            elif record_type == "dual_fold":
                tension_resonance = 0.3
            else:
                tension_resonance = 0.1

            # 2) 查询文本相关性
            ql = query.lower()
            record_text = f"{r['query']} {r.get('response', '')[:200]}"
            text_score = sum(1 for w in ql.split() if w in record_text.lower()) / max(len(ql.split()), 1)

            # 3) 时间衰减: exp(-λ×days), λ=0.01
            try:
                ts = dt.fromisoformat(r["timestamp"])
                days = (now - ts).total_seconds() / 86400
                time_decay = math.exp(-0.01 * days)
            except Exception:
                time_decay = 0.5

            # 4) 折叠深度因子（从 reasoning_type 推断）
            fold_depth_factor = 1.3 if record_type == "dual_fold" else 1.0

            # 综合共振度 = 张力×文本×时间×折叠
            resonance = tension_resonance * (1.0 + text_score) * time_decay * fold_depth_factor
            if resonance > 0.05:
                scored.append((resonance, {
                    "session_id": r["session_id"],
                    "query": r["query"],
                    "response_preview": (r.get("response") or "")[:300],
                    "tension_type": record_tension,
                    "fold_depth": 1 if record_type == "dual_fold" else 0,
                    "timestamp": r["timestamp"],
                    "resonance": round(resonance, 4),
                }))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
    finally:
        conn.close()


# ═══════════════════════════════════════════
# MemoryBackend — 标准接口包装类
# ═══════════════════════════════════════════

class MemoryBackend:
    """持久记忆标准接口。

    封装会话记录、反馈存储、元数据注入等操作，
    供 orchestrator 统一调用。
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def record_session(self, session_id: str, query: str, response: str,
                       dual_state_snapshot: Optional[Dict] = None) -> None:
        """记录一次会话。"""
        record_session(session_id, query, response, dual_state_snapshot)

    def record_dual_session(self, session_id: str, query: str, response: str,
                            dual_state: Optional[Dict] = None) -> None:
        """记录二重会话（含 dual_state）。"""
        record_dual_session(session_id, query, response, dual_state)

    def record_feedback(self, session_id: str, fold_depth: int,
                        dna_score: float, suspension_quality: str,
                        weight_update: float) -> None:
        """记录折叠反馈。"""
        record_feedback(session_id, fold_depth, dna_score, suspension_quality, weight_update)

    def inject_session_metadata(self, session_id: str, metadata: Dict) -> None:
        """注入会话元数据，零 token 开销。"""
        inject_session_metadata(session_id, metadata)

    def get_session(self, session_id: str) -> Optional[Dict]:
        """按 ID 获取会话记录。"""
        return get_session(session_id)

    def get_stats(self) -> Dict:
        """获取记忆统计。"""
        return get_stats()

    def search_reading_list(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索阅读列表。"""
        return search_reading_list(query, limit)

    def retrieve_by_tension_context(self, query: str, tension_type: str,
                                    top_k: int = 5) -> List[Dict]:
        """张力上下文驱动检索。"""
        return retrieve_by_tension_context(query, tension_type, top_k)
