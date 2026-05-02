---
name: kailejiu-memory
description: |
  KL9-RHIZOME v3.0 · 图原生 DualState 持久化层。
  节点=DualState，边=Tension。悬置替代权重归档，二重态树+张力图替代线性会话。
  由 orchestrator 调用，不单独激活。
---

# 开了玖 · 图原生 DualState 持久化层（KL9-RHIZOME v3.0）

## 角色

图原生 DualState 持久化层。不再记录线性时间戳会话，而是以**二重态树 + Tension 图**的双重结构持久化认知状态：
- **二重态树**：每个 `dual_fold()` 产生一个 DualState 节点，`parent_id` 形成折叠树
- **Tension 图**：节点之间的结构性张力作为独立边存储，支持跨分支、跨会话的图遍历
- 睡眠巩固从会话中提取 Tension 结构而非概念关键词
- 反馈记录追踪对话式激活中理论的改造路径，同时保留 RLHF 打分兼容层

## 数据库

`/AstrBot/data/skills/kailejiu-shared/storage/memory.db`

表结构：`dual_states` / `tensions` / `transformation_log` / `feedback` / `reading_list`

### dual_states（核心节点表 — 每个 DualState 一个节点）

```sql
CREATE TABLE dual_states (
    node_id        TEXT PRIMARY KEY,        -- 节点 UUID
    session_id     TEXT NOT NULL,           -- 会话 UUID
    fold_depth     INTEGER NOT NULL,        -- 折叠层级（根=0）
    parent_id      TEXT,                    -- 父节点 UUID（根为 NULL），形成二重态树
    perspective_a  TEXT NOT NULL,           -- A 视角名称（如 "temporal.human"）
    perspective_b  TEXT NOT NULL,           -- B 视角名称
    claim_a        TEXT,                    -- A 视角核心论断
    claim_b        TEXT,                    -- B 视角核心论断
    irreconcilable_json TEXT,              -- 不可调和点（JSON 数组）
    dialogue_json  TEXT,                    -- activated_dialogue（JSON 数组）
    tension_type   TEXT NOT NULL,           -- 张力类型枚举
    suspended      INTEGER DEFAULT 0,       -- 是否已悬置（0=折叠中, 1=已悬置）
    suspension_mode TEXT,                   -- 悬置方式：ironic/juxtaposition/paradox/NULL
    forced         INTEGER DEFAULT 0,       -- 是否强制悬置
    created_at     TEXT DEFAULT (datetime('now')),
    metadata_json  TEXT,                    -- 扩展元数据
    UNIQUE(session_id, fold_depth)
);

CREATE INDEX idx_ds_parent    ON dual_states(parent_id);
CREATE INDEX idx_ds_session   ON dual_states(session_id);
CREATE INDEX idx_ds_suspended ON dual_states(suspended);
CREATE INDEX idx_ds_tension   ON dual_states(tension_type);
```

### tensions（张力边表 — 连接两个 DualState 的结构性张力）

```sql
CREATE TABLE tensions (
    edge_id         TEXT PRIMARY KEY,        -- 边 UUID
    ds_id_A         TEXT NOT NULL,           -- DualState A 的 node_id
    ds_id_B         TEXT NOT NULL,           -- DualState B 的 node_id
    perspective_A   TEXT,                    -- A 视角名称
    perspective_B   TEXT,                    -- B 视角名称
    claim_A         TEXT,                    -- A 的核心论断
    claim_B         TEXT,                    -- B 的核心论断
    irreconcilable_json TEXT,               -- 不可调和点 JSON 数组
    tension_type    TEXT NOT NULL,           -- 张力类型
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_tension_A    ON tensions(ds_id_A);
CREATE INDEX idx_tension_B    ON tensions(ds_id_B);
CREATE INDEX idx_tension_type ON tensions(tension_type);
```

### transformation_log（理论改造路径记录）

```sql
CREATE TABLE transformation_log (
    log_id         TEXT PRIMARY KEY,
    session_id     TEXT NOT NULL,
    node_id        TEXT,                    -- 关联的 fold 节点
    theory_name    TEXT NOT NULL,           -- 被激活的理论名
    original_frame TEXT NOT NULL,           -- 原始框架（结构化摘要）
    transformed_frame TEXT NOT NULL,        -- 改造后框架
    transformation_tension TEXT,            -- 改造过程中产生的张力
    activated_at   TEXT DEFAULT (datetime('now'))
);
```

### feedback（RLHF 兼容层 — 保留 v5.0 基础）

