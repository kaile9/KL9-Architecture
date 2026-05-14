"""
kailejiu-soul — KL9-RHIZOME v1.5 灵魂核心

"慢性烫伤"式成长引擎。不替代人格提示词，而是为其提供
动态风格偏好和体验记忆，使 emergent_style 从查表变为共振。

设计原则：
  - 可见成长：对话中可感知的风格演化
  - 慢性烫伤：EMA(0.95) 指数衰减，抵抗污染
  - 零 LLM 开销：纯本地 SQLite 运算
  - 为 emergent 铺路：输出 style_guidance 供 emergent_style 消费
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "kailejiu-shared" / "storage"
DB_PATH = str(STORAGE_DIR / "memory.db")

# ── 反污染常量 ───────────────────────────────────────────────────
EMA_DECAY = 0.95       # 指数移动平均衰减因子 (0.95 = 新数据权重 5%)
MIN_INTERACTIONS = 3    # 至少积累 N 次交互后才开始影响 emergent
MAX_BURST_PER_HOUR = 20  # 每小时最多接受 20 次更新（防轰炸）

# ── 数据结构 ─────────────────────────────────────────────────────

@dataclass
class SoulState:
    """灵魂状态 — 所有字段通过 EMA 缓慢演化。"""
    # 理论亲和度：{thinker_name: float} 越大越倾向引用该思想家
    theory_affinity: Dict[str, float] = field(default_factory=dict)

    # 张力敏感度：{tension_type: float} 越大处理该张力时越自然
    tension_sensitivity: Dict[str, float] = field(default_factory=dict)

    # 风格轮廓：哪些表达模式被历史验证有效
    stylistic_contours: Dict[str, float] = field(default_factory=dict)

    # 元数据
    total_interactions: int = 0
    last_updated: str = ""
    growth_phase: str = "nascent"  # nascent | forming | mature | weathered

    def to_dict(self) -> dict:
        return {
            "theory_affinity": self.theory_affinity,
            "tension_sensitivity": self.tension_sensitivity,
            "stylistic_contours": self.stylistic_contours,
            "total_interactions": self.total_interactions,
            "last_updated": self.last_updated,
            "growth_phase": self.growth_phase,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SoulState":
        return cls(
            theory_affinity=d.get("theory_affinity", {}),
            tension_sensitivity=d.get("tension_sensitivity", {}),
            stylistic_contours=d.get("stylistic_contours", {}),
            total_interactions=d.get("total_interactions", 0),
            last_updated=d.get("last_updated", ""),
            growth_phase=d.get("growth_phase", "nascent"),
        )


# ── 数据库 ───────────────────────────────────────────────────────

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS soul_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            state_json TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS soul_markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            marker_type TEXT,       -- 'theory_used', 'tension_encountered', 'stylistic_choice'
            marker_key TEXT,        -- thinker name / tension type / pattern name
            marker_value REAL,      -- 本次增量
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS soul_visible_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            event_type TEXT,        -- 'growth_milestone', 'style_shift', 'affinity_change'
            description TEXT,
            created_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_soul_markers_type 
            ON soul_markers(marker_type, created_at);
        CREATE INDEX IF NOT EXISTS idx_soul_markers_session 
            ON soul_markers(session_id);
    """)
    conn.commit()


# ── 防轰炸 ───────────────────────────────────────────────────────

def _check_rate_limit() -> bool:
    """检查最近一小时更新次数。超过阈值拒绝更新。"""
    conn = _get_conn()
    try:
        one_hour_ago = datetime.now().replace(microsecond=0).isoformat()
        # 用简单时间戳
        count = conn.execute(
            "SELECT COUNT(*) FROM soul_markers "
            "WHERE created_at > datetime('now', '-1 hour')"
        ).fetchone()[0]
        return count < MAX_BURST_PER_HOUR
    finally:
        conn.close()


# ── 核心操作 ─────────────────────────────────────────────────────

def load_state() -> SoulState:
    """加载当前灵魂状态。"""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT state_json FROM soul_state WHERE id = 1"
        ).fetchone()
        if row:
            return SoulState.from_dict(json.loads(row["state_json"]))
        return SoulState()
    finally:
        conn.close()


