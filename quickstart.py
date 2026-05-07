#!/usr/bin/env python3
"""
KL9 Agent · 快速启动入口
==========================
支持三种运行模式：
  1. Standalone REPL — 交互式命令行
  2. OpenClaw Plugin — 作为 OpenClaw Agent 插件注册
  3. Hermas/Claw API — 通过 HTTP API 接收任务

用法：
  python quickstart.py                    # 交互模式
  python quickstart.py --mode agent       # Agent 服务
  python quickstart.py --mode openclaw    # OpenClaw 插件模式
  python quickstart.py --eval "query"     # 单条评估
"""

from __future__ import annotations

import sys
import os
import uuid
import time
import json
import readline
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

# ════════════════════════════════════════════════════════════════════
# § 0 · 路径设置
# ════════════════════════════════════════════════════════════════════

script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# ════════════════════════════════════════════════════════════════════
# § 1 · Agent 结果结构
# ════════════════════════════════════════════════════════════════════

class AgentStatus(Enum):
    OK = "ok"
    ERROR = "error"
    DEGRADED = "degraded"  # 部分模块 fallback 到 mock

@dataclass
class KL9AgentResult:
    """Agent 结构化输出 — 可被框架消费"""
    status: str = "ok"           # "ok" | "error" | "degraded"
    query: str = ""
    output: str = ""             # 最终压缩洞察文本
    session_id: str = ""
    
    # 路由信息
    route: str = "standard"      # quick | standard | deep | degraded
    fold_depth: int = 0
    compression_ratio: float = 1.0
    semantic_retention: float = 1.0
    
    # 双视角
    perspective_A: str = ""
    perspective_B: str = ""
    tension_points: List[str] = field(default_factory=list)
    
    # 质量评估
    constitutional_check: bool = False
    cheap_synthesis_detected: bool = False
    
    # 元信息
    processing_time_ms: int = 0
    llm_calls: int = 0
    fallback_used: bool = False
    modules_loaded: Dict[str, bool] = field(default_factory=dict)
    
    # 错误信息
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ════════════════════════════════════════════════════════════════════
# § 2 · Mock 基础设施（核心模块导入失败时的 fallback）
# ════════════════════════════════════════════════════════════════════

_import_warnings: List[str] = []

try:
    import core.n9r20_structures as _structs_mod
    if not hasattr(_structs_mod, "FoldDepth"):
        class _FoldDepth(Enum):
            QUICK = "quick"; STANDARD = "standard"; DEEP = "deep"; DEGRADED = "degraded"
        _structs_mod.FoldDepth = _FoldDepth
except Exception:
    pass

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
        _import_warnings.append(f"⚠ {module_path}.{names[0]} 导入失败: {e}")
        if mock_factory:
            return mock_factory()
        return None


# ── Mock 类 ──────────────────────────────────────────

class _MockPerspectiveType:
    THEORETICAL = "theoretical"; EMBODIED = "embodied"
    PRACTICAL = "practical"; CRITICAL = "critical"

class _MockFoldDepth:
    QUICK = "quick"; STANDARD = "standard"; DEEP = "deep"; DEGRADED = "degraded"

@dataclass
class _MockPerspective:
    name: str = ""; characteristics: List[str] = field(default_factory=list)
    key: str = ""; perspective_type: Any = _MockPerspectiveType.THEORETICAL; viewpoint: str = ""
    def __post_init__(self):
        if not self.key: self.key = self.name

@dataclass
class _MockTension:
    perspective_A: str = ""; perspective_B: str = ""; claim_A: str = ""
    claim_B: str = ""; irreconcilable_points: List[str] = field(default_factory=list)
    tension_points: List[str] = field(default_factory=list); tension_type: str = ""
    intensity: float = 0.5; dual_state: Optional[Any] = None
    max_fold_depth: int = 0; fold_count: int = 0; suspension_reached: bool = False
    def assess_suspension(self) -> bool:
        self.suspension_reached = self.fold_count >= self.max_fold_depth or len(self.irreconcilable_points) >= 4
        return self.suspension_reached

@dataclass
class _MockDualState:
    query: str = ""; session_id: str = ""
    perspective_A: Optional[Any] = None; perspective_B: Optional[Any] = None
    tension: Optional[Any] = None; fold_depth: int = 0; target_fold_depth: int = 4
    compression_ratio: float = 1.0; target_compression_ratio: float = 2.5
    semantic_retention: float = 1.0; current_mode: str = ""
    mode_sequence: List[str] = field(default_factory=list); decision_ready: bool = False
    compressed_output: str = ""; source_skill: str = "compression-core"; timestamp: float = 0.0
    def __post_init__(self):
        if self.timestamp == 0.0: self.timestamp = time.time()

