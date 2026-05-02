---
name: kailejiu-memory
description: |
  KL9-RHIZOME 图原生 DualState 持久记忆层。
  每个节点是 DualState，边是 Tension。悬置替代权重归档，二重态树替代线性会话。
  由 orchestrator 调用，不单独激活。
---

# 开了玖 · KL9-RHIZOME 记忆层

## 架构定位

```
KL9-RHIZOME 认知循环:
  Phase 1: 初始化二重态 → DualState(A, B, dialogue)
  Phase 2: 递归二重折叠 → Tension 涌现 → suspension
  Phase 3: 从悬置中生成表达

kailejiu-memory 职责:
  - 持久化 Phase 2 产生的每个 DualState（节点）
  - 持久化 DualState 之间的 Tension（边）
  - 持久化会话记录 & RLHF 反馈
  - 提供 Tension 图遍历：沿边追溯折叠历史
  - suspension 状态管理（替代 v5.0 weight 衰减归档）
  - DualState 序列化/反序列化
```

## 数据库

`/AstrBot/data/skills/kailejiu-shared/storage/memory.db`

### 表结构

| 表 | 说明 |
|---|------|
| `dual_states` | DualState 节点（每次折叠一个节点） |
| `tensions` | Tension 边（两个 DualState 之间的结构性张力） |
| `sessions` | 会话记录（保留 v5.0 基础，关联 DualState 树根） |
| `feedback` | RLHF 反馈事件（保留 v5.0 基础） |
| `reading_list` | 书目检索（保留不变） |

### dual_states 表

```sql
CREATE TABLE dual_states (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id       INTEGER,              -- 父 DualState（NULL=根），形成二重态树
    session_id      TEXT,                 -- 关联会话
    query           TEXT NOT NULL,        -- 原始查询
    perspective_A   TEXT,                 -- 视角A名称（如 "temporal.human"）
    perspective_B   TEXT,                 -- 视角B名称
    dialogue_json   TEXT,                 -- activated_dialogue JSON 数组
    tension_id      INTEGER,             -- 本次折叠产生的 Tension（FK→tensions.id）
    suspended       INTEGER DEFAULT 0,    -- 0=折叠中, 1=已悬置（自然稳定）
    forced          INTEGER DEFAULT 0,    -- 是否强制悬置（达 max_fold_depth）
    fold_depth      INTEGER DEFAULT 0,    -- 折叠深度
    created_at      TEXT DEFAULT (datetime('now')),
    metadata_json   TEXT                 -- 扩展元数据
);

CREATE INDEX idx_ds_parent    ON dual_states(parent_id);
CREATE INDEX idx_ds_session   ON dual_states(session_id);
CREATE INDEX idx_ds_suspended ON dual_states(suspended);
```

### tensions 表

```sql
CREATE TABLE tensions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ds_id_A             INTEGER NOT NULL,   -- DualState A
    ds_id_B             INTEGER NOT NULL,   -- DualState B
    perspective_A       TEXT,               -- 视角A名称
    perspective_B       TEXT,               -- 视角B名称
    claim_A             TEXT,               -- A的核心论断
    claim_B             TEXT,               -- B的核心论断
    irreconcilable_json TEXT,               -- 不可调和点 JSON 数组
    tension_type        TEXT,               -- eternal_vs_finite / theoretical_vs_empirical / ...
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_tension_ds_A ON tensions(ds_id_A);
CREATE INDEX idx_tension_ds_B ON tensions(ds_id_B);
CREATE INDEX idx_tension_type ON tensions(tension_type);
```

### sessions 表（保留 v5.0，新增 ds_root_id）

```sql
CREATE TABLE sessions (
    session_id      TEXT PRIMARY KEY,
    query           TEXT,
    response        TEXT,
    concepts_used   TEXT,            -- JSON 数组
    field           TEXT,
    reasoning_type  TEXT,
    ds_root_id      INTEGER,        -- ★ 新增：关联根 DualState
    created_at      TEXT DEFAULT (datetime('now'))
);
```

### feedback 表（保留 v5.0）

```sql
CREATE TABLE feedback (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT,
    feedback_type       TEXT,         -- implicit/explicit_correct/explicit_wrong/explicit_correction
    score               REAL,
    text                TEXT,
    concepts_affected   TEXT,         -- JSON 数组
    created_at          TEXT DEFAULT (datetime('now'))
);
```

### reading_list 表（保留不变）

```sql
CREATE TABLE reading_list (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT,
    author          TEXT,
    field           TEXT,
    year            INTEGER,
    impact_note     TEXT,
    temporal_weight REAL DEFAULT 1.0
);
```

---

## 核心操作

```python
import sys
sys.path.insert(0, '/AstrBot/data/skills/kailejiu-shared/lib')
import memory as MEM
```

---

### DualState 存储（新核心 — 图原生节点）

