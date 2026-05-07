#!/usr/bin/env python3
"""
KL9 Agent · 交互式 REPL
======================
一行 `python quickstart.py` 启动，进入 KL9> 对话模式。

完整 9R-2.0 认知流程：
  DualState → Router → TensionBus → DualReasoner → CompressionCore
  → LLMEvaluator → LLMCompressor → 输出 → MemoryLearner 保存

内置命令：
  status  — 查看当前会话状态
  clear   — 清空当前会话上下文
  help    — 显示帮助
  quit    — 退出
"""

from __future__ import annotations

import sys
import os
import uuid
import time
import json
import readline
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# ════════════════════════════════════════════════════════════════════
# § 0 · 路径设置
# ════════════════════════════════════════════════════════════════════

script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# ════════════════════════════════════════════════════════════════════
# § 1 · Mock 基础设施（核心模块导入失败时的 fallback）
# ════════════════════════════════════════════════════════════════════

_import_warnings: List[str] = []

# ── 为 broken core 模块做类型补丁 ─────────────────────────
# compression_core.py 引用了 typing.List 但未导入；
# adaptive_router.py / compression_core.py 引用了 FoldDepth 但 structures.py 未定义。
# 在导入前临时注入这些缺失的符号。

try:
    import core.n9r20_structures as _structs_mod
    if not hasattr(_structs_mod, "FoldDepth"):
        from enum import Enum

        class _FoldDepth(Enum):
            QUICK = "quick"
            STANDARD = "standard"
            DEEP = "deep"
            DEGRADED = "degraded"

        _structs_mod.FoldDepth = _FoldDepth
except Exception as _e:
    pass  # 后续会由 _safe_import 捕获


def _safe_import(module_path: str, names: List[str], mock_factory=None):
    """尝试导入模块中的类，失败时创建 mock 并记录警告。"""
    try:
        mod = __import__(module_path, fromlist=names)
        results = []
        for n in names:
            obj = getattr(mod, n, None)
            if obj is None:
                raise ImportError(f"{module_path} 缺少 {n}")
            results.append(obj)
        return results[0] if len(results) == 1 else results
    except Exception as e:
        _import_warnings.append(f"⚠  {module_path}.{names[0]} 导入失败: {e}")
        if mock_factory:
            return mock_factory()
        return None


# ── Mock 类工厂 ──────────────────────────────────────────

class _MockPerspectiveType:
    THEORETICAL = "theoretical"
    EMBODIED = "embodied"
    PRACTICAL = "practical"
    CRITICAL = "critical"


class _MockFoldDepth:
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    DEGRADED = "degraded"


@dataclass
class _MockPerspective:
    name: str = ""
    characteristics: List[str] = field(default_factory=list)
    key: str = ""
    perspective_type: Any = _MockPerspectiveType.THEORETICAL

    def __post_init__(self):
        if not self.key:
            self.key = self.name


@dataclass
class _MockTension:
    perspective_A: str = ""
    perspective_B: str = ""
    claim_A: str = ""
    claim_B: str = ""
    irreconcilable_points: List[str] = field(default_factory=list)
    tension_type: str = ""
    intensity: float = 0.5


@dataclass
class _MockDualState:
    query: str = ""
    session_id: str = ""
    perspective_A: Optional[Any] = None
    perspective_B: Optional[Any] = None
    tension: Optional[Any] = None
    fold_depth: int = 0
    target_fold_depth: int = 4
    compression_ratio: float = 1.0
    target_compression_ratio: float = 2.5
    semantic_retention: float = 1.0
    current_mode: str = ""
    mode_sequence: List[str] = field(default_factory=list)
    decision_ready: bool = False
    compressed_output: str = ""
    source_skill: str = "compression-core"
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class _MockRoutingDecision:
    path: str = "standard"
    confidence: float = 0.0
    difficulty: float = 0.5
    target_fold_depth: int = 4
    target_compression_ratio: float = 2.5
    urgency: float = 0.5
    concept_density: float = 0.0
    tension_factor: float = 0.0
    length_factor: float = 0.0