@dataclass
class _MockRoutingDecision:
    path: str = "standard"; confidence: float = 0.0; difficulty: float = 0.5
    target_fold_depth: int = 4; target_compression_ratio: float = 2.5; urgency: float = 0.5
    concept_density: float = 0.0; tension_factor: float = 0.0; length_factor: float = 0.0
    academic_markers: List[str] = field(default_factory=list); reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class _MockCompressedOutput:
    output: str = ""; compression_ratio: float = 1.0; semantic_retention: float = 1.0
    fold_depth: int = 0; mode_sequence: List[str] = field(default_factory=list)
    decision_ready: bool = False; session_id: str = ""; timestamp: float = 0.0
    def __post_init__(self):
        if self.timestamp == 0.0: self.timestamp = time.time()

class _MockTensionBus:
    _instance = None
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls); cls._instance._initialized = False
        return cls._instance
    def __init__(self):
        if getattr(self, '_initialized', False): return
        self._initialized = True; self._events: List[Any] = []; self._handlers: Dict[str, List[Any]] = {}
    def emit(self, event):
        self._events.append(event); et = type(event).__name__
        for h in self._handlers.get(et, []):
            try: h(event)
            except Exception: pass
    def on(self, event_type, handler): self._handlers.setdefault(event_type, []).append(handler)
    def clear_session(self, session_id): self._events = [e for e in self._events if getattr(e, "session_id", "") != session_id]
    def route_by_urgency(self, event): return ["compression-core", "dual-reasoner"]
    def fallback_route(self, query): return "standard-compression"

class _MockQueryEvent:
    def __init__(self, query="", session_id=""): self.query = query; self.session_id = session_id; self.timestamp = time.time()

class _MockCompressionCompleteEvent:
    def __init__(self, state=None, output="", compression_ratio=1.0, semantic_retention=1.0):
        self.state = state; self.output = output; self.compression_ratio = compression_ratio
        self.semantic_retention = semantic_retention; self.timestamp = time.time()

class _MockAdaptiveRouter:
    ACADEMIC_MARKERS = ["佛教", "量子", "哲学", "辩证法", "劳动过程", "算法管理", "泰勒制",
        "布雷弗曼", "布洛维", "霍赫希尔德", "斯尔尼塞克", "去技能化", "制造同意",
        "情感劳动", "平台资本主义", "黑箱", "悖论", "张力", "悬置", "连续性", "断裂"]
    def detect(self, text: str) -> Any:
        markers_found = [m for m in self.ACADEMIC_MARKERS if m in text]
        if len(text) <= 25 and not markers_found:
            return _MockRoutingDecision(path="quick", target_fold_depth=0, confidence=0.9, reasoning="Short query")
        if len(markers_found) >= 2:
            return _MockRoutingDecision(path="deep", target_fold_depth=9, confidence=0.85, academic_markers=markers_found)
        return _MockRoutingDecision(path="standard", target_fold_depth=3, confidence=0.7, academic_markers=markers_found)
    def degrade(self, decision):
        if decision.path == "deep":
            return _MockRoutingDecision(path="degraded", target_fold_depth=3, confidence=decision.confidence * 0.7)
        return decision

class _MockDualReasoner:
    def __init__(self, max_folds=9): self.max_folds = max_folds
    def reason(self, dual_state, fold_budget):
        tension = _MockTension(
            perspective_A=getattr(getattr(dual_state, 'perspective_A', None), 'name', '视角A'),
            perspective_B=getattr(getattr(dual_state, 'perspective_B', None), 'name', '视角B'),
            intensity=0.6, dual_state=dual_state, max_fold_depth=min(fold_budget, self.max_folds)
        )
        for i in range(min(fold_budget, self.max_folds)):
            tp = f"第{i+1}层张力：对立概念不可调和"
            tension.tension_points.append(tp); tension.irreconcilable_points.append(tp)
            tension.fold_count = i + 1
            if tension.assess_suspension(): break
        return tension

