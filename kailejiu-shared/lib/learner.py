"""
kailejiu-learner
RLHF + curriculum learning + synthetic query generation.
Works entirely on local SQLite data — no external model dependency.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

import graph_backend as GB
import memory as MEM

__file__ = __file__ if '__file__' in dir() else 'os.path.join(os.path.dirname(__file__), "../../kailejiu-shared/lib")/learner.py'

parent = Path(__file__).parent
STATE_FILE = parent.parent / 'storage' / 'learner_state.json'


def _load_state():
    """Load learner state from JSON file."""
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
    except Exception:
        pass
    return {
        "sessions_seen": [],
        "avg_score_history": [],
        "curriculum_level": "easy",
    }


def _save_state(state):
    """Persist learner state to JSON file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def process_feedback(session_id, feedback_type, text, corrected_concepts=None):
    """
    Main RLHF entry point. Called after user provides explicit feedback.

    feedback_type: "correct" | "wrong" | "correction" | "clarification"
    """
    type_map = {
        "correct": "explicit_correct",
        "wrong": "explicit_wrong",
        "correction": "explicit_correction",
        "clarification": "implicit",
    }
    fb_type = type_map.get(feedback_type, "implicit")

    corrected_data = None
    if corrected_concepts:
        corrected_data = {"concepts": corrected_concepts}

    score_map = {
        "explicit_correct": 1.0,
        "explicit_wrong": 0.0,
        "explicit_correction": 0.4,
        "implicit": 0.5,
    }
    score = score_map.get(fb_type, 0.5)

    result = MEM.record_feedback(
        session_id=session_id,
        feedback_type=fb_type,
        score=score,
        text=text,
        corrected_data=corrected_data,
    )

    _update_curriculum_level(score)
    return result


def _update_curriculum_level(new_score):
    """Update curriculum difficulty based on rolling average of scores."""
    state = _load_state()
    state["avg_score_history"].append(new_score)

    # Keep last 20 scores
    if len(state["avg_score_history"]) > 20:
        state["avg_score_history"] = state["avg_score_history"][-20:]

    avg = sum(state["avg_score_history"]) / len(state["avg_score_history"])

    if avg >= 0.8:
        state["curriculum_level"] = "hard"
    elif avg >= 0.6:
        state["curriculum_level"] = "medium"
    else:
        state["curriculum_level"] = "easy"

    _save_state(state)


def identify_weak_concepts(top_k=5):
    """
    Find concepts by their involvement in unresolved tensions.
    Tension-driven evaluation replaces v5 discrete weighting.
    """
    import sqlite3
    from pathlib import Path

    mem_db = Path(__file__).parent.parent / 'storage' / 'memory.db'
    unresolved = []

    if mem_db.exists():
        conn = None
        try:
            conn = sqlite3.connect(str(mem_db))
            conn.row_factory = sqlite3.Row

            rows = conn.execute("""
                SELECT node_id, fold_depth, tension_type,
                       claim_a, claim_b, irreconcilable_points, suspended
                FROM dual_state_nodes
                WHERE suspended = 0
                ORDER BY fold_depth DESC
            """).fetchall()

            unresolved = [dict(r) for r in rows]
        except sqlite3.OperationalError:
            pass
        finally:
            if conn:
                conn.close()

    graph_db = Path(__file__).parent.parent / 'storage' / 'graph.db'
    concept_map = {}

    if graph_db.exists():
        conn = None
        try:
            conn = sqlite3.connect(str(graph_db))
            conn.row_factory = sqlite3.Row

            rows = conn.execute(
                "SELECT * FROM nodes WHERE label='Concept' AND archived=0"
            ).fetchall()

            for r in rows:
                concept_map[r["name"]] = dict(r)
        except sqlite3.OperationalError:
            pass
        finally:
            if conn:
                conn.close()

    tension_scores = {}

    for node in unresolved:
        text = ' '.join([
            node.get("claim_a", ""),
            node.get("claim_b", ""),
            node.get("irreconcilable_points", ""),
        ])
        depth = node.get("fold_depth", 0)

        for name in concept_map:
            if name in text:
                tension_scores[name] = (
                    tension_scores.get(name, 0) + 1 + depth * 0.5
                )

    results = []
    for name, score in sorted(tension_scores.items(), key=lambda x: x[1], reverse=True):
        entry = dict(concept_map.get(name, {"name": name}))
        entry["tension_score"] = round(score, 2)
        results.append(entry)

    # Add concepts in graph but not in tension_scores with 0 score
    for name, data in concept_map.items():
        if name not in tension_scores:
            entry = dict(data)
            entry["tension_score"] = 0.0
            results.append(entry)

    return results[:top_k]