```sql
CREATE TABLE feedback (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT,
    feedback_type   TEXT,         -- implicit/explicit_correct/explicit_wrong/explicit_correction
    score           REAL,
    text            TEXT,
    concepts_affected TEXT,       -- JSON 数组
    created_at      TEXT DEFAULT (datetime('now'))
);
```

### reading_list（不变）

保留原结构：`title / author / field / year / impact_note / temporal_weight`。

---

## 核心操作

```python
import sys
sys.path.insert(0, '/AstrBot/data/skills/kailejiu-shared/lib')
import memory_v3 as MEM
```

---

### 1. DualState 节点存储

```python
# 每次 dual_fold() 完成后调用。同一 session 同 depth 存在则覆盖。
node_id = MEM.save_dual_state(
    session_id="uuid",
    dual_state={
        "fold_depth": 0,
        "parent_id": None,                 # 父节点 ID（根=None），形成二重态树
        "perspective_a": "temporal.human",
        "perspective_b": "temporal.elf",
        "claim_a": "道德是紧迫的，必须在有限生命中完成选择",
        "claim_b": "道德是漫长的，千年尺度下善恶边界消融",
        "irreconcilable_points": [
            "时间尺度的不可通约——紧迫 vs 延迟",
            "道德判断的基础——生命有限性 vs 永恒返回",
        ],
        "dialogue": [                      # activated_dialogue
            {
                "theory": "哀悼与忧郁",
                "thinker": "弗洛伊德",
                "original_frame": "哀悼是失去对象后的心理工作",
                "transformed_frame": "精灵的哀悼不是工作而是永恒状态",
                "transformation_tension": "有限 vs 无限的哀悼",
            }
        ],
        "tension_type": "eternal_vs_finite",
        "suspended": True,
        "suspension_mode": "paradox",
        "forced": False,
    }
)
# 返回 node_id
# 自动行为：
#   - 若 tension_type 非空且 parent_id 非空 → 写入 tensions 表（建立 Tension 边）
#   - 累计写入次数 % 100 == 0 → 触发睡眠巩固
```

**tension_type 枚举**（对齐 core_structures.py TENSION_TYPES）：

| 类型 | 含义 |
|------|------|
| `eternal_vs_finite` | 永恒 vs 有限（时间尺度的不可通约） |
| `mediated_vs_real` | 中介 vs 真实（存在方式的不可通约） |
| `theoretical_vs_empirical` | 理论框架与经验材料之间的不可调和 |
| `ideal_vs_reality` | 规范性理想与实然状态之间的断裂 |
| `past_vs_present` | 历史语境与当代语境之间的错位 |
| `structure_vs_agency` | 结构决定与能动性之间的永恒紧张 |
| `conflict` | 不可归入上述六类的直接冲突 |
| `resonance` | 两个视角并非冲突而是互相印证 |
| `suspended` | 继承自上一层的已悬置状态 |

**suspension_mode 枚举**：

| 模式 | 含义 |
|------|------|
| `ironic` | 反讽式悬置——承认裂隙但拒绝站队 |
| `juxtaposition` | 并置式悬置——A/B 同时在场，不做调和 |
| `paradox` | 悖论式悬置——揭示问题本身的结构性不可解 |
| `None` | 未悬置 |

---

### 2. DualState 检索 & 二重态树遍历

```python
# 按 ID 获取节点
ds = MEM.get_dual_state(node_id)

# 获取子节点
children = MEM.get_child_states(parent_node_id)
# → [DualState, ...]  按 fold_depth ASC

# 恢复会话的完整折叠路径（根→最深节点）
result = MEM.recover_dual_state(session_id="uuid")
# → {
#     "session_id": "uuid",
#     "root_node": {...},
#     "deepest_node": {...},
#     "fold_path": [{fold_depth, node_id, tension_type, suspended}, ...],
#     "total_folds": 3,
#     "final_suspended": True
# }

# 获取折叠路径（根→指定节点）
path = MEM.get_fold_path(node_id)
# → [DualState, ...]  按 depth ASC

# 活跃/悬置过滤
active    = MEM.get_active_dual_states()       # suspended=0
suspended = MEM.get_suspended_dual_states()    # suspended=1
forced    = MEM.get_forced_dual_states()       # forced=1
```

---

### 3. Tension 图遍历（图原生查询）

