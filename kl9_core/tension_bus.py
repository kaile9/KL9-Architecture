"""
KL9-RHIZOME TensionBus — 去中心化事件总线。
所有技能通过 TensionBus 发射/订阅张力事件，无中心调度。
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable

@dataclass
class TensionBusEvent:
    session_id: str = ""
    timestamp: float = field(default_factory=time.time)

@dataclass
class QueryEvent(TensionBusEvent):
    query: str = ""

@dataclass
class InitialStateEvent(TensionBusEvent):
    state: Any = None  # DualState
    source_skill: str = "kailejiu-core"

@dataclass
class TensionEmittedEvent(TensionBusEvent):
    tension: Any = None  # Tension
    source_skill: str = ""

@dataclass
class ConceptBatchEvent(TensionBusEvent):
    concepts: List[Dict] = field(default_factory=list)
    source_skill: str = "kailejiu-graph"

@dataclass
class SoulParamsEvent(TensionBusEvent):
    params: Dict = field(default_factory=dict)
    source_skill: str = "kailejiu-soul"

@dataclass
class ResearchFindingsEvent(TensionBusEvent):
    findings: List[Dict] = field(default_factory=list)
    source_skill: str = "kailejiu-research"

@dataclass
class FoldCompleteEvent(TensionBusEvent):
    state: Any = None
    response: str = ""
    source_skill: str = "kailejiu-orchestrator"

@dataclass
class TensionSubscription:
    skill_name: str
    role: str = "subscriber"
    tension_types: List[str] = field(default_factory=list)
    event_types: List[str] = field(default_factory=list)
    priority: int = 0
    callback: Optional[Callable] = None

class TensionBus:
    """去中心化事件总线。发射即遗忘，订阅者异步响应。"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._subscriptions: Dict[str, List[TensionSubscription]] = defaultdict(list)
        self._event_buffer: Dict[str, Dict[str, List[TensionBusEvent]]] = defaultdict(lambda: defaultdict(list))
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
    
    def subscribe(self, subscription: TensionSubscription):
        for tt in subscription.tension_types:
            self._subscriptions[tt].append(subscription)
        for et in subscription.event_types:
            self._subscriptions[f"event:{et}"].append(subscription)
    
    def emit(self, event: TensionBusEvent):
        sid = getattr(event, 'session_id', 'global')
        event_type = type(event).__name__
        self._event_buffer[sid][event_type].append(event)
        
        # 1) 调用直接注册的 handlers
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception:
                pass
        
        # 2) 调用订阅者回调（匹配 event_type）
        for sub in self._subscriptions.get(f"event:{event_type}", []):
            if sub.callback:
                try:
                    sub.callback(event)
                except Exception:
                    pass
        
        # 3) 调用订阅者回调（匹配事件自身的 tension_type 字段）
        tension_type = getattr(event, 'tension_type', None)
        if tension_type:
            for sub in self._subscriptions.get(tension_type, []):
                if sub.callback and sub not in self._subscriptions.get(f"event:{event_type}", []):
                    try:
                        sub.callback(event)
                    except Exception:
                        pass
    
    def collect(self, event_types: List[str], session_id: str, timeout: float = 5.0) -> Dict[str, List[TensionBusEvent]]:
        result = {}
        for et in event_types:
            result[et] = self._event_buffer.get(session_id, {}).get(et, [])
        return result
    
    def on(self, event_type: str, handler: Callable):
        self._handlers[event_type].append(handler)
    
    def clear_session(self, session_id: str):
        if session_id in self._event_buffer:
            del self._event_buffer[session_id]

# 全局单例
bus = TensionBus()
