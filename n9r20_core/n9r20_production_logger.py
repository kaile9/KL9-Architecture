"""
9R-2.0 RHIZOME · 全记录制作过程
────────────────────────────────────────────────────────
完整记录每次压缩/概念制作的迭代过程。

核心类：
  N9R20IterationLog     — 单次迭代的完整记录
  N9R20ProductionSession — 一次制作会话（可能包含多次迭代）
  N9R20ProductionLogger  — 全局记录器
                            (开始/记录/结束/保存/加载/报告)

设计原则：
  1. 每次迭代的可追溯性 — 谁/何时/做了什么/结果如何
  2. 会话级聚合 — 一次制作 = 多次迭代 + 最终输出
  3. 持久化 — JSON 格式保存，可加载分析
  4. 自然语言报告 — 自动生成可读的制作过程摘要
"""

from __future__ import annotations

import json
import time
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict

from core.n9r20_config import n9r20_compression_config


# ════════════════════════════════════════════════════════════════════
# § 1 · 单次迭代记录
# ════════════════════════════════════════════════════════════════════

@dataclass
class N9R20IterationLog:
    """
    单次迭代的完整记录。

    记录一次压缩折叠迭代中的所有关键信息：
    - 哪个模式（建/破/证/截）
    - 输入/输出变化
    - 压缩率与保留率变化
    - 是否触发验证/中断
    """

    # ── 标识 ──────────────────────────────────────────────
    iteration_index: int = 0               # 迭代序号（从 0 开始）
    session_id: str = ""                   # 所属会话 ID

    # ── 模式 ──────────────────────────────────────────────
    mode: str = ""                         # 当前四模编码模式
    mode_sequence: List[str] = field(default_factory=list)  # 已执行的模式序列

    # ── 输入/输出 ─────────────────────────────────────────
    input_text: str = ""                   # 进入本次迭代的文本
    output_text: str = ""                  # 离开本次迭代的文本
    input_length: int = 0                  # 输入字符数
    output_length: int = 0                 # 输出字符数

    # ── 压缩指标 ─────────────────────────────────────────
    fold_depth: int = 0                    # 当前折叠深度
    compression_ratio: float = 1.0         # 当前压缩率
    semantic_retention: float = 1.0        # 当前语义保留率
    retention_passed: bool = True          # 语义保留是否达标

    # ── 决断 ─────────────────────────────────────────────
    decision_ready: bool = False           # 是否触发决断
    interrupt_reason: str = ""             # 中断原因（如果触发）
    target_reached: bool = False           # 是否达到目标压缩率

    # ── 元信息 ───────────────────────────────────────────
    duration_ms: float = 0.0               # 本次迭代耗时（毫秒）
    timestamp: float = field(default_factory=time.time)
    notes: str = ""                        # 额外备注


# ════════════════════════════════════════════════════════════════════
# § 2 · 制作会话
# ════════════════════════════════════════════════════════════════════