def save_state(state: SoulState):
    """持久化灵魂状态。"""
    state.last_updated = datetime.now().isoformat()

    # 更新成长阶段
    if state.total_interactions < 10:
        state.growth_phase = "nascent"
    elif state.total_interactions < 50:
        state.growth_phase = "forming"
    elif state.total_interactions < 200:
        state.growth_phase = "mature"
    else:
        state.growth_phase = "weathered"

    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO soul_state (id, state_json, updated_at) "
            "VALUES (1, ?, ?)",
            (json.dumps(state.to_dict(), ensure_ascii=False), state.last_updated)
        )
        conn.commit()
    finally:
        conn.close()


def ema_update(current: float, new: float) -> float:
    """指数移动平均：新值权重 (1-EMA_DECAY)，旧值权重 EMA_DECAY。"""
    return EMA_DECAY * current + (1 - EMA_DECAY) * new


def ema_dict_update(current: Dict[str, float], key: str, value: float) -> Dict[str, float]:
    """对字典中的单个 key 做 EMA 更新。"""
    result = dict(current)
    if key in result:
        result[key] = ema_update(result[key], value)
    else:
        result[key] = value * (1 - EMA_DECAY)  # 首次出现，给较小初始值
    return result


# ── 公开 API ─────────────────────────────────────────────────────

def record_interaction(
    session_id: str,
    theories_used: List[str],
    tension_type: str,
    stylistic_patterns: List[str],
) -> Optional[Dict]:
    """
    记录一次认知管道交互。在 FoldCompleteEvent 后调用。

    对每个理论/张力/风格模式做微量 EMA 更新。
    如果被限流则静默跳过。

    Returns:
        若有可见变化（里程碑/阶段转换）则返回描述，否则 None。
    """
    if not _check_rate_limit():
        return None

    state = load_state()
    old_phase = state.growth_phase

    now = datetime.now().isoformat()
    conn = _get_conn()
    try:
        # 为每个使用的理论做微量更新
        for thinker in theories_used:
            state.theory_affinity = ema_dict_update(
                state.theory_affinity, thinker, 1.0
            )
            conn.execute(
                "INSERT INTO soul_markers (session_id, marker_type, marker_key, marker_value, created_at) "
                "VALUES (?, 'theory_used', ?, 0.05, ?)",
                (session_id, thinker, now)
            )

        # 张力敏感度
        if tension_type:
            state.tension_sensitivity = ema_dict_update(
                state.tension_sensitivity, tension_type, 1.0
            )
            conn.execute(
                "INSERT INTO soul_markers (session_id, marker_type, marker_key, marker_value, created_at) "
                "VALUES (?, 'tension_encountered', ?, 0.05, ?)",
                (session_id, tension_type, now)
            )

        # 风格模式
        for pattern in stylistic_patterns:
            state.stylistic_contours = ema_dict_update(
                state.stylistic_contours, pattern, 1.0
            )
            conn.execute(
                "INSERT INTO soul_markers (session_id, marker_type, marker_key, marker_value, created_at) "
                "VALUES (?, 'stylistic_choice', ?, 0.03, ?)",
                (session_id, pattern, now)
            )

        state.total_interactions += 1
        conn.commit()
    finally:
        conn.close()

    save_state(state)

    # 检测可见变化
    visible = _detect_visible_changes(state, old_phase, theories_used, tension_type)
    if visible:
        _log_visible_change(session_id, visible)

    return visible


def _detect_visible_changes(
    state: SoulState,
    old_phase: str,
    theories: List[str],
    tension: str,
) -> Optional[Dict]:
    """检测值得在对话中展示的变化。"""
    changes = {}

    # 阶段转换
    if state.growth_phase != old_phase:
        phase_names = {
            "nascent": "初生",
            "forming": "成形",
            "mature": "成熟",
            "weathered": "风化",
        }
        changes["milestone"] = f"灵魂阶段：{phase_names.get(old_phase, old_phase)} → {phase_names.get(state.growth_phase, state.growth_phase)}"

    # 理论亲和度显著变化（某思想家权重首次超过 0.3 或增长超过 0.5）
    for t in theories:
        affinity = state.theory_affinity.get(t, 0)
        if 0.28 < affinity < 0.32:  # 首次突破阈值
            changes.setdefault("affinity_shifts", []).append(f"对{t}的理解加深")

    # 张力敏感度变化
    if tension and state.tension_sensitivity.get(tension, 0) > 0.5:
        if state.total_interactions % 20 == 0:  # 每 20 次交互才提示一次
            changes.setdefault("style_shift", f"对'{tension}'类张力的处理趋于自然")

    return changes if changes else None


