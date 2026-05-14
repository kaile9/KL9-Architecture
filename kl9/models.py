"""
9R-2.1 — Unified Data Model Layer

All shared models. Single source of truth.
Imports NOTHING from kl9.* sub-packages.
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional, TypeVar

# ── Routing ──

class RouteLevel(Enum):
    QUICK = auto()
    STANDARD = auto()
    DEEP = auto()


@dataclass
class AcademicComplexityScore:
    total: float = 0.0
    keyword_density: float = 0.0
    conceptual_depth: float = 0.0
    contextual_cues: float = 0.0
    confidence: float = 0.0


@dataclass
class RouteDecision:
    level: RouteLevel
    score: AcademicComplexityScore
    max_fold_depth: int = 3
    reason: str = ""
    degrade_from: Optional[RouteLevel] = None

    @property
    def is_degraded(self) -> bool:
        return self.degrade_from is not None


# ── LLM Communication ──

class TaskType(Enum):
    CHAT = auto()
    ACADEMIC_ANALYSIS = auto()
    EMBED = auto()
    SYNTHESIS = auto()
    REASONING = auto()
    DECOMPOSE = auto()
    VALIDATE = auto()


@dataclass(frozen=True, slots=True)
class Message:
    role: str
    content: str
    name: Optional[str] = None


@dataclass(slots=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0


@dataclass(slots=True)
class LLMResponse:
    content: str
    usage: Usage = field(default_factory=Usage)
    provider: str = "unknown"
    model: str = "unknown"
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    timeout: float = 120.0


class LLMProvider(ABC):
    NAME: str = "abstract"
    BASE_URL: str = ""
    MODEL: str = ""
    MAX_TOKENS: int = 1_048_576  # 1M default for deepseek V4
    MAX_OUTPUT_TOKENS: int = 8192

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        model: str | None = None,
        retry_config: RetryConfig | None = None,
        session: Any | None = None,
    ):
        self.api_key = api_key
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.model = model or self.MODEL
        self.retry_config = retry_config or RetryConfig()
        self._session = session

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        timeout: float = 120.0,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        timeout: float = 120.0,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model!r})"


# ── Task ──

@dataclass
class Task:
    id: str = ""
    query: str = ""
    task_type: TaskType = TaskType.CHAT
    level: RouteLevel = RouteLevel.STANDARD
    max_tokens: int = 8192
    temperature: float = 0.3
    timeout: float = 120.0
    session_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Fold Execution ──

@dataclass
class Perspective:
    """A single cognitive perspective in a fold."""
    name: str
    content: str
    theorists_cited: list[str] = field(default_factory=list)
    concepts_used: list[str] = field(default_factory=list)
    tension_points: list[str] = field(default_factory=list)
    umkehr_markers: list[str] = field(default_factory=list)


@dataclass
class FoldResult:
    """Single fold output with tension/umkehr markers extracted."""
    fold_number: int
    perspective_a: Perspective
    perspective_b: Perspective
    raw_content: str
    tension_markers: list[str] = field(default_factory=list)
    umkehr_markers: list[str] = field(default_factory=list)
    tokens_used: int = 0
    latency_ms: float = 0.0


@dataclass
class FoldChain:
    """Complete fold sequence."""
    query: str
    folds: list[FoldResult] = field(default_factory=list)
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    stopped_reason: str = ""  # "budget_exhausted" | "tension_saturated" | "error"

    @property
    def fold_count(self) -> int:
        return len(self.folds)

    @property
    def all_tensions(self) -> list[str]:
        result: list[str] = []
        for f in self.folds:
            result.extend(f.tension_markers)
        return result

    @property
    def all_umkehrs(self) -> list[str]:
        result: list[str] = []
        for f in self.folds:
            result.extend(f.umkehr_markers)
        return result


# ── Tension Gate ──

@dataclass
class TensionGateResult:
    should_continue: bool
    reason: str
    prior_tension_count: int = 0
    new_tension_count: int = 0
    prior_umkehr_count: int = 0
    new_umkehr_count: int = 0


# ── Quality Validation ──

@dataclass
class QualityScore:
    theoretical_framework: float = 0.0
    citation_standards: float = 0.0
    source_fidelity: float = 0.0
    argumentative_depth: float = 0.0
    stylistic_quality: float = 0.0
    originality: float = 0.0
    constitutional_violations: list[str] = field(default_factory=list)
    forbidden_patterns: list[str] = field(default_factory=list)
    grade: str = "D"

    @property
    def total(self) -> float:
        return (
            self.theoretical_framework * 0.20
            + self.citation_standards * 0.20
            + self.source_fidelity * 0.20
            + self.argumentative_depth * 0.20
            + self.stylistic_quality * 0.10
            + self.originality * 0.10
        )

    def assign_grade(self) -> None:
        t = self.total
        self.grade = "A" if t >= 0.85 else "B" if t >= 0.70 else "C" if t >= 0.55 else "D"


# ── Aggregation ──

@dataclass
class AggregatedOutput:
    content: str
    tension_markers: list[str] = field(default_factory=list)
    umkehr_markers: list[str] = field(default_factory=list)
    fold_depth: int = 0
    quality: Optional[QualityScore] = None
    theorists_cited: list[str] = field(default_factory=list)
    concepts_used: list[str] = field(default_factory=list)
    token_used: int = 0
    latency_ms: float = 0.0
    constitutional_warning: bool = False


# ── Degradation ──

@dataclass
class DegradationPolicy:
    consecutive_failure_threshold: int = 3
    degrading_errors: set[str] = field(
        default_factory=lambda: {"timeout", "rate_limit", "context_overflow", "token_exceeded"}
    )

    @staticmethod
    def next_level(level: RouteLevel) -> Optional[RouteLevel]:
        chain = [RouteLevel.DEEP, RouteLevel.STANDARD, RouteLevel.QUICK]
        if level not in chain:
            return None
        idx = chain.index(level)
        return chain[idx + 1] if idx + 1 < len(chain) else None

    def fallback_levels(self, level: RouteLevel) -> list[RouteLevel]:
        chain = [RouteLevel.DEEP, RouteLevel.STANDARD, RouteLevel.QUICK]
        if level not in chain:
            return list(chain)
        idx = chain.index(level)
        return chain[idx:]

    def should_degrade(
        self, level: RouteLevel, error_type: str, consecutive_failures: int
    ) -> tuple[bool, Optional[RouteLevel]]:
        if consecutive_failures >= self.consecutive_failure_threshold:
            return True, self.next_level(level)
        if consecutive_failures >= 1 and error_type in self.degrading_errors:
            return True, self.next_level(level)
        return False, None


# ── Session ──

class SessionState(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


@dataclass
class Session:
    session_id: str
    user_id: str
    platform: str = "astrbot"
    state: SessionState = SessionState.ACTIVE
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    fold_count: int = 0
    deep_routes_count: int = 0
    queries_count: int = 0
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        object.__setattr__(self, "last_active", time.time())


# ── Style Profile ──

@dataclass
class StyleProfile:
    """Extracted from user's representative works."""
    preferred_patterns: list[str] = field(default_factory=lambda: [
        "不是X，而是Y",
        "这并不意味着",
        "反过来想",
        "但这里有一个",
    ])
    forbidden_patterns: list[str] = field(default_factory=lambda: [
        "综上所述",
        "总而言之",
        "两者互补",
        "统一来看",
        "我认为",
        "在本文中",
        "应当指出",
    ])
    preferred_endings: list[str] = field(default_factory=lambda: [
        "反诘结尾——以问句或省略号收束",
        "张力悬置——以开放悖论结尾",
        "引用收束——以理论家原话结尾不作总结",
    ])
    citation_density_min: float = 0.05
    sentence_rhythm: str = "alternating"  # 长短交替
    max_summary_ratio: float = 0.05  # 禁止超过5%的概括性陈述