```python
# 每次 dual_fold() 完成后，orchestrator 调用此方法持久化
ds_id = MEM.store_dual_state(
    parent_id=None,           # 父 DualState ID（None=根/新会话）
    session_id="uuid",
    query="问题文本",
    perspective_A="temporal.human",
    perspective_B="temporal.elf",
    dialogue=[
        {
            "theory": "哀悼与忧郁",
            "thinker": "弗洛伊德",
            "original_frame": "哀悼是失去对象后的心理工作",
            "transformed_frame": "精灵的哀悼不是工作而是永恒状态",
            "transformation_tension": "有限 vs 无限的哀悼",
        }
    ],
    tension={                 # 若存在张力，自动写入 tensions 表
        "perspective_A": "temporal.human",
        "perspective_B": "temporal.elf",
        "claim_A": "道德是紧迫的，必须在有限生命中完成选择",
        "claim_B": "道德是漫长的，千年尺度下善恶边界消融",
        "irreconcilable_points": [
            "时间尺度的不可通约——紧迫 vs 延迟",
            "道德判断的基础——生命有限性 vs 永恒返回",
        ],
        "tension_type": "eternal_vs_finite",
    },
    suspended=True,           # Phase 2 判定是否悬置
    forced=False,
    fold_depth=1,
)
# 返回 ds_id
# 自动行为：
#   - tension 非空 → 写入 tensions 表，建立 Tension 边
#   - parent_id 非空 → 建立二重态树父子关系
```

### DualState 检索

```python
# 按 ID 获取完整 DualState
ds = MEM.get_dual_state(ds_id)
# → {id, parent_id, session_id, query, perspective_A, perspective_B,
#    dialogue, tension, suspended, forced, fold_depth, created_at}

# 获取子 DualState（沿二重态树向下）
children = MEM.get_child_states(parent_ds_id)
# → [DualState, ...]  按 fold_depth ASC

# 按会话获取完整 DualState 链（根到所有叶子）
chain = MEM.get_session_chain(session_id)
# → [DualState, ...]  按 fold_depth ASC，树结构通过 parent_id 重建

# 获取活跃/悬置 DualState
active    = MEM.get_active_dual_states()       # suspended=0
suspended = MEM.get_suspended_dual_states()    # suspended=1
forced    = MEM.get_forced_dual_states()       # forced=1

# 获取折叠路径（从根到指定节点）
path = MEM.get_fold_path(ds_id)
# → [DualState, ...]  按 depth ASC
```

### Tension 图遍历（新核心 — 沿边查询）

```python
# 获取两个 DualState 之间的 Tension
t = MEM.get_tension_between(ds_id_A, ds_id_B)
# → Tension dict 或 None

# BFS 图遍历：从起点沿所有 Tension 边探索
subgraph = MEM.traverse_tension_graph(
    start_ds_id,
    max_depth=3,              # 最大跳数
    include_suspended=True,   # 是否包含已悬置节点
)
# → {
#     "nodes": [DualState, ...],     # 子图所有节点
#     "edges": [Tension, ...],       # 子图所有张力边
#     "start_node": DualState,
# }

# 获取指定类型的所有 Tension 边
edges = MEM.get_tensions_by_type("eternal_vs_finite")
# → [Tension, ...]

# 获取尚未悬置的活跃张力
unresolved = MEM.get_unresolved_tensions()
# → [(Tension, ds_A, ds_B), ...]  其中 ds_A.suspended=0 或 ds_B.suspended=0
```

### suspension 状态管理（替代 v5.0 weight 衰减归档）

```python
# v5.0: weight *= exp(-elapsed_days / 30); weight < 0.05 → 归档（实质删除）
# KL9-RHIZOME: suspended 标记 → 已悬置的记忆自然稳定，未悬置的自然活跃

# 悬置一个 DualState
MEM.suspend_dual_state(ds_id)
# → suspended=1（记忆"完成"，可输出，不删除）

# 重新激活（新查询使已悬置的张力再次相关）
MEM.reactivate_dual_state(ds_id)
# → suspended=0，该记忆重新进入活跃折叠

# 会话结束：批量悬置该会话所有未悬置 DualState
MEM.suspend_session_states(session_id)

# 统计
stats = MEM.get_suspension_stats()
# → {
#     "total_dual_states": 342,
#     "suspended": 289,
#     "active": 53,
#     "forced": 2,
#     "suspension_ratio": 0.845,
# }
```

**语义对照**：

| v5.0 weight 状态 | KL9-RHIZOME suspension 状态 |
|------------------|---------------------------|
| weight > 1.5（核心强概念） | suspended=0 + fold_depth >= 2（深度折叠中） |
| weight 0.8–1.5（正常） | suspended=0（活跃折叠中） |
| weight 0.3–0.8（弱化） | suspended=1（已悬置，自然稳定） |
| weight < 0.05（归档/删除） | 无对应——suspended=1 保留，永不删除 |

---

### 会话记录（保留 v5.0，关联 DualState 根）

