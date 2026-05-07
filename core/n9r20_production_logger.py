"""
9R-2.0 RHIZOME · Production Logger
──────────────────────────────────
生产日志系统 — 记录完整压缩管线中的每次迭代与整体会话。

设计原则：
    1. 单次迭代记录（N9R20IterationLog）捕获每一步的微观状态
    2. 完整会话记录（N9R20ProductionSession）聚合所有迭代 + 元数据
    3. 生产日志器（N9R20ProductionLogger）提供 start/log/end/save/load/report
    4. 类 SQLite 风格的持久化（JSON 文件），支持惰性写入
    5. 与 N9R20TensionBus 集成，自动监听压缩事件

使用示例：
    >>> logger = N9R20ProductionLogger()
    >>> session = logger.start(query="量子纠缠与缘起性空", session_id="s1")
    >>> logger.log(session.session_id, mode="construct", fold_depth=1, ratio=1.5)
    >>> logger.log(session.session_id, mode="deconstruct", fold_depth=2, ratio=2.0)
    >>> output = logger.end(session.session_id, compressed_output="压缩结果...")
    >>> report = logger.report(session.session_id)
    >>> logger.save("production_logs.json")
"""

from __future__ import annotations

import json
import os
import time
import uuid
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.n9r20_structures import N9R20CompressedOutput
from core.n9r20_tension_bus import (
    N9R20TensionBus,
    n9r20_bus,
    N9R20CompressionTensionEvent,
    N9R20CompressionCompleteEvent,
)


# ════════════════════════════════════════════════════════════════════
# § 1 · N9R20IterationLog — 单次迭代记录
# ════════════════════════════════════════════════════════════════════