# ── Source Retrieval ──

class SourceWeight:
    """信源权重常量"""
    PRIMARY = 1.0      # 论文/原著/一手
    ACADEMIC = 0.7     # 学术二手
    WEB_GENERAL = 0.4  # 通用 web
    LLM_INTERNAL = 0.1 # 内部知识（仅补充）


@dataclass
class SearchResult:
    """单条检索结果"""
    title: str
    url: str = ""
    snippet: str = ""
    content: str = ""         # extract 后的全文
    source_type: str = "web"  # paper | book | article | web
    weight: float = SourceWeight.WEB_GENERAL
    priority: int = 0         # 排序用
    relevance_score: float = 0.0
    published_year: int = 0
    authors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_primary(self) -> bool:
        return self.weight >= SourceWeight.PRIMARY

    @property
    def is_academic(self) -> bool:
        return self.weight >= SourceWeight.ACADEMIC

    def summary(self, max_chars: int = 500) -> str:
        """截断摘要"""
        text = self.content or self.snippet
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "…"


@dataclass
class SourceContext:
    """检索聚合结果"""
    results: list[SearchResult] = field(default_factory=list)
    query: str = ""
    total_found: int = 0
    has_primary: bool = False
    has_academic: bool = False
    missing_notice: str = ""

    @property
    def high_quality_count(self) -> int:
        """权重 ≥ 0.7 的信源数"""
        return sum(1 for r in self.results if r.weight >= SourceWeight.ACADEMIC)

    @property
    def should_degrade(self) -> bool:
        """是否需要降级：无高权重信源"""
        return self.high_quality_count == 0 and len(self.results) > 0

    def format_for_prompt(self, max_sources: int = 5, max_chars_per: int = 2000) -> str:
        """格式化为 prompt 注入用的信源块"""
        if not self.results:
            return ""
        lines = [
            "[检索到的原文]（共 {} 条，按权重排列）\n".format(len(self.results))
        ]
        for i, r in enumerate(self.results[:max_sources]):
            authors = ", ".join(r.authors[:3]) if r.authors else ""
            if authors:
                source_label = "权重 {:.1f} | 来源: {} {}".format(r.weight, authors, r.title)
            else:
                source_label = "权重 {:.1f} | 来源: {}".format(r.weight, r.title)
            if r.published_year:
                source_label += " ({})".format(r.published_year)
            body = r.content[:max_chars_per] if r.content else r.snippet[:max_chars_per]
            lines.append("[{}] {}\n原文: \"{}\"\n---".format(i+1, source_label, body))
        if self.missing_notice:
            lines.append("\n[注意] 未能检索到: {}".format(self.missing_notice))
        lines.append("\n以上为分析信源。所有断言必须可追溯到这些原文。内部知识权重 0.1，仅作补充。")
        return "\n".join(lines)

    def format_for_fold(self, max_chars_total: int = 3000) -> str:
        """为 fold engine 提供精简的信源摘要"""
        if not self.results:
            return ""
        texts = []
        remaining = max_chars_total
        for r in sorted(self.results, key=lambda x: x.weight, reverse=True):
            s = r.summary(max_chars=min(remaining, 500))
            if not s:
                continue
            texts.append("[信源 {}] {}".format(r.weight, s))
            remaining -= len(s)
            if remaining <= 0:
                break
        return "\n".join(texts)

class SearchProvider(ABC):
    """检索服务抽象基类。镜像 LLMProvider 模式。"""

    NAME: str = "abstract"
    BASE_URL: str = ""

    def __init__(self, api_key: str = "", *, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = (base_url or self.BASE_URL).rstrip("/")

    @abstractmethod
    async def search(self, query: str, depth: int = 3) -> list[SearchResult]:
        """搜索并返回结果列表。depth 控制数量。"""
        ...

    @abstractmethod
    async def extract(self, url: str) -> str:
        """下载并提取 URL 的原文内容。"""
        ...


# ── TensionBus Events ──

T = TypeVar("T")


@dataclass
class KL9Event:
    event_type: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