```python
# 获取两个节点之间的张力边
t = MEM.get_tension_between(node_id_A, node_id_B)
# → Tension dict 或 None

# BFS 图遍历：从起点沿所有 Tension 边探索（跨分支、跨会话）
subgraph = MEM.traverse_tension_graph(
    start_node_id,
    max_depth=3,              # 最大跳数
    include_suspended=True,   # 是否包含已悬置节点
)
# → {
#     "nodes": [DualState, ...],
#     "edges": [Tension, ...],
#     "start_node": DualState,
# }

# 获取指定类型的所有张力边
edges = MEM.get_tensions_by_type("eternal_vs_finite")
# → [Tension, ...]

# 获取尚未悬置的活跃张力
unresolved = MEM.get_unresolved_tensions()
# → [(Tension, ds_A, ds_B), ...]
```

---

### 4. suspension 状态管理（替代 weight 衰减归档）

```python
# v5.0: weight < 0.05 → 归档删除
# v3.0: suspended 标记 → 已悬置自然稳定，未悬置自然活跃，永不删除

# 悬置
MEM.suspend_dual_state(node_id, mode="paradox")
# → suspended=1, suspension_mode="paradox"

# 重新激活（新查询使已悬置张力再次相关）
MEM.reactivate_dual_state(node_id)
# → suspended=0, suspension_mode=NULL

# 会话结束：批量悬置
MEM.suspend_session_states(session_id)

# 统计
stats = MEM.get_suspension_stats()
# → {total, suspended, active, forced, suspension_ratio}
```

**语义对照**：

| v5.0 weight | v3.0 suspension |
|-------------|-----------------|
| weight > 1.5（核心） | suspended=0 + fold_depth >= 2（深度折叠中） |
| weight 0.8–1.5（正常） | suspended=0（活跃折叠中） |
| weight 0.3–0.8（弱化） | suspended=1（已悬置，自然稳定） |
| weight < 0.05（归档） | 无对应——suspended=1 保留，永不删除 |

---

### 5. Tension 提取（睡眠巩固核心）

从 session 的所有 fold 节点中提取跨层级的张力结构。

```python
tensions = MEM.extract_tensions_from_session(session_id="uuid")
# → {
#     "session_id": "uuid",
#     "primary_tension": {
#         "type": "eternal_vs_finite",
#         "claim_a": "...",
#         "claim_b": "...",
#         "depth_reached": 3
#     },
#     "tension_lineage": [
#         {"depth": 0, "type": "ideal_vs_reality"},
#         {"depth": 1, "type": "eternal_vs_finite"},
#     ],
#     "suspension_chain": [
#         {"depth": 2, "mode": "paradox", "node_id": "..."},
#     ],
#     "forced_count": 1,
#     "total_folds": 3
# }
```

---

### 6. 理论改造路径记录（替代 RLHF 评分）

```python
MEM.record_transformation(
    session_id="uuid",
    node_id="node-uuid",
    transformation={
        "theory_name": "福柯的生命政治",
        "original_frame": "生命权力对身体的规训与管理",
        "transformed_frame": "在数字平台语境下，生命权力从'使人活'转为'使数据活'",
        "transformation_tension": "historical vs contemporary",
    }
)
# 无分数，无权重的调整
# 仅记录理论在对话语境中被如何改造、产生了何种张力
```

---

### 7. RLHF 反馈（兼容层 — 保留 v5.0 接口）

```python
result = MEM.record_feedback(
    session_id="uuid",
    feedback_type="explicit_wrong",
    score=0.0,
    text="用户的纠正文本",
)
# → {"action": "ask_clarification", "prompt": "哪里不对？"}
# 内部映射：
#   explicit_correct → 标记关联 DualState 为"用户确认"
#   explicit_wrong   → 标记关联 DualState 为"用户否定"
#   explicit_correction → 创建修正子 DualState
```

> v5.0 的 weight ±0.1~0.3 数值调整已完全废弃。v3.0 中反馈影响 DualState 树结构，而非数值权重。

---

### 8. DualState 序列化/反序列化（新增）

```python
# 导出单个 DualState（含关联 Tension、dialogue）
ds_dict = MEM.serialize_dual_state(node_id)
# → 完整 dict，含 Perspective 特征、Tension 细节、dialogue 列表

# 从 dict 恢复（含自动写入 tensions 表）
new_id = MEM.deserialize_dual_state(ds_dict)

# 批量导出 / 导入（JSON Lines）
dump = MEM.export_all_dual_states()
MEM.import_dual_states(dump)
```

---

### 9. 书目检索（不变）

```python
books     = MEM.search_reading_list(query, top_k=3)
all_books = MEM.get_reading_list(field="文化研究", top_k=10)
```

---

## 睡眠巩固（自动触发）

每 100 次 `save_dual_state` 写入自动执行。

