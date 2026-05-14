# kailejiu-shared — KL9-RHIZOME v1.5 共享基础设施层

> 所属架构：KL9-RHIZOME v1.5（TensionBus 事件驱动 + dual_fold 递归二重折叠）
> 角色定位：基础设施层 —— 提供所有技能共用的核心数据结构、TensionBus、图谱/记忆/学习后端

---

## v1.5 核心模块

| 模块 | 状态 | 说明 |
|------|------|------|
| `lib/tension_bus.py` | ✅ v1.5 | 去中心化事件总线，单例模式 |
| `lib/core_structures.py` | ✅ v1.5 | DualState / Tension / Perspective / SuspensionAssessment |
| `lib/dual_fold.py` | ✅ v1.5 | 递归二重折叠引擎 + TOKEN_PRESSURE 监控 |
| `lib/suspension_evaluator.py` | ✅ v1.5 | 悬置评估 + TEMPORAL 压力放宽 |
| `lib/constitutional_dna.py` | ✅ v1.5 | 宪政五原则 + 硬约束审查 |
| `lib/perspective_types.py` | ✅ v1.5 | 6 大视角类别 + 6 种张力类型 + 推荐二重组合 |
| `lib/emergent_style.py` | ✅ v1.5 | 张力类型 → 涌现风格映射 |
| `lib/fold_depth_policy.py` | ✅ v1.5 | 动态折叠深度策略 + token 预估 |
| `lib/graph_backend.py` | ✅ v1.5 | dialogical_retrieval（张力共振）+ genealogy 谱系边 + BM25 fallback |
| `lib/memory.py` | ✅ v1.5 | record_dual_session + inject_session_metadata |
| `lib/learner.py` | ✅ v1.5 源码 | RLHF + curriculum learning + synthetic query generation（.pyc→源码重构） |
| `lib/memory.py` | ✅ RHIZOME v1.0 | 持久记忆后端，会话/反馈/书目/睡眠巩固，对接 DualState 快照。v1.5 新增 `inject_session_metadata()` 注入轻量元数据（学习摘要、张力漂移）不触发 LLM。 |
| `lib/learner.py` | ✅ RHIZOME v1.0 | 迭代学习后端，RLHF/课程学习/合成查询，权重更新写入 memory.db |
| `lib/reasoner.py` | ✅ RHIZOME v1.0 | 推理策略后端，意图分类/CoT/自我反思，视角转换时策略选择 |

---

## v1.5 新增接口

### inject_session_metadata（memory.py）

```python
def inject_session_metadata(session_id: str, metadata: dict):
    """
    向会话记录注入轻量元数据，不触发 LLM。

    由 orchestrator 在每次会话结束时调用（Phase 5.5），
    注入内容包括：
      - lean_summary: 来自 learner.get_lean_summary() 的学习摘要
      - tension_drift: 各张力类型的折叠深度趋势

    零 token 开销——纯数据写入，不经过 LLM 处理。
    元数据附加在 memory.db 的 session 记录中，供后续 learner 分析使用。
    """
```

---

## 职责

kailejiu-shared 是 KL9-RHIZOME 架构的**共享基础设施层**。不直接处理用户请求，而是为其他 8 个活跃技能提供：

1. **核心数据结构** — `core_structures.py`（DualState / Tension / Perspective）
2. **视角类型库** — `perspective_types.py`（6大视角类别 + 6种张力类型 + 4种涌现风格）
3. **二重折叠引擎** — `dual_fold.py`（递归折叠/展开策略，Phase 2 核心）
4. **运行时引擎** — `rhizome_engine.py`（KL9Rhizome 三阶段主引擎）
5. **后端库** — `lib/`（graph_backend.py / memory.py / reasoner.py / learner.py）
6. **持久化存储** — `storage/`（graph.db / memory.db）

---

## 导入路径速查

```python
# 核心数据结构
from core_structures import DualState, Tension, Perspective

# 视角与张力类型库
from perspective_types import (
    PERSPECTIVE_TYPES,        # 6大视角：temporal / existential / social / political / economic_grotesque / truth_construction
    TENSION_TYPES,            # 6种张力（含涌现风格指导）
    RECOMMENDED_DUALITIES,    # 7组推荐二重组合
    EMERGENT_STYLE_MAP,       # 4种涌现风格
)

# 二重折叠引擎
from dual_fold import (
    DualFoldEngine,           # 递归二重折叠/展开
    fold,                     # 折叠操作：A ∪ B → suspended
    unfold,                   # 展开操作：suspended → expressed
    FoldStrategy,             # 折叠策略枚举
)

# 视角注册表（供 research 技能注入候选概念）
from perspective_registry import (
    PerspectiveRegistry,
    register_candidate,
    map_to_perspective_type,
)

# 运行时主引擎
from rhizome_engine import KL9Rhizome

# 后端库
from lib.graph_backend import GraphBackend
from lib.memory import MemoryBackend
from lib.reasoner import ReasoningBackend
from lib.learner import LearningBackend
```