class _MockCompressionCore:
    CONSTITUTIONAL_RULES = ["无'我'", "无'你应当'", "无鸡汤", "无 AI 套话", "不问句结尾",
        "优先使用'不是 X，而是 Y'句式", "矛盾点悬停不下结论", "理论引用大于概括性陈述"]
    def compress(self, tension, route):
        parts = []; pa = getattr(tension, 'perspective_A', '视角A'); pb = getattr(tension, 'perspective_B', '视角B')
        parts.append(f"【Construct】{pa}"); parts.append(f"【Deconstruct】{pb}")
        for i, point in enumerate(getattr(tension, 'irreconcilable_points', [])[:3]):
            parts.append(f"【张力-{i+1}】{point}")
        cheap = any(m in " ".join(parts) for m in ["综上所述", "因此我们可以", "总而言之", "统一来看"])
        if cheap: parts.append("【INTERRUPT】检测到廉价综合，强制重折叠")
        final = "\n\n".join(parts)
        return _MockCompressedOutput(output=final, fold_depth=len(getattr(tension, 'irreconcilable_points', [])), decision_ready=True)
    def _detect_cheap_synthesis(self, parts): return any(m in " ".join(parts) for m in ["综上所述", "因此我们可以", "总而言之", "统一来看"])

class _MockLLMEvaluation:
    def __init__(self): self.difficulty = 0.5; self.fold_depth = 4; self.compression_target = 2.5; self.is_specialized = False; self.reasoning = ""; self.confidence = 0.6

class _MockLLMFoldEvaluator:
    def __init__(self, llm_client=None): self.llm_client = llm_client; self._fallback_enabled = True
    def evaluate(self, query: str):
        if self.llm_client:
            try: return self._llm_evaluate(query)
            except Exception: pass
        return self._fallback_evaluate(query)
    def _llm_evaluate(self, query):
        try:
            resp = self.llm_client.generate(f"评估查询复杂度: {query}")
            return _MockLLMEvaluation()
        except Exception: return self._fallback_evaluate(query)
    def _fallback_evaluate(self, query):
        ev = _MockLLMEvaluation(); ev.difficulty = min(len(query) / 200, 1.0)
        ev.fold_depth = 2 if ev.difficulty < 0.3 else (4 if ev.difficulty < 0.6 else 7)
        ev.reasoning = f"基于规则: 长度={len(query)}, 难度={ev.difficulty:.2f}"
        return ev

class _MockLLMCompressor:
    def __init__(self, llm_client=None, config=None): self.llm_client = llm_client; self.config = config; self._call_count = 0; self._fallback_count = 0; self._total_compress_count = 0
    def fold_once(self, state):
        self._total_compress_count += 1; current = state.compressed_output or state.query
        if self.llm_client:
            try:
                compressed = self.llm_client.generate(f"压缩：\n{current}")
                self._call_count += 1; state.compressed_output = compressed
                state.compression_ratio = len(state.query) / max(len(compressed), 1)
                return state
            except Exception: self._fallback_count += 1
        target_len = max(int(len(current) * 0.6), 10); state.compressed_output = current[:target_len] + "..."
        state.compression_ratio = len(state.query) / max(len(state.compressed_output), 1)
        return state
    def get_stats(self): return {"total": self._total_compress_count, "llm_calls": self._call_count, "fallbacks": self._fallback_count, "llm_available": self.llm_client is not None}

class _MockMemoryLearner:
    def __init__(self, db_path="n9r20_memory.db"): self.db_path = db_path; self._records: List[Dict] = []; self._initialized = True
    def record_skill(self, skill): self._records.append({"name": getattr(skill, "name", "unknown"), "timestamp": time.time()})
    def save_session(self, session_id: str, state: Any, output: str) -> None:
        self._records.append({"session_id": session_id, "query": getattr(state, "query", ""), "output": output, "fold_depth": getattr(state, "fold_depth", 0), "compression_ratio": getattr(state, "compression_ratio", 1.0), "timestamp": time.time()})
    def get_records(self) -> List[Dict]: return self._records

class _MockSkillRecord:
    def __init__(self, name="", category="", success_count=0, fail_count=0, last_used="", metadata=None):
        self.name = name; self.category = category; self.success_count = success_count; self.fail_count = fail_count; self.last_used = last_used; self.metadata = metadata or {}


# ════════════════════════════════════════════════════════════════════
# § 3 · 真实模块导入（失败时回退到 Mock）
# ════════════════════════════════════════════════════════════════════

# --- structures ---
_structures = _safe_import("core.n9r20_structures",
    ["N9R20DualState", "N9R20Perspective", "N9R20Tension", "N9R20PerspectiveType",
     "N9R20RoutingDecision", "N9R20CompressedOutput", "N9R20SkillBook", "N9R20TermNode", "FoldDepth"],
    lambda: (_MockDualState, _MockPerspective, _MockTension, _MockPerspectiveType,
             _MockRoutingDecision, _MockCompressedOutput, None, None, _MockFoldDepth))
