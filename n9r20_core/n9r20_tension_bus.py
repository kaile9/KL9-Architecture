"""
9R-2.0 RHIZOME · 9R-2.0 TensionBus
压缩感知事件总线 · 动态路由 · 去中心化 · 张力类型动态扩展
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Tuple

from core.n9r20_config import n9r20_tension_config, n9r20_routing_config


class N9R20TensionTypeRegistry:
    """
    张力类型动态注册表
    
    替代原 Enum 实现，支持运行时动态添加/删除张力类型。
    保留所有内置类型兼容。
    """
    
    def __init__(self):
        self._types: Dict[str, Dict[str, Any]] = {}
        self._builtins: set = set()
        self._init_builtins()
    
    def _init_builtins(self) -> None:
        """初始化内置张力类型"""
        for tt in n9r20_tension_config.BUILTIN_TENSION_TYPES:
            self._types[tt] = {
                "name": tt,
                "description": f"内置张力类型: {tt}",
                "builtin": True,
            }
            self._builtins.add(tt)
    
    def register(self, tension_type: str, description: str = "") -> bool:
        """
        注册新的张力类型
        
        返回 True 如果注册成功，False 如果已存在
        """
        if tension_type in self._types:
            return False
        self._types[tension_type] = {
            "name": tension_type,
            "description": description or f"自定义张力类型: {tension_type}",
            "builtin": False,
        }
        return True
    
    def unregister(self, tension_type: str) -> bool:
        """
        注销张力类型
        
        内置类型不可注销。返回 True 如果注销成功。
        """
        if tension_type in self._builtins:
            return False
        if tension_type in self._types:
            del self._types[tension_type]
            return True
        return False
    
    def get(self, tension_type: str) -> Optional[Dict[str, Any]]:
        """获取张力类型信息"""
        return self._types.get(tension_type)
    
    def list_all(self) -> List[str]:
        """列出所有张力类型"""
        return list(self._types.keys())
    
    def is_builtin(self, tension_type: str) -> bool:
        """检查是否为内置类型"""
        return tension_type in self._builtins
    
    def __contains__(self, tension_type: str) -> bool:
        return tension_type in self._types


# 全局张力类型注册表
n9r20_tension_registry = N9R20TensionTypeRegistry()


# 保留 Enum 兼容别名
class N9R20TensionType:
    """张力类型兼容类（保留旧接口）"""
    EPISTEMIC = "epistemic"
    DIALECTICAL = "dialectical"
    TEMPORAL = "temporal"
    EXISTENTIAL = "existential"
    AESTHETIC = "aesthetic"
    ETHICAL = "ethical"
    SEMANTIC = "semantic"
    
    @classmethod
    def values(cls) -> List[str]:
        return n9r20_tension_registry.list_all()


class N9R20QueryDepth:
    """查询深度"""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


@dataclass
class N9R20TensionBusEvent:
    """基础事件"""
    session_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class N9R20QueryEvent(N9R20TensionBusEvent):
    """初始查询事件"""
    query: str = ""


@dataclass
class N9R20CompressionTensionEvent(N9R20TensionBusEvent):
    """压缩感知张力事件（9R-2.0 新增）"""
    query: str = ""
    fold_depth: int = 0
    target_fold_depth: int = 4
    target_ratio: float = 2.5
    urgency: float = 0.5  # 紧急度 [0,1]
    tension_type: str = "semantic"
    compression_state: Dict = field(default_factory=dict)


@dataclass
class N9R20CompressionCompleteEvent(N9R20TensionBusEvent):
    """压缩完成事件（9R-2.0 新增）"""
    state: Any = None  # N9R20DualState
    output: str = ""
    compression_ratio: float = 1.0
    semantic_retention: float = 1.0


@dataclass
class N9R20DualPerspectiveEvent(N9R20TensionBusEvent):
    """双视角事件"""
    perspective_A: Any = None  # N9R20Perspective
    perspective_B: Any = None  # N9R20Perspective
    tension: Any = None  # N9R20Tension


@dataclass
class N9R20ConceptClusterEvent(N9R20TensionBusEvent):
    """概念簇事件"""
    concepts: List[Dict] = field(default_factory=list)
    tension_map: Dict = field(default_factory=dict)


@dataclass
class N9R20SkillBookUpdateEvent(N9R20TensionBusEvent):
    """技能书更新事件"""
    skill_name: str = ""
    book: Any = None  # N9R20SkillBook


@dataclass
class N9R20TensionSubscription:
    """张力订阅"""
    skill_name: str
    role: str = "subscriber"
    tension_types: List[str] = field(default_factory=list)
    event_types: List[str] = field(default_factory=list)
    priority: int = 0
    callback: Optional[Callable] = None


class N9R20TensionBus:
    """
    9R-2.0 TensionBus · 压缩感知事件总线
    
    核心升级：
    1. 压缩感知事件（N9R20CompressionTensionEvent / N9R20CompressionCompleteEvent）
    2. 动态优先级路由（route_by_urgency）
    3. 回退路由（fallback_route）
    4. 超时机制（collect_with_timeout）
    """
    
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
        self._subscriptions: Dict[str, List[N9R20TensionSubscription]] = defaultdict(list)
        self._event_buffer: Dict[str, Dict[str, List[N9R20TensionBusEvent]]] = defaultdict(lambda: defaultdict(list))
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._session_states: Dict[str, Dict] = defaultdict(dict)
    
    def subscribe(self, subscription: N9R20TensionSubscription):
        """订阅事件"""
        for tt in subscription.tension_types:
            self._subscriptions[tt].append(subscription)
        for et in subscription.event_types:
            self._subscriptions[f"event:{et}"].append(subscription)
    
    def emit(self, event: N9R20TensionBusEvent):
        """发射事件"""
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
    
    def collect(self, event_types: List[str], session_id: str, 
                timeout: float = 5.0) -> Dict[str, List[N9R20TensionBusEvent]]:
        """收集事件（同步等待）"""
        result = {}
        for et in event_types:
            result[et] = self._event_buffer.get(session_id, {}).get(et, [])
        return result
    
    def collect_with_timeout(self, session_id: str, 
                            timeout: float = 5.0) -> Dict[str, List[N9R20TensionBusEvent]]:
        """收集所有事件（带超时）"""
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            buffer = self._event_buffer.get(session_id, {})
            if buffer:
                return dict(buffer)
            time.sleep(0.1)
        
        return {}
    
    def on(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        self._handlers[event_type].append(handler)
    
    def clear_session(self, session_id: str):
        """清理会话"""
        if session_id in self._event_buffer:
            del self._event_buffer[session_id]
        if session_id in self._session_states:
            del self._session_states[session_id]
    
    # ═══════════════════════════════════════════
    # 9R-2.0 新增：动态路由
    # ═══════════════════════════════════════════
    
    def route_by_urgency(self, event: 'N9R20CompressionTensionEvent') -> List[str]:
        """
        根据紧急度动态调整订阅者响应顺序
        
        高紧急度：只激活核心技能
        中紧急度：激活核心 + 专用技能
        低紧急度：全技能激活
        """
        urgency = event.urgency
        
        if urgency > 0.8:
            return ["compression-core", "fold-engine"]
        elif urgency > 0.5:
            return ["compression-core", "fold-engine", "dual-reasoner"]
        else:
            return [
                "compression-core",
                "fold-engine", 
                "dual-reasoner",
                "semantic-graph",
                "memory-learner"
            ]
    
    def fallback_route(self, query: str) -> str:
        """
        回退路由：通用文本回退至标准压缩
        
        检测是否为专用文本（高概念密度）
        如果不是，回退到标准压缩路径
        """
        if self._is_specialized_text(query):
            return "specialized-compression"
        else:
            return "standard-compression"
    
    def _is_specialized_text(self, query: str) -> bool:
        """检测是否为专用文本"""
        # 使用张力配置中的专用关键词表（包含佛教/哲学/科学核心术语）
        keywords = list(n9r20_tension_config.DEFAULT_SPECIALIZED_KEYWORDS)
        
        if keywords:
            keyword_count = sum(1 for kw in keywords if kw in query)
            keyword_score = keyword_count / max(len(keywords), 1)
            
            # 概念密度检测
            from core.n9r20_utils import compute_concept_density
            concept_density = compute_concept_density(query, keywords=keywords)
            
            # 综合判断
            confidence = keyword_score * 0.4 + concept_density * 0.6
            return confidence > n9r20_routing_config.SPECIALIZED_CONFIDENCE_THRESHOLD
        
        # 无配置关键词时，使用通用概念密度检测但提高阈值
        # 避免普通文本被误判
        from core.n9r20_utils import compute_concept_density
        concept_density = compute_concept_density(query)
        
        # 同时检查是否有明显的学术/专业特征
        # 纯英文通用短文本不应触发
        has_chinese = any(ord(c) > 0x4E00 and ord(c) < 0x9FFF for c in query)
        if not has_chinese and len(query) < 50:
            return False
        
        return concept_density > 0.5  # 提高阈值
    
    def _compute_concept_density(self, query: str) -> float:
        """计算概念密度"""
        from core.n9r20_utils import compute_concept_density
        return compute_concept_density(query)


# 全局单例
n9r20_bus = N9R20TensionBus()