```python
MEM.record_session(
    session_id="uuid",
    query=query,
    response=response,
    concepts_used=["规训", "生命政治"],
    field="文化研究",
    reasoning_type="chain_of_thought",
    ds_root_id=root_ds_id,       # ★ 新增：关联根 DualState
)
# 自动触发：suspend_session_states(session_id)
```

### 反馈处理（RLHF，保留 v5.0 基础）

```python
result = MEM.record_feedback(
    session_id="uuid",
    feedback_type="explicit_wrong",
    score=0.0,
    text="用户的纠正文本",
)
# → {"action": "ask_clarification", "prompt": "哪里不对？"}
```

**反馈类型对应操作**：

| 类型 | 操作 |
|------|------|
| `explicit_correct` | 关联 DualState 标记为"用户确认" |
| `explicit_wrong` | 关联 DualState 标记为"用户否定"，触发会话链重新审视 |
| `explicit_correction` | 将纠正内容创建为修正子 DualState |
| `implicit` | 仅记录，不触发状态变更 |

> v5.0 的数值 weight 调整（±0.10/0.15/0.20/0.30）已废弃。
> KL9-RHIZOME 中反馈影响的是 DualState 树结构（创建修正子节点），而非数值权重。

---

### DualState 序列化/反序列化（新增）

```python
# 导出 DualState 为可传输/可存储 dict
ds_dict = MEM.serialize_dual_state(ds_id)
# → 完整 dict，含 Perspective 特征、Tension 细节、dialogue 列表、元数据

# 从 dict 恢复
ds_id = MEM.deserialize_dual_state(ds_dict)
# → 写入 dual_states 表 + tensions 表（若含 tension），返回新 ds_id

# 批量导出/导入（JSON Lines）
dump = MEM.export_all_dual_states()
MEM.import_dual_states(dump)
```

---

### 书目检索（保留不变）

```python
books     = MEM.search_reading_list(query, top_k=3)
all_books = MEM.get_reading_list(field="文化研究", top_k=10)
```

---

## 统计

```python
stats = MEM.get_stats()
# → {
#     "dual_states": 342,
#     "tensions": 178,
#     "sessions": 89,
#     "feedback_events": 23,
#     "avg_explicit_score": 0.72,
#     "books_in_reading_list": 15,
#     "suspension_ratio": 0.845,
#     "max_fold_depth": 4,
#     "avg_fold_depth": 1.8,
# }
```

## 自动维护

| 触发条件 | 操作 |
|----------|------|
| `store_dual_state()` 含 tension | 自动写入 `tensions` 表（建立 Tension 边） |
| `store_dual_state()` 含 parent_id | 自动建立二重态树父子关系 |
| `record_session()` | 自动 `suspend_session_states(session_id)` |
| `record_feedback(type="explicit_correction")` | 自动创建修正子 DualState |
| 数据库首次创建 | 自动建所有表 + 索引 |
| `get_session_chain()` | 按 `fold_depth` 排序 |

---

## 二重态树与 Tension 图结构示意

```
session_id: "uuid-abc"
│
└── ds_1 (depth=0, suspended=False)        ← 根：原始查询的二重态
    ├── ds_2 (depth=1, suspended=False)    ← 第一次折叠
    │   ├── ds_3 (depth=2, suspended=True) ← 真悬置：张力充分展现
    │   └── ds_4 (depth=2, suspended=True, forced=True) ← 最大深度，强制悬置
    └── ds_5 (depth=1, suspended=True)     ← 另一条折叠路径，已悬置

Tension 边（跨树连接，形成图）:
  ds_2 ←→ ds_5  (tension_type="theoretical_vs_empirical")
  ds_3 ←→ ds_4  (tension_type="ideal_vs_reality")
```

每条从根到叶的路径对应一次完整的递归二重折叠尝试。同一会话可有多条路径
（A/B 视角的不同折叠分支）。Tension 边不仅存在于父子之间，也可跨分支、
跨会话连接——这正是"图原生"的含义：树结构是折叠的骨架，Tension 边是认知的脉络。

---

## v5.0 → KL9-RHIZOME 差异总览

| 维度 | v5.0 | KL9-RHIZOME |
|------|------|-------------|
| 节点类型 | concept（概念） | DualState（二重态） |
| 边类型 | parent/child/sibling（树） | Tension（结构性张力图） |
| 生命周期 | weight 指数衰减 → <0.05 归档 | suspended 标记：活跃↔悬置 |
| 会话模型 | session_id 线性时间戳链 | 二重态树（parent_id 递归） |
| 检索方式 | BM25 关键词 | Tension 图遍历 (BFS) |
| 反馈影响 | weight ±0.1~0.3 数值调整 | 创建修正子 DualState |
| 归档策略 | weight < 0.05 实质失效 | 无删除；suspended=1 保留可检索 |
| 序列化 | 无 | serialize / deserialize DualState |
| 核心表 | sessions / feedback / reading_list | + dual_states / + tensions |

---

> *KL9-RHIZOME 记忆层 v1.0 — 每个记忆都是一个不可调和的二重态，张力是边，悬置是终点，永不删除。*