if isinstance(_structures, tuple):
    (N9R20DualState, N9R20Perspective, N9R20Tension, N9R20PerspectiveType,
     N9R20RoutingDecision, N9R20CompressedOutput, N9R20SkillBook, N9R20TermNode, FoldDepth) = _structures
else:
    N9R20DualState = _safe_import("core.n9r20_structures", ["N9R20DualState"], lambda: _MockDualState)
    N9R20Perspective = _safe_import("core.n9r20_structures", ["N9R20Perspective"], lambda: _MockPerspective)
    N9R20Tension = _safe_import("core.n9r20_structures", ["N9R20Tension"], lambda: _MockTension)
    N9R20PerspectiveType = _safe_import("core.n9r20_structures", ["N9R20PerspectiveType"], lambda: _MockPerspectiveType)
    N9R20RoutingDecision = _safe_import("core.n9r20_structures", ["N9R20RoutingDecision"], lambda: _MockRoutingDecision)
    N9R20CompressedOutput = _safe_import("core.n9r20_structures", ["N9R20CompressedOutput"], lambda: _MockCompressedOutput)
    N9R20SkillBook = _safe_import("core.n9r20_structures", ["N9R20SkillBook"])
    N9R20TermNode = _safe_import("core.n9r20_structures", ["N9R20TermNode"])
    FoldDepth = _safe_import("core.n9r20_structures", ["FoldDepth"], lambda: _MockFoldDepth)

# --- tension bus ---
_tbus = _safe_import("core.n9r20_tension_bus",
    ["N9R20TensionBus", "N9R20QueryEvent", "N9R20CompressionCompleteEvent", "n9r20_bus"],
    lambda: (_MockTensionBus, _MockQueryEvent, _MockCompressionCompleteEvent, _MockTensionBus()))
if isinstance(_tbus, tuple):
    N9R20TensionBus, N9R20QueryEvent, N9R20CompressionCompleteEvent, n9r20_bus = _tbus
else:
    N9R20TensionBus = _safe_import("core.n9r20_tension_bus", ["N9R20TensionBus"], lambda: _MockTensionBus)
    N9R20QueryEvent = _safe_import("core.n9r20_tension_bus", ["N9R20QueryEvent"], lambda: _MockQueryEvent)
    N9R20CompressionCompleteEvent = _safe_import("core.n9r20_tension_bus", ["N9R20CompressionCompleteEvent"], lambda: _MockCompressionCompleteEvent)
    n9r20_bus = _safe_import("core.n9r20_tension_bus", ["n9r20_bus"], lambda: _MockTensionBus())

N9R20AdaptiveRouter = _safe_import("core.n9r20_adaptive_router", ["N9R20AdaptiveRouter"], lambda: _MockAdaptiveRouter)
N9R20DualReasoner = _safe_import("core.n9r20_dual_reasoner", ["N9R20DualReasoner"], lambda: _MockDualReasoner)
N9R20CompressionCore = _safe_import("core.n9r20_compression_core", ["N9R20CompressionCore"], lambda: _MockCompressionCore)
N9R20LLMFoldEvaluator = _safe_import("core.n9r20_llm_evaluator", ["N9R20LLMFoldEvaluator"], lambda: _MockLLMFoldEvaluator)
N9R20LLMCompressor = _safe_import("core.n9r20_llm_compressor", ["N9R20LLMCompressor"], lambda: _MockLLMCompressor)

_memory = _safe_import("core.n9r20_memory_learner", ["N9R20MemoryLearner", "SkillRecord"],
    lambda: (_MockMemoryLearner, _MockSkillRecord))
if isinstance(_memory, tuple): N9R20MemoryLearner, SkillRecord = _memory
else:
    N9R20MemoryLearner = _safe_import("core.n9r20_memory_learner", ["N9R20MemoryLearner"], lambda: _MockMemoryLearner)
    SkillRecord = _safe_import("core.n9r20_memory_learner", ["SkillRecord"], lambda: _MockSkillRecord)


# ════════════════════════════════════════════════════════════════════
# § 4 · LLM 客户端（可替换为真实客户端）
# ════════════════════════════════════════════════════════════════════

class MockLLMClient:
    """本地 mock LLM — 不调用外部 API"""
    def generate(self, prompt: str) -> str:
        p = prompt.lower()
        if "压缩" in prompt or "compress" in p:
            lines = prompt.strip().split("\n"); text = lines[-1] if len(lines) > 1 else prompt
            target_len = max(int(len(text) * 0.5), 10)
            return text[:target_len] + " [压缩结果]"
        if "评估" in prompt or "evaluate" in p:
            return json.dumps({"difficulty": 0.6, "fold_depth": 5, "compression_target": 2.5, "is_specialized": False, "reasoning": "mock", "confidence": 0.7})
        return f"[MockLLM] 收到 {len(prompt)} 字符的 prompt"