def _get_random_concepts(n):
    """Get n random concepts from graph.db."""
    import sqlite3
    from pathlib import Path

    db_path = Path(__file__).parent.parent / 'storage' / 'graph.db'

    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT * FROM nodes WHERE label='Concept' AND archived=0 "
        "ORDER BY RANDOM() LIMIT ?",
        (n,)
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def _generate_query_for_concept(concept, level):
    """Generate a synthetic query targeting a concept at given difficulty."""
    name = concept.get("name", "？")
    thinker = concept.get("thinker", "")
    thinker_prefix = f"{thinker}的" if thinker else ""

    if level == "easy":
        templates = [
            f"{thinker_prefix}{name}是什么？",
            f"如何理解{thinker_prefix}{name}？",
            f"简要解释{thinker_prefix}{name}的含义",
        ]
    elif level == "medium":
        try:
            subgraph = GB.get_subgraph(name, max_hops=1)
            related = [
                n for n in subgraph.get("nodes", [])
                if n.get("name") != name and n.get("label") == "Concept"
            ]
        except Exception:
            related = []

        if related:
            other = random.choice(related)
            other_name = other.get("name", "")
            other_thinker = other.get("thinker", "")
            templates = [
                f"{thinker_prefix}{name}和{other_thinker}的{other_name}有什么区别？",
                f"比较{thinker_prefix}{name}与{other_name}的关系",
            ]
        else:
            templates = [
                f"{thinker_prefix}{name}如何批判传统观念？",
                f"{thinker_prefix}{name}的局限性在哪里？",
            ]
    else:  # hard
        templates = [
            f"{thinker_prefix}{name}的思想谱系是什么？",
            f"如何用{thinker_prefix}{name}分析当代现象？",
            f"{thinker_prefix}{name}与结构主义批判的关系",
        ]

    return random.choice(templates)


def generate_curriculum_queries(n=3):
    """
    Self-play: generate synthetic queries targeting weak concepts.
    Difficulty adapts to current curriculum level.
    """
    state = _load_state()
    level = state.get("curriculum_level", "easy")

    weak = identify_weak_concepts(top_k=20)
    if not weak:
        weak = _get_random_concepts(20)

    selected = random.sample(weak, min(n, len(weak)))
    queries = []

    for c in selected:
        q = _generate_query_for_concept(c, level)
        queries.append({
            "query": q,
            "target_concept": c.get("name", ""),
            "target_thinker": c.get("thinker", ""),
            "difficulty": level,
            "purpose": "curriculum_reinforcement",
        })

    return queries


KNOWN_THINKERS = [
    "福柯", "鲍德里亚", "拉康", "阿尔都塞", "德里达", "布尔迪厄",
    "哈贝马斯", "本雅明", "阿多诺", "葛兰西", "卢卡奇", "齐泽克",
    "巴特", "列斐伏尔", "波伏瓦", "萨特", "梅洛-庞蒂", "马尔库塞",
    "弗洛姆", "韦伯", "涂尔干", "马克思", "恩格斯", "黑格尔", "康德",
    "尼采", "海德格尔", "胡塞尔", "阿甘本", "朗西埃", "巴迪欧",
    "南希", "斯蒂格勒", "德勒兹", "瓜塔里", "布朗肖", "列维纳斯",
    "萨林斯", "格尔茨", "列维-斯特劳斯",
]