@dataclass
class N9R20IterationLog:
    """
    单次压缩迭代的微观记录。

    捕获四模编码中每一步的状态快照，包括：
    - 当前模式（construct / deconstruct / validate / interrupt）
    - fold 深度与压缩率
    - 语义保留率估算
    - 时间戳
    - 任意扩展字段
    """

    iteration_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    """迭代唯一标识"""

    mode: str = ""
    """当前模式: 'construct' | 'deconstruct' | 'validate' | 'interrupt'"""

    fold_depth: int = 0
    """当前 fold 深度"""

    compression_ratio: float = 1.0
    """当前压缩率"""

    semantic_retention: float = 1.0
    """估算语义保留率 [0, 1]"""

    output_preview: str = ""
    """压缩输出预览（前 80 字符）"""

    duration_ms: float = 0.0
    """本迭代耗时（毫秒）"""

    timestamp: float = field(default_factory=time.time)
    """Unix 时间戳"""

    extras: Dict[str, Any] = field(default_factory=dict)
    """扩展字段（任意键值对）"""

    def __post_init__(self) -> None:
        if len(self.output_preview) > 80:
            self.output_preview = self.output_preview[:80] + "..."

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典。"""
        return {
            "iteration_id": self.iteration_id,
            "mode": self.mode,
            "fold_depth": self.fold_depth,
            "compression_ratio": self.compression_ratio,
            "semantic_retention": self.semantic_retention,
            "output_preview": self.output_preview,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "extras": self.extras,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "N9R20IterationLog":
        """从字典反序列化。"""
        return cls(
            iteration_id=data.get("iteration_id", uuid.uuid4().hex[:8]),
            mode=data.get("mode", ""),
            fold_depth=data.get("fold_depth", 0),
            compression_ratio=data.get("compression_ratio", 1.0),
            semantic_retention=data.get("semantic_retention", 1.0),
            output_preview=data.get("output_preview", ""),
            duration_ms=data.get("duration_ms", 0.0),
            timestamp=data.get("timestamp", time.time()),
            extras=data.get("extras", {}),
        )


# ════════════════════════════════════════════════════════════════════
# § 2 · N9R20ProductionSession — 完整会话记录
# ════════════════════════════════════════════════════════════════════


@dataclass
class N9R20ProductionSession:
    """
    一次完整生产会话的聚合记录。

    包含：
    - 输入查询与路由决策
    - 所有迭代记录列表
    - 最终压缩输出
    - 聚合统计指标（总耗时、平均保留率、成功判定等）
    """

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    """会话唯一标识"""

    query: str = ""
    """原始查询"""

    query_length: int = 0
    """查询字符数"""

    # ── 路由决策 ──
    path: str = "standard"
    """路由路径: 'specialized' | 'standard'"""

    target_fold_depth: int = 4
    """目标 fold 深度"""

    target_compression_ratio: float = 2.5
    """目标压缩率"""

    difficulty: float = 0.5
    """任务难度 [0, 1]"""

    urgency: float = 0.5
    """紧急度 [0, 1]"""

    # ── 迭代记录 ──
    iterations: List[N9R20IterationLog] = field(default_factory=list)
    """所有迭代记录（按时间排序）"""

    # ── 最终输出 ──
    compressed_output: str = ""
    """最终压缩输出"""

    final_compression_ratio: float = 1.0
    """最终压缩率"""

    final_semantic_retention: float = 1.0
    """最终语义保留率"""

    actual_fold_depth: int = 0
    """实际 fold 深度"""

    mode_sequence: List[str] = field(default_factory=list)
    """模式序列"""

    decision_ready: bool = False
    """是否已决断"""

    # ── 聚合统计 ──
    total_duration_ms: float = 0.0
    """总耗时（毫秒）"""

    iteration_count: int = 0
    """总迭代次数"""

    avg_retention: float = 1.0
    """平均语义保留率"""

    success: bool = False
    """本次生产是否成功"""

    # ── 时间戳 ──
    started_at: float = field(default_factory=time.time)
    """开始时间"""

    ended_at: float = 0.0
    """结束时间（0 表示未结束）"""

    # ── 元数据 ──
    tags: List[str] = field(default_factory=list)
    """标签"""

    notes: str = ""
    """备注"""

    def __post_init__(self) -> None:
        if self.query and not self.query_length:
            self.query_length = len(self.query)

    @property
    def is_ended(self) -> bool:
        """会话是否已结束。"""
        return self.ended_at > 0.0

    @property
    def duration_seconds(self) -> float:
        """会话耗时（秒）。"""
        end = self.ended_at if self.ended_at > 0 else time.time()
        return end - self.started_at

    def add_iteration(self, log: N9R20IterationLog) -> None:
        """
        添加一次迭代记录并更新聚合统计。

        参数：
            log: 迭代记录
        """
        self.iterations.append(log)
        self.iteration_count = len(self.iterations)
        self.total_duration_ms += log.duration_ms
        # 更新平均保留率
        if self.iteration_count > 0:
            retentions = [it.semantic_retention for it in self.iterations]
            self.avg_retention = sum(retentions) / len(retentions)

    def finalize(
        self,
        output: N9R20CompressedOutput,
        success: bool = True,
    ) -> None:
        """
        从 N9R20CompressedOutput 填充最终输出字段。

        参数：
            output: 压缩输出
            success: 是否成功
        """
        self.compressed_output = output.output
        self.final_compression_ratio = output.compression_ratio
        self.final_semantic_retention = output.semantic_retention
        self.actual_fold_depth = output.fold_depth
        self.mode_sequence = list(output.mode_sequence)
        self.decision_ready = output.decision_ready
        self.success = success
        self.ended_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（完整）。"""
        return {
            "session_id": self.session_id,
            "query": self.query,
            "query_length": self.query_length,
            "path": self.path,
            "target_fold_depth": self.target_fold_depth,
            "target_compression_ratio": self.target_compression_ratio,
            "difficulty": self.difficulty,
            "urgency": self.urgency,
            "iterations": [it.to_dict() for it in self.iterations],
            "compressed_output": self.compressed_output,
            "final_compression_ratio": self.final_compression_ratio,
            "final_semantic_retention": self.final_semantic_retention,
            "actual_fold_depth": self.actual_fold_depth,
            "mode_sequence": self.mode_sequence,
            "decision_ready": self.decision_ready,
            "total_duration_ms": self.total_duration_ms,
            "iteration_count": self.iteration_count,
            "avg_retention": self.avg_retention,
            "success": self.success,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "tags": self.tags,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "N9R20ProductionSession":
        """从字典反序列化。"""
        session = cls(
            session_id=data.get("session_id", uuid.uuid4().hex[:12]),
            query=data.get("query", ""),
            query_length=data.get("query_length", 0),
            path=data.get("path", "standard"),
            target_fold_depth=data.get("target_fold_depth", 4),
            target_compression_ratio=data.get("target_compression_ratio", 2.5),
            difficulty=data.get("difficulty", 0.5),
            urgency=data.get("urgency", 0.5),
            compressed_output=data.get("compressed_output", ""),
            final_compression_ratio=data.get("final_compression_ratio", 1.0),
            final_semantic_retention=data.get("final_semantic_retention", 1.0),
            actual_fold_depth=data.get("actual_fold_depth", 0),
            mode_sequence=data.get("mode_sequence", []),
            decision_ready=data.get("decision_ready", False),
            total_duration_ms=data.get("total_duration_ms", 0.0),
            iteration_count=data.get("iteration_count", 0),
            avg_retention=data.get("avg_retention", 1.0),
            success=data.get("success", False),
            started_at=data.get("started_at", time.time()),
            ended_at=data.get("ended_at", 0.0),
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
        )
        # 恢复迭代记录
        session.iterations = [
            N9R20IterationLog.from_dict(it)
            for it in data.get("iterations", [])
        ]
        return session


# ════════════════════════════════════════════════════════════════════
# § 3 · N9R20ProductionLogger — 生产日志系统
# ════════════════════════════════════════════════════════════════════


class N9R20ProductionLogger:
    """
    生产日志记录器。

    核心功能：
    - start(): 开始新生产会话
    - log():   记录一次迭代
    - end():   结束会话并记录最终输出
    - save():  持久化到 JSON 文件
    - load():  从 JSON 文件加载所有会话
    - report(): 生成自然语言会话报告

    与 N9R20TensionBus 集成：
    - 自动监听 N9R20CompressionCompleteEvent，在压缩完成时自动记录

    线程安全：使用 RLock 保护内部数据结构。

    属性：
        sessions: 所有会话记录（session_id → N9R20ProductionSession）
        total_sessions: 历史总会话数
        total_success: 历史成功会话数
        success_rate: 历史成功率
    """

    def __init__(self, auto_subscribe: bool = True):
        """
        初始化生产日志器。

        参数：
            auto_subscribe: 是否自动订阅 N9R20TensionBus 事件
        """
        self._sessions: Dict[str, N9R20ProductionSession] = {}
        self._lock = threading.RLock()
        self._auto_subscribe = auto_subscribe

        if auto_subscribe:
            self._subscribe_to_bus()

    # ── 属性 ──────────────────────────────────────────────────

    @property
    def sessions(self) -> Dict[str, N9R20ProductionSession]:
        """返回所有会话记录的浅拷贝。"""
        with self._lock:
            return dict(self._sessions)

    @property
    def total_sessions(self) -> int:
        """历史总会话数。"""
        with self._lock:
            return len(self._sessions)

    @property
    def total_success(self) -> int:
        """历史成功会话数。"""
        with self._lock:
            return sum(1 for s in self._sessions.values() if s.success)

    @property
    def success_rate(self) -> float:
        """历史成功率 [0, 1]。"""
        with self._lock:
            total = len(self._sessions)
            if total == 0:
                return 0.0
            return self.total_success / total

    # ── 公共 API ──────────────────────────────────────────────

    def start(
        self,
        query: str,
        session_id: str = "",
        path: str = "standard",
        target_fold_depth: int = 4,
        target_compression_ratio: float = 2.5,
        difficulty: float = 0.5,
        urgency: float = 0.5,
        **kwargs: Any,
    ) -> N9R20ProductionSession:
        """
        开始一次新的生产会话。

        参数：
            query: 原始查询文本
            session_id: 会话 ID（空则自动生成）
            path: 路由路径
            target_fold_depth: 目标 fold 深度
            target_compression_ratio: 目标压缩率
            difficulty: 预估难度
            urgency: 紧急度
            **kwargs: 其他字段将存入 session 的 notes

        返回：
            新创建的 N9R20ProductionSession
        """
        sid = session_id or uuid.uuid4().hex[:12]

        session = N9R20ProductionSession(
            session_id=sid,
            query=query,
            query_length=len(query),
            path=path,
            target_fold_depth=target_fold_depth,
            target_compression_ratio=target_compression_ratio,
            difficulty=difficulty,
            urgency=urgency,
            started_at=time.time(),
            tags=kwargs.pop("tags", []),
            notes=kwargs.pop("notes", ""),
        )

        with self._lock:
            self._sessions[sid] = session

        return session

    def log(
        self,
        session_id: str,
        mode: str = "",
        fold_depth: int = 0,
        compression_ratio: float = 1.0,
        semantic_retention: float = 1.0,
        output_preview: str = "",
        duration_ms: float = 0.0,
        **extras: Any,
    ) -> Optional[N9R20IterationLog]:
        """
        记录一次压缩迭代。

        参数：
            session_id: 所属会话 ID
            mode: 当前模式
            fold_depth: 当前 fold 深度
            compression_ratio: 当前压缩率
            semantic_retention: 当前语义保留率
            output_preview: 输出预览
            duration_ms: 迭代耗时（毫秒）
            **extras: 扩展字段

        返回：
            新创建的 N9R20IterationLog，或 None（会话不存在）
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            iteration = N9R20IterationLog(
                mode=mode,
                fold_depth=fold_depth,
                compression_ratio=compression_ratio,
                semantic_retention=semantic_retention,
                output_preview=output_preview,
                duration_ms=duration_ms,
                extras=dict(extras),
            )
            session.add_iteration(iteration)
            return iteration

    def end(
        self,
        session_id: str,
        output: Optional[N9R20CompressedOutput] = None,
        success: bool = True,
    ) -> Optional[N9R20ProductionSession]:
        """
        结束一次生产会话。

        参数：
            session_id: 会话 ID
            output: 压缩输出（可选，提供则会自动填充 finalize）
            success: 是否标记为成功

        返回：
            已结束的 N9R20ProductionSession，或 None（会话不存在）
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            if output is not None:
                session.finalize(output, success=success)
            else:
                session.success = success
                session.ended_at = time.time()

            return session

    def get(self, session_id: str) -> Optional[N9R20ProductionSession]:
        """
        获取指定会话记录。

        参数：
            session_id: 会话 ID

        返回：
            N9R20ProductionSession 或 None
        """
        with self._lock:
            return self._sessions.get(session_id)

    def report(self, session_id: str) -> str:
        """
        生成自然语言会话报告。

        参数：
            session_id: 会话 ID

        返回：
            自然语言报告字符串
        """
        session = self.get(session_id)
        if session is None:
            return f"[ProductionLogger] 会话 '{session_id}' 不存在。"

        lines: List[str] = [
            "=" * 60,
            f"  生产报告 · 会话 {session.session_id}",
            "=" * 60,
            "",
            f"  查询:       {session.query[:80]}{'...' if len(session.query) > 80 else ''}",
            f"  路径:       {session.path}",
            f"  难度:       {session.difficulty}",
            f"  紧急度:     {session.urgency}",
            f"  目标 fold:  {session.target_fold_depth}",
            f"  目标压缩率: {session.target_compression_ratio}",
            "",
            f"  迭代次数:   {session.iteration_count}",
            f"  实际 fold:  {session.actual_fold_depth}",
            f"  实际压缩率: {session.final_compression_ratio}",
            f"  平均保留率: {session.avg_retention:.2%}",
            f"  总耗时:     {session.duration_seconds:.3f}s",
            f"  成功:       {'✓' if session.success else '✗'}",
            "",
            "  模式序列:",
        ]

        if session.mode_sequence:
            lines.append(f"    {' → '.join(session.mode_sequence)}")
        else:
            lines.append("    (无)")

        if session.iterations:
            lines.append("")
            lines.append("  迭代详情:")
            lines.append(f"    {'ID':<10} {'模式':<14} {'Fold':<6} {'压缩率':<8} {'保留率':<8}")
            lines.append(f"    {'-'*10} {'-'*14} {'-'*6} {'-'*8} {'-'*8}")
            for it in session.iterations:
                lines.append(
                    f"    {it.iteration_id:<10} {it.mode:<14} {it.fold_depth:<6} "
                    f"{it.compression_ratio:<8.2f} {it.semantic_retention:<8.2%}"
                )

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def save(self, filepath: str) -> int:
        """
        将所有会话持久化到 JSON 文件。

        参数：
            filepath: JSON 文件路径

        返回：
            写入的会话数量
        """
        with self._lock:
            data: Dict[str, Any] = {
                "version": "9R-2.0",
                "total_sessions": len(self._sessions),
                "sessions": [
                    session.to_dict() for session in self._sessions.values()
                ],
            }
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return len(self._sessions)

    def load(self, filepath: str, merge: bool = True) -> int:
        """
        从 JSON 文件加载会话。

        参数：
            filepath: JSON 文件路径
            merge: True → 合并到现有会话；False → 替换所有会话

        返回：
            加载的会话数量
        """
        if not os.path.exists(filepath):
            return 0

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        loaded_sessions: Dict[str, N9R20ProductionSession] = {}
        for raw in data.get("sessions", []):
            session = N9R20ProductionSession.from_dict(raw)
            loaded_sessions[session.session_id] = session

        with self._lock:
            if merge:
                self._sessions.update(loaded_sessions)
            else:
                self._sessions = loaded_sessions

        return len(loaded_sessions)

    def list_sessions(
        self,
        success_only: bool = False,
        limit: int = 20,
    ) -> List[N9R20ProductionSession]:
        """
        列出会话（按开始时间降序）。

        参数：
            success_only: 仅列出成功会话
            limit: 最大返回数量

        返回：
            会话列表
        """
        with self._lock:
            sessions = sorted(
                self._sessions.values(),
                key=lambda s: s.started_at,
                reverse=True,
            )
            if success_only:
                sessions = [s for s in sessions if s.success]
            return sessions[:limit]

    def clear(self) -> int:
        """
        清空所有会话记录。

        返回：
            清除的会话数量
        """
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            return count

    # ── N9R20TensionBus 集成 ──────────────────────────────────

    def _subscribe_to_bus(self) -> None:
        """订阅 N9R20TensionBus 的压缩事件。"""
        try:
            n9r20_bus.on("N9R20CompressionCompleteEvent", self._on_compression_complete)
        except Exception:
            pass  # 静默失败 — TensionBus 可能在测试环境中不可用

    def _on_compression_complete(self, event: Any) -> None:
        """
        处理 N9R20CompressionCompleteEvent。

        自动记录压缩完成事件到对应会话。
        """
        session_id = getattr(event, "session_id", "")
        if not session_id:
            return

        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                # 自动创建一个新会话（如果已有 TensionBus 事件但无会话）
                return

            # 从事件中提取 N9R20CompressedOutput
            output = N9R20CompressedOutput(
                output=getattr(event, "output", ""),
                compression_ratio=getattr(event, "compression_ratio", 1.0),
                semantic_retention=getattr(event, "semantic_retention", 1.0),
                session_id=session_id,
            )
            # 如果 N9R20DualState 在事件中，提取更多信息
            state = getattr(event, "state", None)
            if state is not None:
                output.fold_depth = getattr(state, "fold_depth", 0)
                output.mode_sequence = getattr(state, "mode_sequence", [])
                output.decision_ready = getattr(state, "decision_ready", False)

            session.finalize(output, success=True)


# ════════════════════════════════════════════════════════════════════
# § 4 · 全局单例
# ════════════════════════════════════════════════════════════════════

#: 全局生产日志记录器单例
n9r20_production_logger: N9R20ProductionLogger = N9R20ProductionLogger()


__all__ = [
    "N9R20IterationLog",
    "N9R20ProductionSession",
    "N9R20ProductionLogger",
    "n9r20_production_logger",
]