# ════════════════════════════════════════════════════════════════════
# § 5 · Skillbook 加载器
# ════════════════════════════════════════════════════════════════════

class SkillbookLoader:
    """加载 skillbook/prebuilt/ 下的 SKILL.md"""
    def __init__(self, base_path: Optional[Path] = None):
        self.base = base_path or (script_dir / "skillbook" / "prebuilt")
        self._cache: Dict[str, str] = {}
    
    def list_skills(self, language: str = "") -> List[str]:
        if not self.base.exists(): return []
        if language:
            lang_dir = self.base / language
            if not lang_dir.exists(): return []
            return [d.name for d in lang_dir.iterdir() if d.is_dir()]
        result = []
        for lang_dir in self.base.iterdir():
            if lang_dir.is_dir() and not lang_dir.name.startswith("."):
                for skill_dir in lang_dir.iterdir():
                    if skill_dir.is_dir(): result.append(f"{lang_dir.name}/{skill_dir.name}")
        return result
    
    def load_skill(self, path: str) -> str:
        """path 格式: 'zh/Asvaghosa-Dasheng-Qixin-Lun-554' 或 '大乘起信论'（模糊匹配）"""
        if path in self._cache: return self._cache[path]
        skill_path = self.base / path / "SKILL.md"
        if not skill_path.exists():
            # 模糊匹配
            for lang_dir in self.base.iterdir():
                if not lang_dir.is_dir(): continue
                for skill_dir in lang_dir.iterdir():
                    if skill_dir.is_dir() and (path in skill_dir.name or path in skill_dir.name.replace("-", "")):
                        skill_path = skill_dir / "SKILL.md"
                        if skill_path.exists(): break
                if skill_path.exists(): break
        if not skill_path.exists():
            raise FileNotFoundError(f"技能书未找到: {path}")
        content = skill_path.read_text(encoding="utf-8")
        self._cache[path] = content
        return content


# ════════════════════════════════════════════════════════════════════
# § 6 · KL9 Agent 核心类
# ════════════════════════════════════════════════════════════════════

