# n9r20_core · 9R-2.0

N9R20Framework 核心模块。

## 模块列表

| 模块 | 功能 | 行数 |
|:---|:---|:---:|
| n9r20_structures.py | 核心数据结构：DualState, Tension, Perspective, RoutingDecision, CompressedOutput | ~120 |
| n9r20_tension_bus.py | 事件总线：发布订阅、张力路由、会话隔离 | ~60 |
| n9r20_adaptive_router.py | 自适应路由：文本类型检测、难度评估、压缩预算分配 | ~50 |
| n9r20_dual_reasoner.py | 双视角推理：A/B 同时运算、矛盾悬停 | ~40 |
| n9r20_compression_core.py | 四模压缩引擎：Construct → Deconstruct → Validate → Interrupt | ~60 |
| n9r20_semantic_graph.py | 概念图谱：术语节点管理、关系边追踪 | ~40 |
| n9r20_memory_learner.py | 记忆学习：SQLite 持久化、技能记录 | ~60 |
| n9r20_llm_evaluator.py | LLM 评估器：难度评估、fold 预算分配 | ~40 |
| version.py | 版本常量 | ~15 |
| __init__.py | 包入口 | ~30 |

总计：~535 行