def _log_visible_change(session_id: str, changes: Dict):
    """记录可见变化到日志表。"""
    conn = _get_conn()
    try:
        for event_type, description in changes.items():
            if isinstance(description, list):
                for d in description:
                    conn.execute(
                        "INSERT INTO soul_visible_log (session_id, event_type, description, created_at) "
                        "VALUES (?, 'affinity_change', ?, datetime('now'))",
                        (session_id, d)
                    )
            else:
                conn.execute(
                    "INSERT INTO soul_visible_log (session_id, event_type, description, created_at) "
                    "VALUES (?, ?, ?, datetime('now'))",
                    (session_id, event_type, str(description))
                )
        conn.commit()
    finally:
        conn.close()


def get_style_guidance(tension_type: str) -> Dict:
    """
    为 emergent_style 提供风格引导。
    在 Phase 5（emergent_style + Constitutional DNA）前调用。

    Returns:
        {
            "affinities": [("鲍德里亚", 0.72), ...],     # 当前最活跃的理论亲和
            "tension_feel": float,                       # 对该张力的处理自然度
            "stylistic_hints": ["并置而非缝合", ...],     # 当前风格轮廓中的高频模式
            "growth_phase": "forming",                   # 当前成长阶段
        }
    """
    state = load_state()

    # 如果交互次数太少，返回空引导（继续用默认 emergent_style）
    if state.total_interactions < MIN_INTERACTIONS:
        return {"growth_phase": "nascent", "ready": False}

    # Top 3 理论亲和
    affinities = sorted(
        state.theory_affinity.items(), key=lambda x: x[1], reverse=True
    )[:3]

    # 对该张力类型的处理自然度
    tension_feel = state.tension_sensitivity.get(tension_type, 0.3)

    # Top 5 风格模式
    stylistic = sorted(
        state.stylistic_contours.items(), key=lambda x: x[1], reverse=True
    )[:5]
    stylistic_hints = [s[0] for s in stylistic if s[1] > 0.2]

    return {
        "affinities": affinities,
        "tension_feel": round(tension_feel, 2),
        "stylistic_hints": stylistic_hints or ["保持悬置", "拒绝缝合"],
        "growth_phase": state.growth_phase,
        "total_interactions": state.total_interactions,
        "ready": True,
    }


def get_visible_growth_summary() -> List[str]:
    """
    获取最近的可见成长事件，用于对话中展示。
    小开会偶尔（概率 ~5%）在对话开头引用这些事件。
    """
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT description, created_at FROM soul_visible_log "
            "ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        return [r["description"] for r in rows]
    finally:
        conn.close()


def extract_stylistic_patterns(response: str) -> List[str]:
    """
    从生成的响应中提取风格模式标记。
    纯规则引擎，零 LLM 开销。

    检测模式：
      - 并置连接词（"不是X，而是Y"）
      - 否定引介（"X不在于Y，而在于Z"）
      - 悬置标记（"悬而未决""不可调和"）
      - 简短断句（整句不超过 15 字）
      - 引文密度（被引号包裹的短句占比）
    """
    patterns = []

    # 并置结构
    if "不是" in response and "而是" in response:
        patterns.append("否定-并置")

    # 否定引介
    if "不在于" in response or "并非" in response:
        patterns.append("否定引介")

    # 悬置标记
    suspension_words = ["悬置", "不可调和", "张力", "二重", "悖论", "矛盾但"]
    if any(w in response for w in suspension_words):
        patterns.append("悬置保持")

    # 短句节奏（检测是否有连续的短句）
    import re
    sentences = re.split(r'[。！？\n]', response)
    short_count = sum(1 for s in sentences if 0 < len(s.strip()) <= 15)
    if short_count >= 2:
        patterns.append("短句节奏")

    # 引文倾向
    quoted = len(re.findall(r'「[^」]+」|"[^"]+"', response))
    if quoted >= 2:
        patterns.append("引文锚定")

    return patterns


def extract_theories_from_dialogues(activated_dialogue: List[Dict]) -> List[str]:
    """从激活对话中提取理论家名称。"""
    thinkers = []
    for d in activated_dialogue:
        thinker = d.get("thinker", "")
        if thinker and thinker not in thinkers:
            thinkers.append(thinker)
    return thinkers