class KL9Agent:
    """
    KL9-RHIZOME 9R-2.0 Agent
    
    支持三种模式：
    1. Standalone: 本地 REPL 交互
    2. Plugin: 注册到 OpenClaw/Hermas 框架
    3. API: 通过 HTTP 接收任务
    """
    VERSION = "9R-2.0"
    
    def __init__(self, db_path: str = "", llm_client=None, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.llm_client = llm_client or MockLLMClient()
        self.turn_count = 0
        self.history: List[Dict] = []
        
        # 子系统
        self.router = N9R20AdaptiveRouter() if N9R20AdaptiveRouter else _MockAdaptiveRouter()
        self.bus = n9r20_bus if n9r20_bus else _MockTensionBus()
        self.reasoner = N9R20DualReasoner() if N9R20DualReasoner else _MockDualReasoner()
        self.compression = N9R20CompressionCore() if N9R20CompressionCore else _MockCompressionCore()
        self.evaluator = N9R20LLMFoldEvaluator(self.llm_client) if N9R20LLMFoldEvaluator else _MockLLMFoldEvaluator(self.llm_client)
        self.compressor = N9R20LLMCompressor(self.llm_client) if N9R20LLMCompressor else _MockLLMCompressor(self.llm_client)
        self.memory = N9R20MemoryLearner(db_path) if N9R20MemoryLearner else _MockMemoryLearner(db_path)
        self.skillbook = SkillbookLoader()
        
        # 模块加载状态
        self.modules_loaded = {
            "router": N9R20AdaptiveRouter is not _MockAdaptiveRouter,
            "bus": n9r20_bus is not None,
            "reasoner": N9R20DualReasoner is not _MockDualReasoner,
            "compression": N9R20CompressionCore is not _MockCompressionCore,
            "evaluator": N9R20LLMFoldEvaluator is not _MockLLMFoldEvaluator,
            "compressor": N9R20LLMCompressor is not _MockLLMCompressor,
            "memory": N9R20MemoryLearner is not _MockMemoryLearner,
        }
        self.fallback_used = any(not v for v in self.modules_loaded.values())
    
    # ──────────────────────────────────────────
    # 核心处理流程
    # ──────────────────────────────────────────
    
    def process(self, query: str) -> KL9AgentResult:
        """处理查询，返回结构化结果 — 可被框架消费"""
        start_time = time.time()
        self.turn_count += 1
        result = KL9AgentResult(
            query=query, session_id=self.session_id,
            fallback_used=self.fallback_used,
            modules_loaded=self.modules_loaded
        )
        
        try:
            # Step 1: Router
            route_decision = self.router.detect(query)
            route_path = getattr(route_decision, 'path', 'standard')
            target_depth = getattr(route_decision, 'target_fold_depth', 4)
            result.route = route_path
            result.fold_depth = target_depth
            
            # Step 2: DualState
            dual_state = N9R20DualState(query=query, session_id=self.session_id,
                target_fold_depth=target_depth)
            
            # Step 3: TensionBus
            self.bus.emit(N9R20QueryEvent(query=query, session_id=self.session_id))
            
            # Step 4: DualReasoner
            tension = self.reasoner.reason(dual_state, target_depth)
            result.perspective_A = getattr(tension, 'perspective_A', '')
            result.perspective_B = getattr(tension, 'perspective_B', '')
            result.tension_points = getattr(tension, 'irreconcilable_points', []) or getattr(tension, 'tension_points', [])
            
            # Step 5: LLM Evaluator
            evaluation = self.evaluator.evaluate(query)
            if hasattr(evaluation, 'fold_depth') and evaluation.fold_depth:
                result.fold_depth = evaluation.fold_depth
            
            # Step 6: CompressionCore
            comp_result = self.compression.compress(tension, route_path)
            output_text = getattr(comp_result, 'output', '') or getattr(comp_result, 'content', '')
            result.compression_ratio = getattr(comp_result, 'compression_ratio', 1.0) or getattr(comp_result, 'fold_depth_used', 1.0)
            result.semantic_retention = getattr(comp_result, 'semantic_retention', 1.0)
            result.constitutional_check = getattr(comp_result, 'constitutional_check', False)
            result.cheap_synthesis_detected = self.compression._detect_cheap_synthesis([output_text]) if hasattr(self.compression, '_detect_cheap_synthesis') else False
            
            # Step 7: LLM Compressor (refine)
            dual_state.compressed_output = output_text
            refined = self.compressor.fold_once(dual_state)
            final_output = getattr(refined, 'compressed_output', output_text) or output_text
            result.output = final_output
            
            # Step 8: Memory
            self.memory.save_session(self.session_id, dual_state, final_output)
            
            # Stats
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            if hasattr(self.compressor, 'get_stats'):
                stats = self.compressor.get_stats()
                result.llm_calls = stats.get('llm_call_count', 0)
            
            # History
            self.history.append({"turn": self.turn_count, "query": query, "route": route_path, "output": final_output[:100]})
            
        except Exception as e:
            result.status = "error"
            result.error = str(e)
            result.output = f"[处理异常] {e}"
        
        return result
    
    # ──────────────────────────────────────────
    # Skillbook 操作
    # ──────────────────────────────────────────
    
    def load_skill(self, skill_path: str) -> str:
        """加载技能书内容"""
        return self.skillbook.load_skill(skill_path)
    
    def list_skills(self, language: str = "") -> List[str]:
        """列出可用技能书"""
        return self.skillbook.list_skills(language)
    
    # ──────────────────────────────────────────
    # 状态与工具
    # ──────────────────────────────────────────
    
    def status(self) -> str:
        lines = ["=" * 60, "【KL9 Agent 状态】", "=" * 60,
            f"Session ID: {self.session_id}", f"对话轮次: {self.turn_count}",
            f"LLM: {'MockLLM (本地)' if isinstance(self.llm_client, MockLLMClient) else '外部 API'}",
            "\n▸ 子系统:"]
        for name, ok in self.modules_loaded.items():
            lines.append(f"  {name}: {'✓ 真实' if ok else '⚠ mock'}")
        if hasattr(self.compressor, 'get_stats'):
            lines.append("\n▸ 压缩器统计:");
            for k, v in self.compressor.get_stats().items(): lines.append(f"  {k}: {v}")
        if self.history:
            lines.append(f"\n▸ 最近 {min(3, len(self.history))} 轮:")
            for h in self.history[-3:]: lines.append(f"  Turn {h['turn']}: [{h['route']}] {h['query'][:40]}...")
        if _import_warnings:
            lines.append("\n▸ 模块加载警告:");
            for w in _import_warnings[-3:]: lines.append(f"  {w}")
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
    
    def clear(self):
        self.turn_count = 0; self.history.clear()
        try: self.bus.clear_session(self.session_id)
        except Exception: pass
        return "✓ 会话上下文已清空"
    
    # ──────────────────────────────────────────
    # Agent 模式接口（供框架调用）
    # ──────────────────────────────────────────
    
    def run_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准 Agent 任务接口 — 供 OpenClaw/Hermas 框架调用
        
        task_input: {"query": str, "session_id": str(可选), "options": dict(可选)}
        returns: KL9AgentResult.to_dict()
        """
        query = task_input.get("query", "")
        if not query:
            return KL9AgentResult(status="error", error="missing query").to_dict()
        
        # 支持外部传入 session_id
        if task_input.get("session_id"):
            self.session_id = task_input["session_id"]
        
        result = self.process(query)
        return result.to_dict()
    
    def health(self) -> Dict[str, Any]:
        """健康检查 — 供框架调用"""
        return {
            "status": "healthy" if not self.fallback_used else "degraded",
            "version": self.VERSION,
            "session_id": self.session_id,
            "modules": self.modules_loaded,
            "mock_fallback": self.fallback_used,
            "skillbooks_available": len(self.skillbook.list_skills()),
        }
    
    def get_capabilities(self) -> List[str]:
        """返回 Agent 能力列表 — 供框架注册"""
        return [
            "dual_perspective_reasoning",
            "structural_tension_analysis",
            "semantic_compression",
            "constitutional_validation",
            "skillbook_loading",
            "multi_turn_session",
        ]


# ════════════════════════════════════════════════════════════════════
# § 7 · OpenClaw / Hermas 插件注册接口
# ════════════════════════════════════════════════════════════════════

class KL9Plugin:
    """
    OpenClaw / Hermas 标准插件接口
    
    框架侧调用方式：
      plugin = KL9Plugin()
      result = plugin.handle({"query": "..."})
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        db_path = self.config.get("db_path", "")
        llm_client = self.config.get("llm_client")  # 框架注入的 LLM client
        self.agent = KL9Agent(db_path=db_path, llm_client=llm_client)
    
    def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理框架派发的任务"""
        return self.agent.run_task(request)
    
    def health(self) -> Dict[str, Any]:
        return self.agent.health()
    
    def capabilities(self) -> List[str]:
        return self.agent.get_capabilities()


# ════════════════════════════════════════════════════════════════════
# § 8 · REPL 交互模式（保留原有功能）
# ════════════════════════════════════════════════════════════════════

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌿 KL9-RHIZOME 9R-2.0 · Agent 快速启动                      ║
║                                                              ║
║   输入问题 → 走完整认知流程 → 输出结构化结果                   ║
║                                                              ║
║   命令:  status    查看状态                                   ║
║          skills   列出技能书                                  ║
║          load     加载技能书（如 load 大乘起信论）             ║
║          clear    清空会话                                    ║
║          help     显示帮助                                    ║
║          quit     退出                                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

def print_help():
    print("""
【KL9 Agent 帮助】

交互命令:
  status       查看当前会话、子系统状态
  skills       列出可用的技能书
  load <name>  加载技能书内容（如 load 大乘起信论）
  clear        清空本轮对话上下文
  help         显示此帮助
  quit / exit  退出 REPL

直接输入文本 → Agent 将其作为 query 走完整 9R-2.0 流程处理。

Agent 接口（供框架调用）:
  agent.run_task({"query": "..."})  → 返回结构化 JSON
  agent.health()                     → 返回健康状态
  agent.get_capabilities()           → 返回能力列表

注意:
  · LLM 调用当前使用 MockLLMClient（本地规则，不耗 API）
  · 生产环境替换为真实 LLM 客户端即可
  · core 模块为 stub 时自动 fallback 到 mock
""")

def repl(agent: Optional[KL9Agent] = None):
    """主 REPL 循环"""
    print_banner()
    
    if _import_warnings:
        print("⚠ 部分 core 模块加载失败，已 fallback 到 mock:");
        for w in _import_warnings: print(f"   {w}")
        print()
    
    if agent is None:
        db_path = str(script_dir / "data" / "n9r20_memory.db")
        Path(db_path).parent.mkdir(exist_ok=True)
        agent = KL9Agent(db_path=db_path)
    
    print(f"📦 Session: {agent.session_id}")
    print(f"🗄  Memory:  {agent.memory.db_path if hasattr(agent.memory, 'db_path') else 'memory.db'}")
    print(f"📚 Skills:  {len(agent.list_skills())} 本可用")
    print()
    
    histfile = script_dir / ".kl9_history"
    try: readline.read_history_file(str(histfile))
    except FileNotFoundError: pass
    
    while True:
        try: user_input = input("KL9> ").strip()
        except (EOFError, KeyboardInterrupt): print("\n👋 再见。"); break
        if not user_input: continue
        readline.add_history(user_input)
        cmd = user_input.lower()
        
        if cmd in ("quit", "exit", "q"): print("👋 再见。"); break
        elif cmd == "status": print(agent.status())
        elif cmd == "clear": print(agent.clear())
        elif cmd == "help": print_help()
        elif cmd == "skills":
            skills = agent.list_skills()
            print(f"\n📚 可用技能书 ({len(skills)} 本):");
            for s in skills[:20]: print(f"  · {s}")
            if len(skills) > 20: print(f"  ... 还有 {len(skills)-20} 本")
        elif cmd.startswith("load "):
            skill_name = user_input[5:].strip()
            try:
                content = agent.load_skill(skill_name)
                print(f"\n📖 已加载: {skill_name}")
                print(f"   长度: {len(content)} 字符")
                # 显示前 10 行
                lines = content.split('\n')[:10]
                print('\n'.join(lines))
                if len(content.split('\n')) > 10: print("   ...")
            except FileNotFoundError:
                print(f"❌ 技能书未找到: {skill_name}")
        else:
            try:
                result = agent.process(user_input)
                print(f"\n{result.output}")
                # 调试信息
                if result.status != "ok":
                    print(f"\n[状态: {result.status}] {result.error}")
            except Exception as e:
                print(f"\n❌ 处理异常: {e}")
                import traceback; traceback.print_exc()
    
    try: readline.write_history_file(str(histfile))
    except Exception: pass


# ════════════════════════════════════════════════════════════════════
# § 9 · Agent HTTP API 模式（供 Hermas/Claw 调用）
# ════════════════════════════════════════════════════════════════════

def run_agent_api(host: str = "127.0.0.1", port: int = 8233):
    """启动 Agent HTTP 服务"""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
    except ImportError:
        print("❌ 缺少 http.server 模块，无法启动 API 模式")
        return
    
    agent = KL9Agent()
    
    class AgentHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/run":
                self._send(404, {"error": "unknown endpoint, use POST /run"})
                return
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                task = json.loads(body.decode('utf-8'))
                result = agent.run_task(task)
                self._send(200, result)
            except Exception as e:
                self._send(500, {"status": "error", "error": str(e)})
        
        def do_GET(self):
            if self.path == "/health":
                self._send(200, agent.health())
            elif self.path == "/capabilities":
                self._send(200, {"capabilities": agent.get_capabilities()})
            else:
                self._send(404, {"error": "unknown endpoint"})
        
        def _send(self, code, data):
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        
        def log_message(self, format, *args): pass  # 静默日志
    
    server = HTTPServer((host, port), AgentHandler)
    print(f"🚀 KL9 Agent API 运行在 http://{host}:{port}")
    print(f"   POST /run      — 执行任务")
    print(f"   GET  /health   — 健康检查")
    print(f"   GET  /capabilities — 能力列表")
    print(f"   示例: curl -X POST http://{host}:{port}/run -d '{{\"query\":\"佛教心性论\"}}'")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Agent API 已停止")


# ════════════════════════════════════════════════════════════════════
# § 10 · 入口
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="KL9 Agent · 快速启动")
    parser.add_argument("--mode", choices=["repl", "agent", "api", "openclaw"],
                       default="repl", help="运行模式（默认 repl）")
    parser.add_argument("--host", default="127.0.0.1", help="API 模式绑定地址")
    parser.add_argument("--port", type=int, default=8233, help="API 模式端口")
    parser.add_argument("--eval", dest="eval_query", help="单条评估模式，非交互")
    parser.add_argument("--version", action="store_true", help="显示版本")
    parser.add_argument("--db", default="", help="数据库路径")
    args = parser.parse_args()
    
    if args.version:
        print(f"KL9-RHIZOME {KL9Agent.VERSION}")
        return 0
    
    # 单条评估
    if args.eval_query:
        agent = KL9Agent(db_path=args.db)
        result = agent.process(args.eval_query)
        print(result.to_json())
        return 0
    
    # REPL 模式（默认）
    if args.mode == "repl":
        repl()
        return 0
    
    # Agent API 模式
    if args.mode in ("agent", "api"):
        run_agent_api(args.host, args.port)
        return 0
    
    # OpenClaw 模式 — 输出配置并退出，由框架加载
    if args.mode == "openclaw":
        print(json.dumps({
            "plugin": "KL9Plugin",
            "entry": "quickstart.KL9Plugin",
            "config": {"db_path": args.db or str(script_dir / "data" / "n9r20_memory.db")},
            "capabilities": KL9Agent(db_path=args.db).get_capabilities(),
        }, ensure_ascii=False, indent=2))
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
