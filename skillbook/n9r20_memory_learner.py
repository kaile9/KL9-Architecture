"""
9R-2.0 RHIZOME · Memory-Learner
记忆学习器 · 整合 memory + learner · 技能书传播

设计原则：
1. 从每次压缩会话中学习 — 增量更新
2. 技能书（N9R20SkillBook）跟踪各技能的性能统计
3. 技能书传播：高效技能的参数向低效技能扩散
4. 遗忘曲线：旧经验随时间衰减
5. 去中心化：记忆以 session 为单位，无全局层级

佛教文本只是方便构件，不是思想源流 — 本模块是通用认知架构的记忆层。
"""

import time
import math
import threading
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field

from core.n9r20_structures import N9R20SkillBook, N9R20CompressedOutput, N9R20RoutingDecision
from core.n9r20_tension_bus import (
    N9R20TensionBus, n9r20_bus,
    N9R20CompressionTensionEvent, N9R20CompressionCompleteEvent,
    N9R20SkillBookUpdateEvent, N9R20TensionSubscription
)
from core.n9r20_config import (
    n9r20_memory_config,
    n9r20_compression_config as C_CFG,
    n9r20_routing_config     as R_CFG,
)


# ═══════════════════════════════════════════════════════════
# 辅助数据结构
# ═══════════════════════════════════════════════════════════

@dataclass
class N9R20SessionMemory:
    """
    单次会话的记忆记录

    只保留关键指标，不存储完整内容（去中心化 — 记忆分布存储）。
    """
    session_id: str
    query_preview: str = ""          # query 摘要（前 100 字符）
    compression_ratio: float = 1.0
    semantic_retention: float = 1.0
    fold_depth: int = 0
    difficulty: float = 0.5
    path: str = "standard"
    success: bool = False
    skill_performances: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if len(self.query_preview) > n9r20_memory_config.QUERY_PREVIEW_MAX_CHARS:
            self.query_preview = self.query_preview[:n9r20_memory_config.QUERY_PREVIEW_MAX_CHARS] + "..."


@dataclass
class N9R20SkillProfile:
    """
    技能画像 — 每个技能的学习档案

    跟踪技能在不同条件下的表现。
    """
    skill_name: str
    total_calls: int = 0
    success_count: int = 0
    retention_sum: float = 0.0
    compression_sum: float = 0.0
    difficulty_distribution: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    best_retention: float = 0.0
    worst_retention: float = 1.0
    last_used: float = 0.0

    @property
    def success_rate(self) -> float:
        return self.success_count / max(self.total_calls, 1)

    @property
    def avg_retention(self) -> float:
        return self.retention_sum / max(self.total_calls, 1)

    @property
    def avg_compression(self) -> float:
        return self.compression_sum / max(self.total_calls, 1)


# ═══════════════════════════════════════════════════════════
# 记忆学习器核心
# ═══════════════════════════════════════════════════════════