@dataclass
class _MockCompressedOutput:
    output: str = ""
    compression_ratio: float = 1.0
    semantic_retention: float = 1.0
    fold_depth: int = 0
    mode_sequence: List[str] = field(default_factory=list)
    decision_ready: bool = False
    session_id: str = ""
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class _MockSkillBook:
    def __init__(self):
        self.skill_name = ""
        self.total_calls = 0
        self.success_rate = 0.0
        self.average_retention = 0.0
        self.average_compression_ratio = 0.0
        self.last_updated = time.time()


class _MockTensionBus:
    """Mock 事件总线：记录事件，支持简单的订阅/发射。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._events: List[Any] = []
        self._handlers: Dict[str, List[Any]] = {}
        self._subscriptions: Dict[str, List[Any]] = {}

    def emit(self, event):
        self._events.append(event)
        et = type(event).__name__
        for h in self._handlers.get(et, []):
            try:
                h(event)
            except Exception:
                pass

    def on(self, event_type, handler):
        self._handlers.setdefault(event_type, []).append(handler)

    def subscribe(self, sub):
        pass

    def collect(self, event_types, session_id, timeout=5.0):
        return {}

    def clear_session(self, session_id):
        self._events = [e for e in self._events if getattr(e, "session_id", "") != session_id]

    def route_by_urgency(self, event):
        return ["compression-core", "dual-reasoner"]

    def fallback_route(self, query):
        return "standard-compression"


class _MockQueryEvent:
    def __init__(self, query="", session_id=""):
        self.query = query
        self.session_id = session_id
        self.timestamp = time.time()


class _MockCompressionCompleteEvent:
    def __init__(self, state=None, output="", compression_ratio=1.0, semantic_retention=1.0):
        self.state = state
        self.output = output
        self.compression_ratio = compression_ratio
        self.semantic_retention = semantic_retention
        self.timestamp = time.time()


class _MockAdaptiveRouter:
    ACADEMIC_MARKERS = [
        "佛教", "量子", "哲学", "辩证法", "劳动过程", "算法管理",
        "泰勒制", "布雷弗曼", "布洛维", "霍赫希尔德", "斯尔尼塞克",
        "去技能化", "制造同意", "情感劳动", "平台资本主义",
        "黑箱", "悖论", "张力", "悬置", "连续性", "断裂",
    ]

    def detect(self, text: str) -> Any:
        markers_found = [m for m in self.ACADEMIC_MARKERS if m in text]
        marker_count = len(markers_found)

        if len(text) <= 25 and marker_count == 0:
            return _MockRoutingDecision(
                path="quick",
                target_fold_depth=0,
                confidence=0.9,
                reasoning="Short query, no academic markers.",
            )
        if marker_count >= 2:
            return _MockRoutingDecision(
                path="deep",
                target_fold_depth=9,
                confidence=0.85,
                reasoning=f"Academic markers >= 2: full chain.",
            )
        return _MockRoutingDecision(
            path="standard",
            target_fold_depth=3,
            confidence=0.7,
            reasoning="Low academic content: single-layer.",
        )

    def degrade(self, decision):
        if decision.path == "deep":
            return _MockRoutingDecision(
                path="degraded",
                target_fold_depth=3,
                confidence=decision.confidence * 0.7,
            )
        return decision


class _MockDualReasoner:
    def __init__(self, max_folds=9):
        self.max_folds = max_folds

    def reason(self, dual_state, fold_budget):
        tension = _MockTension(
            perspective_A=dual_state.perspective_A.name if dual_state.perspective_A else "视角A",
            perspective_B=dual_state.perspective_B.name if dual_state.perspective_B else "视角B",
            intensity=0.6,
        )
        # 模拟 fold 迭代
        for i in range(min(fold_budget, self.max_folds)):
            tension.irreconcilable_points.append(
                f"第{i+1}层张力：对立概念不可调和"
            )
        return tension


class _MockCompressionCore:
    CONSTITUTIONAL_RULES = [
        "无'我'", "无'你应当'", "无鸡汤", "无 AI 套话",
        "不问句结尾", "优先使用'不是 X，而是 Y'句式",
        "矛盾点悬停不下结论", "理论引用大于概括性陈述",
    ]

    def compress(self, tension, route):
        parts = []
        parts.append(f"【Construct】{tension.perspective_A}")
        parts.append(f"【Deconstruct】{tension.perspective_B}")
        for i, point in enumerate(tension.irreconcilable_points[:2]):
            parts.append(f"【张力-{i+1}】{point}")
        final = "\n\n".join(parts)
        return _MockCompressedOutput(
            output=final,
            fold_depth=len(tension.irreconcilable_points),
            decision_ready=True,
        )


class _MockLLMEvaluation:
    def __init__(self):
        self.difficulty = 0.5
        self.fold_depth = 4
        self.compression_target = 2.5
        self.is_specialized = False
        self.reasoning = "基于规则评估"
        self.confidence = 0.6


class _MockLLMFoldEvaluator:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._fallback_enabled = True

    def evaluate(self, query: str):
        if self.llm_client:
            return self._llm_evaluate(query)
        return self._fallback_evaluate(query)

    def _llm_evaluate(self, query):
        try:
            prompt = f"评估查询复杂度: {query}"
            resp = self.llm_client.generate(prompt)
            return _MockLLMEvaluation()
        except Exception:
            return self._fallback_evaluate(query)

    def _fallback_evaluate(self, query):
        ev = _MockLLMEvaluation()
        ev.difficulty = min(len(query) / 200, 1.0)
        if ev.difficulty < 0.3:
            ev.fold_depth = 2
        elif ev.difficulty < 0.6:
            ev.fold_depth = 4
        else:
            ev.fold_depth = 7
        ev.reasoning = f"基于规则: 长度={len(query)}, 概念密度估计={ev.difficulty:.2f}"
        return ev


class _MockLLMCompressor:
    def __init__(self, llm_client=None, config=None):
        self.llm_client = llm_client
        self.config = config
        self._call_count = 0
        self._fallback_count = 0
        self._total_compress_count = 0

    def fold_once(self, state):
        self._total_compress_count += 1
        current = state.compressed_output or state.query
        if self.llm_client:
            try:
                compressed = self.llm_client.generate(f"压缩以下内容：\n{current}")
                self._call_count += 1
                state.compressed_output = compressed
                state.compression_ratio = len(state.query) / max(len(compressed), 1)
                return state
            except Exception:
                self._fallback_count += 1
        # fallback
        target_len = max(int(len(current) * 0.6), 10)
        state.compressed_output = current[:target_len] + "..."
        state.compression_ratio = len(state.query) / max(len(state.compressed_output), 1)
        return state

    def compress(self, text, target_ratio=0.6, instruction=""):
        self._total_compress_count += 1
        if not text:
            return text
        target_len = max(int(len(text) * target_ratio), 10)
        return text[:target_len] + "..."

    def get_stats(self):
        return {
            "total_compress_count": self._total_compress_count,
            "llm_call_count": self._call_count,
            "fallback_count": self._fallback_count,
            "llm_available": self.llm_client is not None,
        }


class _MockMemoryLearner:
    def __init__(self, db_path="n9r20_memory.db"):
        self.db_path = db_path
        self._records: List[Dict] = []
        self._initialized = True

    def record_skill(self, skill):
        self._records.append({
            "name": getattr(skill, "name", "unknown"),
            "category": getattr(skill, "category", "general"),
            "timestamp": time.time(),
        })

    def get_skill(self, name):
        return None

    def list_skills(self, category=""):
        return []

    def save_session(self, session_id: str, state: Any, output: str) -> None:
        """保存会话记录（扩展方法，用于 quickstart REPL）。"""
        self._records.append({
            "session_id": session_id,
            "query": getattr(state, "query", ""),
            "output": output,
            "fold_depth": getattr(state, "fold_depth", 0),
            "compression_ratio": getattr(state, "compression_ratio", 1.0),
            "timestamp": time.time(),
        })


class _MockSkillRecord:
    def __init__(self, name="", category="", success_count=0, fail_count=0, last_used="", metadata=None):
        self.name = name
        self.category = category
        self.success_count = success_count
        self.fail_count = fail_count
        self.last_used = last_used
        self.metadata = metadata or {}


# ════════════════════════════════════════════════════════════════════
# § 2 · 真实模块导入（失败时回退到 Mock）
# ════════════════════════════════════════════════════════════════════

# --- structures ---
_structures = _safe_import(
    "core.n9r20_structures",
    ["N9R20DualState", "N9R20Perspective", "N9R20Tension", "N9R20PerspectiveType",
     "N9R20RoutingDecision", "N9R20CompressedOutput", "N9R20SkillBook", "N9R20TermNode"],
    lambda: (_MockDualState, _MockPerspective, _MockTension, _MockPerspectiveType,
             _MockRoutingDecision, _MockCompressedOutput, _MockSkillBook, None)
)
if isinstance(_structures, tuple):
    (N9R20DualState, N9R20Perspective, N9R20Tension, N9R20PerspectiveType,
     N9R20RoutingDecision, N9R20CompressedOutput, N9R20SkillBook, N9R20TermNode) = _structures
else:
    # 真实导入成功
    N9R20DualState = _safe_import("core.n9r20_structures", ["N9R20DualState"], _make_mock_dual_state)
    N9R20Perspective = _safe_import("core.n9r20_structures", ["N9R20Perspective"], lambda: _MockPerspective)
    N9R20Tension = _safe_import("core.n9r20_structures", ["N9R20Tension"], lambda: _MockTension)
    N9R20PerspectiveType = _safe_import("core.n9r20_structures", ["N9R20PerspectiveType"], lambda: _MockPerspectiveType)
    N9R20RoutingDecision = _safe_import("core.n9r20_structures", ["N9R20RoutingDecision"], lambda: _MockRoutingDecision)
    N9R20CompressedOutput = _safe_import("core.n9r20_structures", ["N9R20CompressedOutput"], lambda: _MockCompressedOutput)
    N9R20SkillBook = _safe_import("core.n9r20_structures", ["N9R20SkillBook"], lambda: _MockSkillBook)
    N9R20TermNode = _safe_import("core.n9r20_structures", ["N9R20TermNode"])

# --- tension bus ---
_tbus = _safe_import(
    "core.n9r20_tension_bus",
    ["N9R20TensionBus", "N9R20QueryEvent", "N9R20CompressionCompleteEvent", "n9r20_bus"],
    lambda: (_MockTensionBus, _MockQueryEvent, _MockCompressionCompleteEvent, _MockTensionBus())
)
if isinstance(_tbus, tuple):
    N9R20TensionBus, N9R20QueryEvent, N9R20CompressionCompleteEvent, n9r20_bus = _tbus
else:
    N9R20TensionBus = _safe_import("core.n9r20_tension_bus", ["N9R20TensionBus"], lambda: _MockTensionBus)
    N9R20QueryEvent = _safe_import("core.n9r20_tension_bus", ["N9R20QueryEvent"], lambda: _MockQueryEvent)
    N9R20CompressionCompleteEvent = _safe_import(
        "core.n9r20_tension_bus", ["N9R20CompressionCompleteEvent"], lambda: _MockCompressionCompleteEvent
    )
    n9r20_bus = _safe_import("core.n9r20_tension_bus", ["n9r20_bus"], lambda: _MockTensionBus())

# --- adaptive router ---
N9R20AdaptiveRouter = _safe_import("core.n9r20_adaptive_router", ["N9R20AdaptiveRouter"], lambda: _MockAdaptiveRouter)

# --- dual reasoner ---
N9R20DualReasoner = _safe_import("core.n9r20_dual_reasoner", ["N9R20DualReasoner"], lambda: _MockDualReasoner)

# --- compression core ---
N9R20CompressionCore = _safe_import("core.n9r20_compression_core", ["N9R20CompressionCore"], lambda: _MockCompressionCore)

# --- llm evaluator ---
N9R20LLMFoldEvaluator = _safe_import("core.n9r20_llm_evaluator", ["N9R20LLMFoldEvaluator"], lambda: _MockLLMFoldEvaluator)

# --- llm compressor ---
N9R20LLMCompressor = _safe_import("core.n9r20_llm_compressor", ["N9R20LLMCompressor"], lambda: _MockLLMCompressor)

# --- memory learner ---
_memory = _safe_import(
    "core.n9r20_memory_learner",
    ["N9R20MemoryLearner", "SkillRecord"],
    lambda: (_MockMemoryLearner, _MockSkillRecord)
)
if isinstance(_memory, tuple):
    N9R20MemoryLearner, SkillRecord = _memory
else:
    N9R20MemoryLearner = _safe_import("core.n9r20_memory_learner", ["N9R20MemoryLearner"], lambda: _MockMemoryLearner)
    SkillRecord = _safe_import("core.n9r20_memory_learner", ["SkillRecord"], lambda: _MockSkillRecord)


# ════════════════════════════════════════════════════════════════════
# § 3 · Mock LLM 客户端（让流程跑通，不依赖外部 API）
# ════════════════════════════════════════════════════════════════════

class MockLLMClient:
    """
    本地 mock LLM 客户端 —— 不调用任何外部 API。

    基于规则生成响应，让 9R-2.0 完整流程可以跑通。
    生产环境替换为真实的 OpenAI / Claude / 本地 Ollama 客户端即可。
    """

    def generate(self, prompt: str) -> str:
        """基于 prompt 类型返回模拟响应。"""
        p = prompt.lower()

        # 压缩类 prompt
        if "压缩" in prompt or "compress" in p:
            # 提取最后一段文本作为输入
            lines = prompt.strip().split("\n")
            text = lines[-1] if len(lines) > 1 else prompt
            target_len = max(int(len(text) * 0.5), 10)
            return text[:target_len] + " [压缩结果]"

        # 评估类 prompt
        if "评估" in prompt or "evaluate" in p or "difficulty" in p:
            return json.dumps({
                "difficulty": 0.5,
                "fold_depth": 4,
                "compression_target": 2.5,
                "is_specialized": False,
                "reasoning": "基于规则的 mock 评估",
                "confidence": 0.6,
            }, ensure_ascii=False)

        # 双视角 / 张力分析
        if "张力" in prompt or "tension" in p or "perspective" in p:
            return (
                "视角A：理论层面 —— 强调概念结构和逻辑一致性\n"
                "视角B：实践层面 —— 强调经验性和可操作性\n"
                "核心张力：抽象与具体之间的不可调和性"
            )

        # 默认响应
        return f"[MockLLM 响应] 收到 {len(prompt)} 字符的 prompt。"


# ════════════════════════════════════════════════════════════════════
# § 4 · KL9 Agent 核心引擎
# ════════════════════════════════════════════════════════════════════

class KL9Agent:
    """
    KL9 Agent —— 9R-2.0 完整认知流程编排器。

    每轮对话执行：
      1. 路由决策（Router）
      2. 事件总线通知（TensionBus）
      3. 双视角推理（DualReasoner）
      4. 四模式压缩（CompressionCore）
      5. LLM 评估（LLMEvaluator）
      6. LLM 语义压缩（LLMCompressor）
      7. 输出格式化
      8. 记忆保存（MemoryLearner）
    """

    def __init__(self, llm_client=None, db_path="n9r20_memory.db"):
        self.session_id = str(uuid.uuid4())[:8]
        self.turn_count = 0
        self.history: List[Dict[str, Any]] = []

        # 初始化各子系统
        self.llm_client = llm_client or MockLLMClient()
        self.router = N9R20AdaptiveRouter()
        self.bus = n9r20_bus if n9r20_bus else _MockTensionBus()
        self.reasoner = N9R20DualReasoner()
        self.compression = N9R20CompressionCore()
        self.evaluator = N9R20LLMFoldEvaluator(llm_client=self.llm_client)
        self.compressor = N9R20LLMCompressor(llm_client=self.llm_client)
        self.memory = N9R20MemoryLearner(db_path=db_path)

    def process(self, query: str) -> Dict[str, Any]:
        """
        处理单轮用户输入，返回完整结果字典。
        """
        self.turn_count += 1
        start_time = time.time()

        # ── 1. 创建 DualState ──────────────────────────────
        state = N9R20DualState(
            query=query,
            session_id=self.session_id,
        )

        # ── 2. 路由决策 ────────────────────────────────────
        route_decision = self.router.detect(query)
        # 将路由决策映射到 state
        state.target_fold_depth = getattr(route_decision, "target_fold_depth", 4) or 4
        state.target_compression_ratio = getattr(route_decision, "target_compression_ratio", 2.5) or 2.5

        # ── 3. 事件总线：发射 QueryEvent ───────────────────
        try:
            event = N9R20QueryEvent(query=query, session_id=self.session_id)
        except Exception:
            event = _MockQueryEvent(query=query, session_id=self.session_id)
        self.bus.emit(event)

        # ── 4. 双视角推理 ──────────────────────────────────
        # 构建 A/B 视角
        pa = N9R20Perspective(name="理论视角", characteristics=["抽象", "逻辑", "结构"])
        pb = N9R20Perspective(name="实践视角", characteristics=["经验", "操作", "效果"])
        state.perspective_A = pa
        state.perspective_B = pb

        fold_budget = min(state.target_fold_depth, 9)
        tension = self.reasoner.reason(state, fold_budget)
        state.tension = tension
        state.fold_depth = len(getattr(tension, "irreconcilable_points", []))

        # ── 5. 四模式压缩 ──────────────────────────────────
        try:
            compressed = self.compression.compress(tension, route_decision)
            state.compressed_output = getattr(compressed, "output", "")
            state.decision_ready = getattr(compressed, "decision_ready", True)
            state.mode_sequence = getattr(compressed, "mode_sequence", ["construct", "deconstruct"])
        except Exception as e:
            _import_warnings.append(f"compression_core 运行时错误: {e}")
            state.compressed_output = f"【压缩输出】{query[:100]}..."
            state.decision_ready = True

        # ── 6. LLM 评估 ────────────────────────────────────
        try:
            eval_result = self.evaluator.evaluate(query)
            # 根据评估微调 fold 深度
            if hasattr(eval_result, "fold_depth"):
                state.target_fold_depth = eval_result.fold_depth
            if hasattr(eval_result, "compression_target"):
                state.target_compression_ratio = eval_result.compression_target
        except Exception as e:
            _import_warnings.append(f"llm_evaluator 运行时错误: {e}")

        # ── 7. LLM 语义压缩 ─────────────────────────────────
        try:
            state = self.compressor.fold_once(state)
        except Exception as e:
            _import_warnings.append(f"llm_compressor 运行时错误: {e}")
            # fallback
            if not state.compressed_output:
                target_len = max(int(len(query) * 0.6), 10)
                state.compressed_output = query[:target_len] + "..."
                state.compression_ratio = len(query) / max(len(state.compressed_output), 1)

        # ── 8. 格式化输出 ──────────────────────────────────
        output = self._format_output(state, route_decision, tension)

        # ── 9. 记忆保存 ────────────────────────────────────
        try:
            self.memory.save_session(self.session_id, state, output)
            # 同时记录 skill 调用
            sr = SkillRecord(
                name="kl9_quickstart",
                category="compression-core",
                success_count=1,
                last_used=time.strftime("%Y-%m-%d %H:%M:%S"),
                metadata={"session_id": self.session_id, "turn": self.turn_count, "query": query},
            )
            self.memory.record_skill(sr)
        except Exception as e:
            _import_warnings.append(f"memory_learner 运行时错误: {e}")

        elapsed = time.time() - start_time

        result = {
            "session_id": self.session_id,
            "turn": self.turn_count,
            "query": query,
            "route": getattr(route_decision, "path", "standard"),
            "fold_depth": state.fold_depth,
            "target_fold_depth": state.target_fold_depth,
            "compression_ratio": round(state.compression_ratio, 2),
            "semantic_retention": round(state.semantic_retention, 2),
            "output": output,
            "elapsed_ms": round(elapsed * 1000, 1),
            "mode_sequence": state.mode_sequence,
            "decision_ready": state.decision_ready,
        }
        self.history.append(result)
        return result

    def _format_output(self, state, route_decision, tension) -> str:
        """将状态格式化为用户友好的输出。"""
        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"【KL9 洞察 · 第 {self.turn_count} 轮】")
        lines.append(f"{'='*60}")

        # 路由信息
        route_name = getattr(route_decision, "path", "standard")
        confidence = getattr(route_decision, "confidence", 0.0)
        lines.append(f"\n▸ 路由决策: {route_name} (置信度: {confidence:.0%})")
        lines.append(f"▸ 分配 fold 深度: {state.target_fold_depth}")
        lines.append(f"▸ 目标压缩率: {state.target_compression_ratio:.1f}x")

        # 双视角
        pa = state.perspective_A
        pb = state.perspective_B
        if pa and pb:
            lines.append(f"\n▸ 双视角张力:")
            lines.append(f"  A — {getattr(pa, 'name', '视角A')}: {getattr(pa, 'characteristics', [])}")
            lines.append(f"  B — {getattr(pb, 'name', '视角B')}: {getattr(pb, 'characteristics', [])}")

        # 张力点
        tension_points = getattr(tension, "irreconcilable_points", [])
        if tension_points:
            lines.append(f"\n▸ 识别到的张力点 ({len(tension_points)} 层):")
            for i, tp in enumerate(tension_points[:5], 1):
                lines.append(f"  {i}. {tp}")
            if len(tension_points) > 5:
                lines.append(f"  ... 共 {len(tension_points)} 层")

        # 压缩结果
        lines.append(f"\n▸ 压缩输出:")
        lines.append(f"  {state.compressed_output}")

        # 元信息
        lines.append(f"\n▸ 压缩统计:")
        lines.append(f"  实际压缩率: {state.compression_ratio:.2f}x")
        lines.append(f"  语义保留率: {state.semantic_retention:.0%}")
        lines.append(f"  四模序列: {' → '.join(state.mode_sequence) if state.mode_sequence else 'N/A'}")
        lines.append(f"  决断就绪: {'是' if state.decision_ready else '否'}")

        lines.append(f"\n{'='*60}")
        return "\n".join(lines)

    def status(self) -> str:
        """返回当前会话状态。"""
        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"【KL9 Agent 状态】")
        lines.append(f"{'='*60}")
        lines.append(f"Session ID: {self.session_id}")
        lines.append(f"对话轮次: {self.turn_count}")
        lines.append(f"LLM 客户端: {'MockLLM (本地规则)' if isinstance(self.llm_client, MockLLMClient) else '外部 API'}")

        # 子系统状态
        lines.append(f"\n▸ 子系统:")
        lines.append(f"  Router:     {'✓' if self.router else '✗'}")
        lines.append(f"  TensionBus: {'✓' if self.bus else '✗'}")
        lines.append(f"  Reasoner:   {'✓' if self.reasoner else '✗'}")
        lines.append(f"  Compressor: {'✓' if self.compression else '✗'}")
        lines.append(f"  Evaluator:  {'✓' if self.evaluator else '✗'}")
        lines.append(f"  LLMComp:    {'✓' if self.compressor else '✗'}")
        lines.append(f"  Memory:     {'✓' if self.memory else '✗'}")

        # 统计
        lines.append(f"\n▸ 压缩器统计:")
        try:
            stats = self.compressor.get_stats()
            for k, v in stats.items():
                lines.append(f"  {k}: {v}")
        except Exception:
            lines.append("  (统计获取失败)")

        # 历史
        if self.history:
            lines.append(f"\n▸ 最近 {min(3, len(self.history))} 轮对话:")
            for h in self.history[-3:]:
                lines.append(f"  Turn {h['turn']}: [{h['route']}] {h['query'][:40]}...")

        # 导入警告
        if _import_warnings:
            lines.append(f"\n▸ 模块加载警告:")
            for w in _import_warnings[-5:]:
                lines.append(f"  {w}")

        lines.append(f"\n{'='*60}")
        return "\n".join(lines)

    def clear(self):
        """清空当前会话上下文（保留 session_id）。"""
        self.turn_count = 0
        self.history.clear()
        try:
            self.bus.clear_session(self.session_id)
        except Exception:
            pass
        return "✓ 会话上下文已清空（Session ID 保持不变）"


# ════════════════════════════════════════════════════════════════════
# § 5 · REPL 主循环
# ════════════════════════════════════════════════════════════════════

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌿 KL9-RHIZOME 9R-2.0 · 交互式 Agent                        ║
║                                                              ║
║   输入你的问题，Agent 将走完整认知流程：                       ║
║   Router → TensionBus → DualReasoner → CompressionCore      ║
║   → LLMEvaluator → LLMCompressor → MemoryLearner              ║
║                                                              ║
║   命令:  status  查看状态                                     ║
║          clear  清空会话                                      ║
║          help   显示帮助                                      ║
║          quit   退出                                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_help():
    print("""