| 维度 | v1.0 | v2.0 | v3.0 |
|:---|:---|:---|:---|
| 巩固对象 | 概念关键词 weight | Tension 结构 | Tension 结构 + 张力边图 |
| 衰减机制 | `weight *= exp(-days/30)` | 30天未引用→归档 | 30天未引用→归档到 `dual_state_archive` |
| 归档条件 | `weight < 0.05` | 孤立节点归档 | 孤立节点归档（无子 + 无 Tension 边连接） |
| 强化机制 | 高频概念 weight↑ | 跨 session 同类张力→ recurrent_tension | 同左 + 张力图聚类 |
| 输出物 | 无 | consolidation_report | consolidation_report + 张力图统计 |

```python
# 自动执行，无需手动调用
# 内部逻辑：
#   1. 归档：孤立节点（无子节点 + 无 Tension 边 + 30天未引用）→ archive
#   2. 检测：跨 session 重复出现的同类张力 → recurrent_tension 模式
#   3. 聚类：Tension 图中连通分量统计
#   4. 报告：本轮归档数、复现张力模式、活跃 session 数
```

---

## 二重态树 + Tension 图结构示意

```
session_id: "uuid-abc"
│
└── ds_1 (depth=0, suspended=False)          ← 根：原始查询的二重态
    ├── ds_2 (depth=1, suspended=False)      ← 第一次折叠
    │   ├── ds_3 (depth=2, suspended=True)   ← 真悬置：张力充分展现
    │   └── ds_4 (depth=2, suspended=True, forced=True) ← 最大深度强制悬置
    └── ds_5 (depth=1, suspended=True)       ← 另一条折叠路径

Tension 边（独立 tensions 表，跨树连接形成图）:
  ds_2 ←→ ds_5  (tension_type="theoretical_vs_empirical")
  ds_3 ←→ ds_4  (tension_type="ideal_vs_reality")
  ds_1 ←→ ds_X  (跨 session 连接，tension_type="past_vs_present")
```

每条从根到叶的路径是一次完整的递归二重折叠。Tension 边不仅存在于父子之间，
也可跨分支、跨会话连接——这就是"图原生"的含义。

---

## 统计

```python
stats = MEM.get_stats()
# → {
#     "active_nodes": 247,
#     "archived_nodes": 89,
#     "active_sessions": 53,
#     "total_tensions": 178,             # Tension 边总数
#     "transformations_logged": 128,
#     "feedback_events": 23,             # RLHF 兼容层
#     "recurrent_tension_patterns": 3,
#     "suspension_ratio": 0.845,
#     "max_fold_depth": 4,
#     "avg_fold_depth": 1.8,
#     "books_in_reading_list": 42,
#     "last_consolidation": "2026-05-02T14:30:00Z",
# }
```

## 自动维护

| 触发条件 | 操作 |
|----------|------|
| `save_dual_state()` 含 tension_type + parent_id | 自动写入 `tensions` 表 |
| `save_dual_state()` 含 parent_id | 自动建立二重态树父子关系 |
| `save_dual_state()` 累计 % 100 == 0 | 触发睡眠巩固 |
| `record_feedback(type="explicit_correction")` | 创建修正子 DualState |
| `suspend_session_states()` | 批量悬置会话所有未悬置节点 |
| `deserialize_dual_state()` | 自动重建 tensions 边 |

---

## v5.0 → KL9-RHIZOME v3.0 差异总览

| 维度 | v5.0 | v3.0 |
|------|------|------|
| 节点类型 | concept（概念） | DualState（二重态） |
| 边类型 | parent/child/sibling（树） | Tension（结构性张力图，独立 tensions 表） |
| 生命周期 | weight 指数衰减 → <0.05 归档 | suspended 标记 + 孤立节点归档 |
| 会话模型 | session_id 线性时间戳链 | 二重态树（parent_id）+ Tension 图 |
| 检索方式 | BM25 关键词 | Tension 图遍历 (BFS) + 树遍历 |
| 反馈影响 | weight ±0.1~0.3 数值调整 | 创建修正子 DualState + RLHF 兼容层 |
| 归档策略 | weight < 0.05 实质失效 | 孤立节点归档；suspended=1 保留可检索 |
| 序列化 | 无 | serialize / deserialize / export / import |
| 核心表 | sessions/feedback/reading_list | dual_states/tensions/transformation_log/feedback/reading_list |

---

> *KL9-RHIZOME v3.0 — 节点是二重态，边是张力，悬置是终点，图是记忆的本体。永不删除。*