class N9R20MemoryLearner:
    """
    记忆学习器 · 技能书传播

    核心功能：
    1. 会话记忆管理（环形缓冲区 + 遗忘）
    2. 技能书维护与自动更新
    3. 技能书传播（高效技能 → 低效技能）
    4. 遗忘曲线（指数衰减）
    5. 经验回放（采样历史会话用于学习）

    与 N9R20TensionBus 集成：
    - 订阅 N9R20CompressionCompleteEvent：学习压缩结果
    - 发射 N9R20SkillBookUpdateEvent：当技能书显著更新时
    """

    # ═══ 核心技能列表 ═══
    CORE_SKILLS = [
        "compression-core",
        "dual-reasoner",
        "semantic-graph",
        "memory-learner",
        "adaptive-n9r20_router"
    ]

    def __init__(self, max_memories: int = None, forget_halflife: float = None):
        """
        初始化记忆学习器
        
        参数：
            max_memories: 最大记忆数量（默认从配置读取）
            forget_halflife: 遗忘半衰期秒数（默认从配置读取）
        """
        cfg = n9r20_memory_config
        
        # ═══ 记忆存储 ═══
        self._memories: OrderedDict[str, N9R20SessionMemory] = OrderedDict()
        self._max_memories = max_memories if max_memories is not None else cfg.MAX_MEMORIES
        self._forget_halflife = forget_halflife if forget_halflife is not None else cfg.FORGET_HALFLIFE
        self._forget_constant = math.log(2) / self._forget_halflife

        # ═══ 技能书 ═══
        self._skill_books: Dict[str, N9R20SkillBook] = {}
        self._skill_profiles: Dict[str, N9R20SkillProfile] = {}

        # 初始化核心技能书
        for skill_name in self.CORE_SKILLS:
            self._skill_books[skill_name] = N9R20SkillBook(skill_name=skill_name)
            self._skill_profiles[skill_name] = N9R20SkillProfile(skill_name=skill_name)

        # ═══ 锁 ═══
        self._lock = threading.RLock()

        # ═══ N9R20TensionBus 集成 ═══
        self.n9r20_bus = n9r20_bus
        self.n9r20_bus.subscribe(N9R20TensionSubscription(
            skill_name="memory-learner",
            role="subscriber",
            event_types=["N9R20CompressionCompleteEvent", "N9R20CompressionTensionEvent"],
            priority=1,
            callback=self._on_event
        ))

        # ═══ 传播配置 ═══
        cfg = n9r20_memory_config
        self._propagation_rate: float = cfg.PROPAGATION_RATE
        self._propagation_threshold: float = cfg.PROPAGATION_THRESHOLD

    # ═══════════════════════════════════════════════
    # 公共 API — 记忆管理
    # ═══════════════════════════════════════════════

    def remember(self, session_memory: N9R20SessionMemory) -> None:
        """
        存储会话记忆

        环形缓冲区：超出容量时移除最旧的记忆。
        """
        with self._lock:
            sid = session_memory.session_id

            # 环形缓冲区
            if len(self._memories) >= self._max_memories:
                self._memories.popitem(last=False)  # FIFO

            self._memories[sid] = session_memory

    def recall(self, session_id: str) -> Optional[N9R20SessionMemory]:
        """
        召回特定会话记忆

        自动应用遗忘因子：如果记忆太旧，返回 None。
        """
        with self._lock:
            memory = self._memories.get(session_id)
            if memory is None:
                return None

            # 检查是否已遗忘
            forget_factor = self._compute_forget_factor(memory.timestamp)
            if forget_factor < n9r20_memory_config.FORGET_THRESHOLD:
                # 几乎遗忘，移除
                del self._memories[session_id]
                return None

            return memory

    def forget_old_memories(self) -> int:
        """
        遗忘过期记忆

        返回被遗忘的记忆数量。
        """
        with self._lock:
            now = time.time()
            to_forget: List[str] = []

            for sid, memory in self._memories.items():
                forget_factor = self._compute_forget_factor(memory.timestamp)
                if forget_factor < n9r20_memory_config.FORGET_THRESHOLD:
                    to_forget.append(sid)

            for sid in to_forget:
                del self._memories[sid]

            return len(to_forget)

    def sample_memories(self, n: int = 10, 
                         min_retention: float = 0.0) -> List[N9R20SessionMemory]:
        """
        经验回放：采样历史记忆

        优先采样高保留率（成功）的记忆。
        """
        with self._lock:
            if not self._memories:
                return []

            # 按保留率排序
            sorted_memories = sorted(
                self._memories.values(),
                key=lambda m: m.semantic_retention,
                reverse=True
            )

            # 过滤
            filtered = [m for m in sorted_memories if m.semantic_retention >= min_retention]

            return filtered[:n]

    def recent_memories(self, n: int = 10) -> List[N9R20SessionMemory]:
        """获取最近的 n 条记忆"""
        with self._lock:
            items = list(self._memories.values())
            return items[-n:] if len(items) > n else items

    def memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        with self._lock:
            if not self._memories:
                return {"total": 0}

            retentions = [m.semantic_retention for m in self._memories.values()]
            ratios = [m.compression_ratio for m in self._memories.values()]
            paths = [m.path for m in self._memories.values()]

            return {
                "total": len(self._memories),
                "avg_retention": sum(retentions) / len(retentions),
                "avg_compression_ratio": sum(ratios) / len(ratios),
                "specialized_ratio": paths.count("specialized") / len(paths),
                "standard_ratio": paths.count("standard") / len(paths),
                "success_rate": sum(1 for m in self._memories.values() if m.success) / len(self._memories),
            }

    # ═══════════════════════════════════════════════
    # 公共 API — 技能书管理
    # ═══════════════════════════════════════════════

    def get_skill_book(self, skill_name: str) -> Optional[N9R20SkillBook]:
        """获取技能书"""
        return self._skill_books.get(skill_name)

    def get_all_skill_books(self) -> Dict[str, N9R20SkillBook]:
        """获取所有技能书"""
        return dict(self._skill_books)

    @property
    def skill_books(self) -> Dict[str, N9R20SkillBook]:
        """技能书属性（兼容访问）"""
        return dict(self._skill_books)

    def update_skill_book(self, skill_name: str, 
                           retention: float, 
                           compression_ratio: float,
                           success: bool) -> None:
        """
        更新技能书

        增量更新统计指标。
        """
        with self._lock:
            if skill_name not in self._skill_books:
                self._skill_books[skill_name] = N9R20SkillBook(skill_name=skill_name)
                self._skill_profiles[skill_name] = N9R20SkillProfile(skill_name=skill_name)

            book = self._skill_books[skill_name]
            profile = self._skill_profiles[skill_name]

            # 增量更新
            book.total_calls += 1
            profile.total_calls += 1
            if success:
                profile.success_count += 1

            profile.retention_sum += retention
            profile.compression_sum += compression_ratio
            profile.best_retention = max(profile.best_retention, retention)
            profile.worst_retention = min(profile.worst_retention, retention)
            profile.last_used = time.time()

            # 同步到 N9R20SkillBook
            book.success_rate = profile.success_rate
            book.average_retention = profile.avg_retention
            book.average_compression_ratio = profile.avg_compression
            book.last_updated = time.time()

    def propagate_skill_books(self) -> Dict[str, Dict[str, float]]:
        """
        技能书传播

        高效技能的参数向低效技能扩散：
        1. 计算各技能的性能得分
        2. 识别性能差异超过阈值的技能对
        3. 从高效技能向低效技能传播（提升其参数）

        返回传播映射：{target_skill: {source_skill: influence}}
        """
        with self._lock:
            if len(self._skill_profiles) < 2:
                return {}

            # 计算性能得分（综合保留率和成功率）
            scores: Dict[str, float] = {}
            for name, profile in self._skill_profiles.items():
                if profile.total_calls < n9r20_memory_config.PROPAGATION_MIN_CALLS:
                    continue  # 样本太少，不参与传播
                scores[name] = (
                    profile.avg_retention * n9r20_memory_config.SKILL_SCORE_WEIGHT_RETENTION +
                    profile.success_rate * n9r20_memory_config.SKILL_SCORE_WEIGHT_SUCCESS +
                    profile.avg_compression * n9r20_memory_config.SKILL_SCORE_WEIGHT_COMPRESSION
                )

            if len(scores) < 2:
                return {}

            # 排序
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            best_name, best_score = ranked[0]

            propagation_map: Dict[str, Dict[str, float]] = {}

            for name, score in ranked[1:]:
                diff = best_score - score
                if diff > self._propagation_threshold:
                    # 传播：低效技能吸收高效技能的部分参数
                    influence = min(diff * self._propagation_rate, 0.5)
                    propagation_map[name] = {best_name: round(influence, 3)}

                    # 实际参数调整（模拟）
                    self._apply_skill_influence(name, best_name, influence)

            return propagation_map

    def recommend_skill_order(self, difficulty: float) -> List[Tuple[str, float]]:
        """
        根据历史表现推荐技能调用顺序

        Args:
            difficulty: 任务难度 [0, 1]

        Returns:
            按推荐度降序排列的 (skill_name, score) 列表
        """
        with self._lock:
            recommendations = []

            for name, profile in self._skill_profiles.items():
                if profile.total_calls < n9r20_memory_config.RECOMMEND_MIN_CALLS:
                    # 经验不足，给予中等推荐
                    recommendations.append((name, 0.5))
                    continue

                # 基于历史表现和历史难度匹配度计算得分
                history_score = (
                    profile.avg_retention * n9r20_memory_config.RECOMMEND_WEIGHT_RETENTION +
                    profile.success_rate * n9r20_memory_config.RECOMMEND_WEIGHT_SUCCESS +
                    profile.avg_compression * n9r20_memory_config.RECOMMEND_WEIGHT_COMPRESSION
                )

                # 最近使用惩罚（鼓励探索）
                time_since_last = time.time() - profile.last_used
                recency_factor = min(time_since_last / n9r20_memory_config.RECOMMEND_RECENCY_WINDOW, 1.0) * n9r20_memory_config.RECOMMEND_RECENCY_FACTOR

                score = history_score + recency_factor
                recommendations.append((name, round(score, 3)))

            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations

    def get_skill_diagnostics(self) -> Dict[str, Any]:
        """获取技能诊断报告"""
        with self._lock:
            diagnostics = {}
            for name, profile in self._skill_profiles.items():
                diagnostics[name] = {
                    "total_calls": profile.total_calls,
                    "success_rate": round(profile.success_rate, 3),
                    "avg_retention": round(profile.avg_retention, 3),
                    "avg_compression": round(profile.avg_compression, 3),
                    "best_retention": round(profile.best_retention, 3),
                    "worst_retention": round(profile.worst_retention, 3),
                    "last_used_ago": round(time.time() - profile.last_used, 1),
                }
            return diagnostics

    # ═══════════════════════════════════════════════
    # 内部方法
    # ═══════════════════════════════════════════════

    def _compute_forget_factor(self, timestamp: float) -> float:
        """
        计算遗忘因子

        指数衰减：e^(-λ·Δt)
        """
        dt = time.time() - timestamp
        if dt < 0:
            return 1.0
        return math.exp(-self._forget_constant * dt)

    def _apply_skill_influence(self, target: str, source: str, 
                                 influence: float) -> None:
        """
        应用技能影响（参数传播）

        将 source 技能的有效参数传递到 target 技能。
        这是技能书传播的核心机制。
        """
        source_book = self._skill_books.get(source)
        target_book = self._skill_books.get(target)
        if not source_book or not target_book:
            return

        # 目标技能的指标向源技能靠拢
        # 使用指数移动平均 (EMA)
        alpha = influence
        target_book.average_retention = (
            (1 - alpha) * target_book.average_retention +
            alpha * source_book.average_retention
        )
        target_book.average_compression_ratio = (
            (1 - alpha) * target_book.average_compression_ratio +
            alpha * source_book.average_compression_ratio
        )
        target_book.success_rate = (
            (1 - alpha * 0.5) * target_book.success_rate +
            alpha * 0.5 * source_book.success_rate
        )
        target_book.last_updated = time.time()

    def _learn_from_session(self, session_id: str,
                             output: N9R20CompressedOutput,
                             routing: Optional[N9R20RoutingDecision] = None) -> None:
        """
        从单个会话中学习

        提取经验并更新各技能书。
        """
        # 创建会话记忆
        memory = N9R20SessionMemory(
            session_id=session_id,
            query_preview=output.output[:n9r20_memory_config.QUERY_PREVIEW_MAX_CHARS],
            compression_ratio=output.compression_ratio,
            semantic_retention=output.semantic_retention,
            fold_depth=output.fold_depth,
            difficulty=routing.difficulty if routing else 0.5,
            path=routing.path if routing else "standard",
            success=output.semantic_retention >= C_CFG.SEMANTIC_RETENTION_THRESHOLD,
            skill_performances={
                "compression-core": output.semantic_retention,
                "dual-reasoner": output.semantic_retention * 0.9,   # 次级技能略低
                "semantic-graph": output.semantic_retention * C_CFG.SEMANTIC_RETENTION_THRESHOLD,
                "adaptive-n9r20_router": output.semantic_retention * 0.95,
            }
        )
        self.remember(memory)

        # 更新各技能书
        success = output.semantic_retention >= C_CFG.SEMANTIC_RETENTION_THRESHOLD
        for skill_name in self.CORE_SKILLS:
            perf = memory.skill_performances.get(skill_name, output.semantic_retention)
            self.update_skill_book(
                skill_name=skill_name,
                retention=perf,
                compression_ratio=output.compression_ratio,
                success=success
            )

        # 定期传播（每 N 个会话）
        trigger_interval = n9r20_memory_config.PROPAGATION_PERIOD
        if self._skill_books["compression-core"].total_calls % trigger_interval == 0:
            propagation = self.propagate_skill_books()
            if propagation:
                for target, sources in propagation.items():
                    for source, influence in sources.items():
                        self.n9r20_bus.emit(N9R20SkillBookUpdateEvent(
                            session_id=session_id,
                            skill_name=target,
                            book=self._skill_books.get(target)
                        ))

        # 定期遗忘（每 N 个会话）
        forget_interval = n9r20_memory_config.FORGET_PERIOD
        if self._skill_books["compression-core"].total_calls % forget_interval == 0:
            self.forget_old_memories()

    # ═══════════════════════════════════════════════
    # N9R20TensionBus 事件处理
    # ═══════════════════════════════════════════════

    def _on_event(self, event: Any) -> None:
        """统一事件处理入口"""
        if isinstance(event, N9R20CompressionCompleteEvent):
            self._handle_compression_complete(event)
        elif isinstance(event, N9R20CompressionTensionEvent):
            self._handle_compression_tension(event)

    def _handle_compression_complete(self, event: N9R20CompressionCompleteEvent) -> None:
        """
        处理压缩完成事件

        主要学习入口：从压缩结果中学习。
        """
        state = event.state  # N9R20DualState
        output = event.output

        # 构建路由决策（从 state 中提取）
        routing = None
        if state:
            routing = N9R20RoutingDecision(
                path="specialized" if getattr(state, 'current_mode', '') else "standard",
                difficulty=getattr(state, 'tension', None) and state.tension.intensity or 0.5,
                target_fold_depth=getattr(state, 'target_fold_depth', R_CFG.FOLD_DEPTH_DEFAULT),
                target_compression_ratio=getattr(state, 'target_compression_ratio', R_CFG.COMPRESSION_RATIO_DEFAULT),
                compression_ratio=event.compression_ratio,
                semantic_retention=event.semantic_retention,
            )

        self._learn_from_session(
            session_id=event.session_id,
            output=N9R20CompressedOutput(
                output=event.output,
                compression_ratio=event.compression_ratio,
                semantic_retention=event.semantic_retention,
                fold_depth=getattr(state, 'fold_depth', 0) if state else 0,
                session_id=event.session_id,
            ),
            routing=routing
        )

    def _handle_compression_tension(self, event: N9R20CompressionTensionEvent) -> None:
        """
        处理压缩张力事件

        预处理：记录 query 特征，为后续学习做准备。
        """
        # 更新 adaptive-n9r20_router 的调用次数
        if "adaptive-n9r20_router" in self._skill_profiles:
            self._skill_profiles["adaptive-n9r20_router"].total_calls += 1
            self._skill_profiles["adaptive-n9r20_router"].last_used = time.time()


# 全局单例
n9r20_memory_learner = N9R20MemoryLearner()