@dataclass
class N9R20ProductionSession:
    """
    一次制作会话的完整记录。

    一次制作会话 = 用户输入 → 路由 → 多次迭代 → 最终输出。
    """

    # ── 标识 ──────────────────────────────────────────────
    session_id: str = ""                   # 会话唯一 ID
    query: str = ""                        # 用户原始查询

    # ── 路由 ──────────────────────────────────────────────
    routing_path: str = "standard"         # 路由路径
    routing_difficulty: float = 0.5        # 路由分配的难度
    routing_urgency: float = 0.5           # 路由分配的紧急度
    target_fold_depth: int = 4             # 目标折叠深度
    target_compression_ratio: float = 2.5  # 目标压缩率

    # ── 迭代记录 ─────────────────────────────────────────
    iterations: List[N9R20IterationLog] = field(default_factory=list)

    # ── 最终结果 ─────────────────────────────────────────
    final_output: str = ""                 # 最终输出
    final_compression_ratio: float = 1.0   # 最终压缩率
    final_semantic_retention: float = 1.0  # 最终语义保留率
    final_fold_depth: int = 0              # 最终折叠深度
    success: bool = False                  # 制作是否成功

    # ── 时间 ─────────────────────────────────────────────
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0
    total_duration_ms: float = 0.0

    # ── 元信息 ───────────────────────────────────────────
    tags: List[str] = field(default_factory=list)   # 标签
    notes: str = ""                                  # 备注

    @property
    def iteration_count(self) -> int:
        """迭代次数。"""
        return len(self.iterations)

    @property
    def mode_summary(self) -> Dict[str, int]:
        """
        各模式的执行次数统计。

        Returns:
            {"construct": N, "deconstruct": N, ...}
        """
        summary: Dict[str, int] = defaultdict(int)
        for it in self.iterations:
            if it.mode:
                summary[it.mode] += 1
        return dict(summary)

    @property
    def retention_trend(self) -> List[float]:
        """
        保留率变化趋势（按迭代顺序）。

        Returns:
            各次迭代的保留率列表
        """
        return [it.semantic_retention for it in self.iterations]

    @property
    def compression_trend(self) -> List[float]:
        """
        压缩率变化趋势（按迭代顺序）。

        Returns:
            各次迭代的压缩率列表
        """
        return [it.compression_ratio for it in self.iterations]

    def add_iteration(self, iteration: N9R20IterationLog) -> None:
        """
        添加一次迭代记录。

        Args:
            iteration: 迭代记录
        """
        iteration.iteration_index = len(self.iterations)
        self.iterations.append(iteration)

    def finalize(
        self,
        final_output: str,
        compression_ratio: float,
        semantic_retention: float,
        fold_depth: int,
        success: bool = False,
    ) -> None:
        """
        终结会话，记录最终结果。

        Args:
            final_output:       最终输出文本
            compression_ratio:  最终压缩率
            semantic_retention: 最终语义保留率
            fold_depth:         最终折叠深度
            success:            是否成功
        """
        self.final_output = final_output
        self.final_compression_ratio = compression_ratio
        self.final_semantic_retention = semantic_retention
        self.final_fold_depth = fold_depth
        self.success = success
        self.ended_at = time.time()
        self.total_duration_ms = (self.ended_at - self.started_at) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典。"""
        return {
            "session_id": self.session_id,
            "query": self.query,
            "routing_path": self.routing_path,
            "routing_difficulty": self.routing_difficulty,
            "routing_urgency": self.routing_urgency,
            "target_fold_depth": self.target_fold_depth,
            "target_compression_ratio": self.target_compression_ratio,
            "iterations": [
                {
                    "iteration_index": it.iteration_index,
                    "mode": it.mode,
                    "mode_sequence": it.mode_sequence,
                    "input_length": it.input_length,
                    "output_length": it.output_length,
                    "fold_depth": it.fold_depth,
                    "compression_ratio": it.compression_ratio,
                    "semantic_retention": it.semantic_retention,
                    "retention_passed": it.retention_passed,
                    "decision_ready": it.decision_ready,
                    "interrupt_reason": it.interrupt_reason,
                    "target_reached": it.target_reached,
                    "duration_ms": it.duration_ms,
                    "timestamp": it.timestamp,
                    "notes": it.notes,
                }
                for it in self.iterations
            ],
            "final_output": self.final_output,
            "final_compression_ratio": self.final_compression_ratio,
            "final_semantic_retention": self.final_semantic_retention,
            "final_fold_depth": self.final_fold_depth,
            "success": self.success,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "total_duration_ms": self.total_duration_ms,
            "tags": self.tags,
            "notes": self.notes,
        }


# ════════════════════════════════════════════════════════════════════
# § 3 · 制作过程记录器
# ════════════════════════════════════════════════════════════════════

class N9R20ProductionLogger:
    """
    制作过程全局记录器。

    职责：
    1. 管理所有制作会话
    2. 提供开始/记录迭代/结束会话的 API
    3. 持久化到 JSON 文件
    4. 生成统计报告与自然语言摘要

    使用示例：
      logger = N9R20ProductionLogger()
      logger.start_session("sess_001", "什么是空性？")
      logger.log_iteration("sess_001", iteration_log)
      logger.end_session("sess_001", output, ratio, retention, depth, True)
      report = logger.generate_report()
    """

    def __init__(self, storage_dir: str = ""):
        """
        初始化记录器。

        Args:
            storage_dir: 日志存储目录，空字符串表示不持久化
        """
        self._sessions: Dict[str, N9R20ProductionSession] = {}
        self._active_session_ids: List[str] = []
        self._storage_dir = storage_dir

    # ── 会话管理 ────────────────────────────────────────────

    def start_session(
        self,
        session_id: str,
        query: str,
        routing_path: str = "standard",
        difficulty: float = 0.5,
        urgency: float = 0.5,
        target_fold_depth: int = 4,
        target_compression_ratio: float = 2.5,
    ) -> N9R20ProductionSession:
        """
        开始一次制作会话。

        Args:
            session_id:              会话唯一 ID
            query:                   用户原始查询
            routing_path:            路由路径
            difficulty:              路由分配的难度
            urgency:                 紧急度
            target_fold_depth:       目标折叠深度
            target_compression_ratio: 目标压缩率

        Returns:
            新创建的制作会话
        """
        session = N9R20ProductionSession(
            session_id=session_id,
            query=query,
            routing_path=routing_path,
            routing_difficulty=difficulty,
            routing_urgency=urgency,
            target_fold_depth=target_fold_depth,
            target_compression_ratio=target_compression_ratio,
        )
        self._sessions[session_id] = session
        self._active_session_ids.append(session_id)
        return session

    def log_iteration(
        self,
        session_id: str,
        iteration: N9R20IterationLog,
    ) -> None:
        """
        记录一次迭代。

        Args:
            session_id: 会话 ID
            iteration:  迭代记录
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"会话 {session_id} 不存在，请先调用 start_session")
        iteration.session_id = session_id
        session.add_iteration(iteration)

    def end_session(
        self,
        session_id: str,
        final_output: str,
        compression_ratio: float,
        semantic_retention: float,
        fold_depth: int,
        success: bool = False,
    ) -> N9R20ProductionSession:
        """
        结束一次制作会话。

        Args:
            session_id:        会话 ID
            final_output:       最终输出
            compression_ratio:  最终压缩率
            semantic_retention: 最终语义保留率
            fold_depth:         最终折叠深度
            success:            是否成功

        Returns:
            已终结的制作会话
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"会话 {session_id} 不存在")
        session.finalize(
            final_output=final_output,
            compression_ratio=compression_ratio,
            semantic_retention=semantic_retention,
            fold_depth=fold_depth,
            success=success,
        )
        if session_id in self._active_session_ids:
            self._active_session_ids.remove(session_id)
        return session

    def get_session(self, session_id: str) -> Optional[N9R20ProductionSession]:
        """获取指定会话。"""
        return self._sessions.get(session_id)

    def get_active_sessions(self) -> List[N9R20ProductionSession]:
        """获取所有活跃（未终结）的会话。"""
        return [
            self._sessions[sid]
            for sid in self._active_session_ids
            if sid in self._sessions
        ]

    # ── 持久化 ──────────────────────────────────────────────

    def save(self, filepath: Optional[str] = None) -> str:
        """
        将所有会话保存为 JSON 文件。

        Args:
            filepath: 保存路径，None 时使用 storage_dir/sessions_TIMESTAMP.json

        Returns:
            实际保存的文件路径
        """
        if filepath is None:
            if not self._storage_dir:
                self._storage_dir = os.getcwd()
            os.makedirs(self._storage_dir, exist_ok=True)
            timestamp = int(time.time())
            filepath = os.path.join(
                self._storage_dir,
                f"production_sessions_{timestamp}.json",
            )

        data = {
            "version": "9R-2.0",
            "saved_at": time.time(),
            "session_count": len(self._sessions),
            "sessions": [
                session.to_dict()
                for session in self._sessions.values()
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def load(self, filepath: str) -> int:
        """
        从 JSON 文件加载会话。

        Args:
            filepath: JSON 文件路径

        Returns:
            加载的会话数量
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for session_data in data.get("sessions", []):
            session = self._dict_to_session(session_data)
            if session:
                self._sessions[session.session_id] = session
                count += 1

        return count

    def _dict_to_session(self, data: Dict[str, Any]) -> Optional[N9R20ProductionSession]:
        """从字典恢复制作会话。"""
        try:
            session = N9R20ProductionSession(
                session_id=data.get("session_id", ""),
                query=data.get("query", ""),
                routing_path=data.get("routing_path", "standard"),
                routing_difficulty=data.get("routing_difficulty", 0.5),
                routing_urgency=data.get("routing_urgency", 0.5),
                target_fold_depth=data.get("target_fold_depth", 4),
                target_compression_ratio=data.get("target_compression_ratio", 2.5),
                final_output=data.get("final_output", ""),
                final_compression_ratio=data.get("final_compression_ratio", 1.0),
                final_semantic_retention=data.get("final_semantic_retention", 1.0),
                final_fold_depth=data.get("final_fold_depth", 0),
                success=data.get("success", False),
                started_at=data.get("started_at", time.time()),
                ended_at=data.get("ended_at", 0.0),
                total_duration_ms=data.get("total_duration_ms", 0.0),
                tags=data.get("tags", []),
                notes=data.get("notes", ""),
            )

            for it_data in data.get("iterations", []):
                iteration = N9R20IterationLog(
                    iteration_index=it_data.get("iteration_index", 0),
                    session_id=session.session_id,
                    mode=it_data.get("mode", ""),
                    mode_sequence=it_data.get("mode_sequence", []),
                    input_length=it_data.get("input_length", 0),
                    output_length=it_data.get("output_length", 0),
                    fold_depth=it_data.get("fold_depth", 0),
                    compression_ratio=it_data.get("compression_ratio", 1.0),
                    semantic_retention=it_data.get("semantic_retention", 1.0),
                    retention_passed=it_data.get("retention_passed", True),
                    decision_ready=it_data.get("decision_ready", False),
                    interrupt_reason=it_data.get("interrupt_reason", ""),
                    target_reached=it_data.get("target_reached", False),
                    duration_ms=it_data.get("duration_ms", 0.0),
                    timestamp=it_data.get("timestamp", time.time()),
                    notes=it_data.get("notes", ""),
                )
                session.iterations.append(iteration)

            return session
        except Exception:
            return None

    # ── 统计报告 ────────────────────────────────────────────

    def generate_report(self) -> Dict[str, Any]:
        """
        生成制作过程统计报告。

        报告包含：
        - 总会话数
        - 成功率
        - 平均迭代次数
        - 平均压缩率与保留率
        - 模式使用分布
        - 路由路径分布

        Returns:
            统计报告字典
        """
        sessions = list(self._sessions.values())
        if not sessions:
            return {"message": "无已记录的制作会话"}

        total = len(sessions)
        success_count = sum(1 for s in sessions if s.success)
        total_iterations = sum(s.iteration_count for s in sessions)

        avg_compression = (
            sum(s.final_compression_ratio for s in sessions) / total
        )
        avg_retention = (
            sum(s.final_semantic_retention for s in sessions) / total
        )
        avg_iterations = total_iterations / total
        avg_duration = (
            sum(s.total_duration_ms for s in sessions) / total
        )

        # 模式分布
        mode_counts: Dict[str, int] = defaultdict(int)
        for s in sessions:
            for mode, count in s.mode_summary.items():
                mode_counts[mode] += count

        # 路由分布
        path_counts: Dict[str, int] = defaultdict(int)
        for s in sessions:
            path_counts[s.routing_path] += 1

        # 难度分布
        difficulty_buckets = {"低 (0-0.33)": 0, "中 (0.33-0.66)": 0, "高 (0.66-1.0)": 0}
        for s in sessions:
            d = s.routing_difficulty
            if d < 0.33:
                difficulty_buckets["低 (0-0.33)"] += 1
            elif d < 0.66:
                difficulty_buckets["中 (0.33-0.66)"] += 1
            else:
                difficulty_buckets["高 (0.66-1.0)"] += 1

        return {
            "total_sessions": total,
            "active_sessions": len(self._active_session_ids),
            "success_count": success_count,
            "success_rate": round(success_count / max(total, 1), 3),
            "total_iterations": total_iterations,
            "avg_iterations_per_session": round(avg_iterations, 1),
            "avg_compression_ratio": round(avg_compression, 2),
            "avg_semantic_retention": round(avg_retention, 2),
            "avg_duration_ms": round(avg_duration, 1),
            "mode_distribution": dict(mode_counts),
            "routing_distribution": dict(path_counts),
            "difficulty_distribution": difficulty_buckets,
        }

    def generate_narrative_report(self) -> str:
        """
        生成自然语言形式的制作过程报告。

        用中文自然语言描述统计结果，便于阅读和理解。

        Returns:
            自然语言报告文本
        """
        stats = self.generate_report()
        if "message" in stats:
            return stats["message"]

        lines = [
            "9R-2.0 RHIZOME · 制作过程报告",
            "=" * 40,
            "",
            f"共完成 {stats['total_sessions']} 次制作会话，"
            f"其中 {stats['success_count']} 次成功，"
            f"成功率 {stats['success_rate'] * 100:.1f}%。",
            "",
            f"平均每次制作经历 {stats['avg_iterations_per_session']} 次迭代，"
            f"平均耗时 {stats['avg_duration_ms']:.0f} 毫秒。",
            "",
            f"平均压缩率: {stats['avg_compression_ratio']:.2f}，"
            f"平均语义保留率: {stats['avg_semantic_retention']:.2f}。",
            "",
            "模式使用分布:",
        ]

        for mode, count in sorted(stats["mode_distribution"].items()):
            lines.append(f"  {mode}: {count} 次")

        lines.append("")
        lines.append("路由路径分布:")
        for path, count in stats["routing_distribution"].items():
            lines.append(f"  {path}: {count} 次")

        lines.append("")
        lines.append("难度分布:")
        for bucket, count in stats["difficulty_distribution"].items():
            lines.append(f"  {bucket}: {count} 次")

        return "\n".join(lines)

    # ── 清理 ────────────────────────────────────────────────

    def clear(self) -> None:
        """清除所有记录。"""
        self._sessions.clear()
        self._active_session_ids.clear()

    @property
    def session_count(self) -> int:
        """已记录的总会话数。"""
        return len(self._sessions)


# 全局单例
n9r20_production_logger = N9R20ProductionLogger()