【KL9 Agent 帮助】

交互命令:
  status      查看当前会话、子系统状态、历史记录
  clear       清空本轮对话上下文（Session ID 不变）
  help        显示此帮助
  quit / exit 退出 REPL

输入任何其他文本，Agent 会将其作为 query 走完整 9R-2.0 流程处理。

流程说明:
  1. Router      — 检测查询类型，分配 fold 深度
  2. TensionBus  — 发射 QueryEvent，通知各子系统
  3. DualReasoner — 建立 A/B 双视角，识别张力点
  4. CompressionCore — 四模式压缩（construct/deconstruct/validate/interrupt）
  5. LLMEvaluator — 评估查询复杂度，动态调整参数
  6. LLMCompressor — 语义感知压缩（复用框架 LLM 连接）
  7. MemoryLearner — 保存会话记录，持续学习

注意:
  · LLM 调用当前使用 MockLLMClient（本地规则，不耗 API）
  · 生产环境替换为真实 LLM 客户端即可
  · 某些 core 模块为 stub 状态，已自动 fallback 到 mock
""")


def repl():
    """主 REPL 循环。"""
    print_banner()

    # 如果有模块加载警告，先显示
    if _import_warnings:
        print("⚠  部分 core 模块加载失败，已自动 fallback 到 mock 实现:")
        for w in _import_warnings:
            print(f"   {w}")
        print()

    # 初始化 Agent
    db_path = script_dir / "data" / "n9r20_memory.db"
    db_path.parent.mkdir(exist_ok=True)
    agent = KL9Agent(db_path=str(db_path))

    print(f"📦 Session ID: {agent.session_id}")
    print(f"🗄  Memory DB:  {db_path}")
    print()

    # readline 历史
    histfile = script_dir / ".kl9_history"
    try:
        readline.read_history_file(str(histfile))
    except FileNotFoundError:
        pass

    while True:
        try:
            user_input = input("KL9> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见。")
            break

        if not user_input:
            continue

        # 保存到 readline 历史
        readline.add_history(user_input)

        # 命令分发
        cmd = user_input.lower()

        if cmd in ("quit", "exit", "q"):
            print("👋 再见。")
            break

        elif cmd == "status":
            print(agent.status())

        elif cmd == "clear":
            print(agent.clear())

        elif cmd == "help":
            print_help()

        else:
            # 走完整 9R-2.0 流程
            try:
                result = agent.process(user_input)
                print(result["output"])
            except Exception as e:
                print(f"\n❌ 处理异常: {e}")
                import traceback
                traceback.print_exc()

    # 保存历史
    try:
        readline.write_history_file(str(histfile))
    except Exception:
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="KL9 Agent · 交互式 REPL")
    parser.add_argument("--version", action="store_true", help="显示版本并退出")
    parser.add_argument("--eval", dest="eval_query", help="非交互模式：直接处理一条查询")
    args = parser.parse_args()

    if args.version:
        print("KL9-RHIZOME 9R-2.0 (quickstart.py)")
        return 0

    if args.eval_query:
        # 非交互模式
        db_path = script_dir / "data" / "n9r20_memory.db"
        db_path.parent.mkdir(exist_ok=True)
        agent = KL9Agent(db_path=str(db_path))
        result = agent.process(args.eval_query)
        print(result["output"])
        return 0

    # 交互模式
    repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