---

## 架构映射

```
KL9-RHIZOME 递归二重折叠
├── rhizome_engine.py          ← 运行时主引擎
│   ├── Phase 1: initialize_dual_state()
│   ├── Phase 2: recursive_dual_fold()   ← 调用 dual_fold.py
│   └── Phase 3: express_from_suspension()
├── dual_fold.py               ← 二重折叠引擎（RHIZOME v1.0 新增）
│   ├── DualFoldEngine         ← 折叠/展开调度
│   ├── fold()                 ← A/B → suspended
│   ├── unfold()               ← suspended → expressed
│   └── FoldStrategy           ← 策略枚举
├── core_structures.py         ← 核心数据类
│   ├── DualState              ← 二重态（A/B 平等不可调和）
│   ├── Tension                ← 结构性张力
│   └── Perspective            ← 认知视角
├── perspective_types.py       ← 视角与张力类型库
│   ├── PERSPECTIVE_TYPES      ← 6大视角（temporal/existential/social/political/economic_grotesque/truth_construction）
│   ├── TENSION_TYPES          ← 6种张力（含涌现风格指导）
│   ├── RECOMMENDED_DUALITIES  ← 7组推荐二重组合
│   └── EMERGENT_STYLE_MAP     ← 4种涌现风格
├── perspective_registry.py    ← 视角注册表（RHIZOME v1.0 新增）
│   ├── register_candidate()   ← 研究代理注入候选概念
│   └── map_to_perspective_type() ← 概念→视角类别映射
├── lib/
│   ├── graph_backend.py       ← 知识图谱后端（BM25检索 + subgraph遍历）
│   ├── memory.py              ← 持久记忆后端（会话/反馈/书目/睡眠巩固）
│   ├── reasoner.py            ← 推理策略后端（意图分类/CoT/自我反思）
│   └── learner.py             ← 迭代学习后端（RLHF/课程学习/合成查询）
└── storage/
    ├── graph.db               ← 概念知识图谱数据库
    └── memory.db              ← 会话记忆数据库
```

---

## 与其他技能的关系

| 技能 | 调用方式 |
|------|---------|
| kailejiu-orchestrator | 主入口：调用 `KL9Rhizome.respond(query)` |
| kailejiu-graph | 被 orchestrator 通过 `graph_backend.py` 调用 |
| kailejiu-memory | 被 orchestrator 通过 `memory.py` 调用 |
| kailejiu-reasoner | 视角转换时通过 `reasoner.py` 的策略选择 |
| kailejiu-learner | 宪法批判后通过 `learner.py` 更新权重 |
| kailejiu-research | 新概念发现后写入 graph.db + 注入 `perspective_registry` |
| kailejiu-core | 宪法DNA 由 `rhizome_engine.py._build_constitutional_dna()` 提供 |
| kailejiu-soul | 涌现风格由 `TENSION_TYPES[].emergent_style` 提供 |

---

## 设计原则

1. **纯数据容器** — 数据结构不含业务逻辑，仅提供基础方法和 prompt 构建辅助
2. **二重性本质** — A 和 B 平等且不可调和，这不是 bug 而是 feature
3. **悬置优先** — suspended=True 才输出，forced=True 是例外
4. **张力 ≠ 矛盾** — 张力是存在方式的裂痕，不是可解决的命题对立
5. **不可通约** — 视角间不可还原，保持各自的认知完整性
6. **递归折叠** — `dual_fold.py` 支持嵌套折叠，每一层保持 A/B 对称性

---

## 版本历史

- v1.0 (2026-05-02): 初始版本，随 KL9-RHIZOME 架构一并发布
  - 新增 `dual_fold.py` 二重折叠引擎
  - 新增 `perspective_registry.py` 视角注册表
  - `bootstrap.py` / `graph_backend` / `memory` / `learner` / `reasoner` 全部升级至 RHIZOME 兼容
- 前身：kailejiu v5.0 五层架构 → 已被 KL9-RHIZOME 取代