def extract_concepts_from_correction(correction_text, field=None):
    """
    Parse user's correction text to extract concept mentions.
    Heuristic-based (no LLM). Matches:
      - 《book》 → work title
      - [concept] or 「concept」 → concept name
      - known thinker names in text
    """
    import re

    # Extract works: 《...》
    works = re.findall(r'《(.{1,30}?)》', correction_text)

    # Find thinker mentions
    thinkers_found = [t for t in KNOWN_THINKERS if t in correction_text]

    # Extract concept quotes: [...] or 「...」
    concept_quotes = re.findall(r'\[(.{2,20}?)\]|「(.{2,20}?)」', correction_text)
    concepts = [a or b for a, b in concept_quotes]

    extracted = []
    for i, c in enumerate(concepts):
        extracted.append({
            "name": c[:20] if c else "",
            "thinker": thinkers_found[i] if i < len(thinkers_found) else "",
            "work": works[i] if i < len(works) else "",
            "field": field,
            "tier1": f"来自用户纠正记录 ({datetime.now().date()})",
            "tier2": correction_text[:300] if correction_text else "",
            "tier3": "",
        })

    return extracted


def get_learner_report():
    """Generate comprehensive learner report."""
    state = _load_state()
    weak = identify_weak_concepts(top_k=5)

    graph_stats = GB.get_stats()
    mem_stats = MEM.get_stats()

    curriculum_level = state.get("curriculum_level", "easy")

    # Weighted average score over last 20
    scores = state.get("avg_score_history", [0.5])
    avg_score = round(sum(scores) / max(len(scores), 1), 3)

    top_weak_names = [c["name"] for c in weak]
    next_queries = generate_curriculum_queries(3)

    return {
        "curriculum_level": curriculum_level,
        "avg_score_window": avg_score,
        "top_weak_concepts": top_weak_names,
        "graph": graph_stats,
        "memory": mem_stats,
        "next_curriculum_queries": next_queries,
        "difficulty_spectrum": {
            "value": (1.0 if curriculum_level == "hard"
                      else 0.6 if curriculum_level == "medium"
                      else 0.3),
        },
        "dual_states": {
            "total_folds": mem_stats.get("total_sessions", 0),
        },
    }


def get_lean_summary():
    """Lightweight summary for session metadata injection. No LLM cost."""
    try:
        report = get_learner_report()
        return {
            "difficulty_value": report.get("difficulty_spectrum", {}).get("value", 0.5),
            "total_folds": report.get("dual_states", {}).get("total_folds", 0),
            "suspension_rate": 0.0,
            "tension_drift": {},
            "dominant_tension": None,
        }
    except Exception:
        return {
            "difficulty_value": 0.5,
            "total_folds": 0,
            "suspension_rate": 0.0,
        }


# ═══════════════════════════════════════════
# LearningBackend — 标准接口包装类
# ═══════════════════════════════════════════

class LearningBackend:
    """迭代学习标准接口。

    封装反馈处理、课程生成、弱概念识别等学习操作，
    供 orchestrator 统一调用。
    """

    def __init__(self):
        pass

    def process_feedback(self, session_id: str, query: str,
                         response: str, correction: Optional[str] = None,
                         rating: Optional[float] = None) -> dict:
        """处理用户反馈，触发评估和权重更新。"""
        return process_feedback(session_id, query, response, correction, rating)

    def get_lean_summary(self) -> dict:
        """获取学习摘要（零 token 开销元数据）。"""
        return get_lean_summary()

    def get_learner_report(self) -> dict:
        """获取完整学习报告。"""
        return get_learner_report()

    def identify_weak_concepts(self, threshold: float = 0.4) -> List[dict]:
        """识别弱概念（权重低于阈值）。"""
        return identify_weak_concepts(threshold)

    def generate_curriculum_queries(self, count: int = 5) -> List[str]:
        """生成课程查询用于自我对弈训练。"""
        return generate_curriculum_queries(count)

    def extract_concepts_from_correction(self, text: str) -> List[str]:
        """从纠正文中提取概念名。"""
        return extract_concepts_from_correction(text)
