---
name: kailejiu-memory
version: "2.0"
description: |
  KL9-RHIZOME v1.5 · 持久记忆层。所有记忆保持活跃，无归档门控。
  订阅 TensionBus (FoldCompleteEvent)，持续参与 DualState 构建。
  记忆检索由 tension_context 驱动而非权重排序。
---

# 开了玖 · 记忆层（KL9-RHIZOME v2.0）

## 架构声明

本模块是 KL9-RHIZOME 网状架构的**持久化记忆层**。v2 的核心跃迁：记忆不再是被动归档的离散记录，而是持续参与 DualState 构建的活体——每一条折叠历史、每一次反馈标注，都通过 TensionBus 回流到当前的认知循环中。

**核心跃迁**：

| v1.0（树状归档 + 权重门控衰减） | v2.0（图原生存储 + 张力上下文检索） |
|:---|:---|
| sessions 扁平行 + parent_state_id 外键链 | fold_nodes + fold_edges — DualState 作为图节点嵌入 |
| weight < 0.05 → 归档，不再参与检索 | 所有记忆保持活跃，检索由 tension_context 决定 |
| 指数衰减: weight(t) = w₀ × exp(-Δt/halflife) | 共振度: jaccard(tension_types) × exp(-λ×days) × fold_depth_factor |
| 时间戳记录 → 被动遗忘 | 存在论视角 → 时间通过 prior_tensions 累积间接作用 |
| 线性 session 记录 | 树状 DualState 持久化，A/B 分叉自然成图 |
| 离散权重 delta: +0.10/-0.15/-0.20 | 连续可逆折叠权重: FoldWeight + fold_history |

---

## 核心角色：记忆持久化与回流

### 定位

记忆层是 KL9-RHIZOME 的「折叠历史记录器」。不在「会话结束后」工作——而在每次 dual_fold() 期间通过 TensionBus 实时回流：过去的共振折叠经验注入下一轮折叠的 activated_dialogue，成为「记忆参考」。

```
dual_fold(state, depth)
    │
    ├── TensionBus.publish("dual_fold.completed", state)
    │       └── memory.store_dual_state(...)     # 持久化
    │
    ├── if depth > 0 and state.has_tension():
    │       TensionBus.publish("tension_type.active", state.tension)
    │           └── memory.retrieve_relevant_memories(tension_context)
    │               └── 共振记忆回流到下一轮 activated_dialogue
    │
    └── suspension 评估后:
            TensionBus.publish("suspension.assessed", assessment)
                └── memory.record_fold_feedback(...)
```

### 激活方式

```python
# v1.0: 等待「会话结束后记录」
# MEM.record_session(session_id, query, response, concepts_used, ...)

# v2.0: 订阅 TensionBus，实时参与
TensionBus.subscribe(TensionSubscription(
    skill_name="memory",
    events=[
        "dual_fold.completed",
        "suspension.assessed",
        "session.closed",
        "perspective.activeness_changed",
        "tension_type.changed",
    ],
    priority=1
))
```

---

## 核心操作

### 1. store_dual_state(session_id, state, parent_state_id, fold_depth) — 图节点持久化

**每个 DualState 作为图节点嵌入，通过边表达折叠关系。而非扁平行记录。**

```python
def store_dual_state(
    session_id: str,
    state: DualState,
    parent_state_id: Optional[str] = None,
    fold_depth: int = 0,
) -> str:
    """
    将 DualState 持久化为图节点。

    v1.0: INSERT INTO sessions (session_id, query, response, concepts_used[JSON], ...)
    v2.0:
      1. 创建 Session 节点（label="Session"）
      2. 为每个 concept 创建 DEPLOYS 边
      3. 通过 PARENT_OF 边表达父子折叠关系
      4. 通过 BRANCHED_FROM 边表达 A/B 视角分叉

    树结构不再通过 parent_state_id 外键实现，
    而通过图边 PARENT_OF 表达。
    同一个 DualState 节点可以同时是多个折叠路径的一部分——
    当 A/B 视角分叉后各自递归折叠产生不同子节点时，在图自然形成分叉。
    """
    node_id = f"session:{session_id}"

    # 存储 Session 节点
    GB.store_node(
        node_id=node_id,
        label="Session",
        name=session_id,
        tier1_def=state.query[:100],
        tier2_def=json.dumps({
            "perspective_A": state.perspective_A.name if state.perspective_A else "",
            "perspective_B": state.perspective_B.name if state.perspective_B else "",
            "fold_depth": fold_depth,
            "suspended": state.suspended,
            "forced": state.forced,
            "tension_type": state.tension.tension_type if state.tension else "",
        }),
    )

    # 创建 PARENT_OF 边
    if parent_state_id:
        GB.create_edge(
            from_id=f"session:{parent_state_id}",
            to_id=node_id,
            rel_type="PARENT_OF",
            confidence=1.0,
        )

    # 创建 DEPLOYS 边（session → concept）
    for dialogue in state.activated_dialogue or []:
        concept_name = dialogue.get("theory", "")
        concept = GB.get_concept(concept_name)
        if concept:
            GB.create_edge(
                from_id=node_id,
                to_id=concept["id"],
                rel_type="DEPLOYS",
                confidence=0.5,
            )

    return node_id
```

---

### 2. retrieve_relevant_memories(tension_context, top_k) — 张力上下文检索

**记忆的「相关与否」不由离散权重决定，而由当前 tension_type 与记忆中 tension_context 的共振程度决定。**

```python
def retrieve_relevant_memories(
    tension_context: dict,
    top_k: int = 5,
) -> List[dict]:
    """
    按张力上下文检索相关记忆。

    共振度公式：
      resonance = jaccard(tension_types_current, tension_types_memory)
                × exp(-λ × days_since_recorded)        # λ=0.05, ~14天半衰期
                × min(1.0, fold_depth / avg_fold_depth) # 深层折叠记忆权重更高

    所有记忆始终可检索——只是共振度低的记忆在无匹配张力时不浮现。
    """
    # 收集所有记忆节点
    all_memories = _get_all_fold_nodes()

    scored = []
    for mem in all_memories:
        resonance = _compute_resonance(mem, tension_context)
        if resonance > 0.05:  # 极低共振仍保留但通常不返回
            scored.append((resonance, mem))

    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored[:top_k]]
```

**共振度分量**：

| 分量 | 计算方式 | 语义 |
|:---|:---|:---|
| tension_jaccard | 当前活跃 tension 与记忆 tension 的 Jaccard 系数 | 同类型张力下的折叠经验最相关 |
| temporal_decay | exp(-0.05 × days) | ~14天半衰期，但不归零 |
| fold_depth_bonus | min(1.0, depth / avg_depth) | 深折叠 = 更丰富的张力经验 |

---

### 3. record_fold_feedback(session_id, state_id, assessment) — 折叠反馈记录

**反馈类型与 SuspensionCategory 对齐：**

| SuspensionCategory | feedback_type |
|:---|:---|
| GENUINE | genuine_suspension |
| PSEUDO | pseudo_suspension |
| NOT_SUSPENDED | insufficient_depth |

```python
def record_fold_feedback(
    session_id: str,
    state_id: str,
    assessment: SuspensionAssessment,
) -> None:
    """
    记录折叠反馈。包含完整 tension_context，
    使其可被后续折叠检索和共振匹配。

    v1.0: INSERT INTO feedback (session_id, feedback_type, score, text, ...)
    v2.0: 创建 FEEDBACK_ON 边，附加 tension_context 到边属性
    """
    # 查找 session 节点和 state 节点之间的 DEPLOYS 边
    deploy_edges = _find_deploy_edges(f"session:{session_id}")

    for edge in deploy_edges:
        # 更新边的 fold_history
        fold_event = FoldEvent(
            fold_type=assessment.category.lower(),
            delta=_assessment_to_delta(assessment),
            perspective_key=assessment.tension_type or "",
            timestamp=datetime.now().isoformat(),
        )
        _apply_fold(edge["id"], fold_event)

    # 创建 FEEDBACK_ON 边
    GB.create_edge(
        from_id=f"session:{session_id}",
        to_id=state_id,
        rel_type="FEEDBACK_ON",
        confidence=assessment.confidence or 0.5,
    )
```

---

### 4. load_session_tree(session_id) / get_fold_paths(session_id, state_id) — 折叠树加载与路径发现

```python
def load_session_tree(session_id: str) -> dict:
    """
    加载会话折叠树。保留 v1 接口。

    返回: {root_state, tree}
    树结构通过图边 PARENT_OF 和 BRANCHED_FROM 表达。
    """
    root = _get_node(f"session:{session_id}")
    tree = _traverse_children(root["id"], edge_type="PARENT_OF")
    return {"root_state": root, "tree": tree}


def get_fold_paths(session_id: str, state_id: str) -> List[List[dict]]:
    """
    图遍历——返回从根到该节点的所有可能路径（可能多条，因 A/B 分叉）。

    新增于 v2.0。因为同一个 DualState 节点可能是多个折叠路径的一部分。
    """
    return _find_all_paths(
        from_id=f"session:{session_id}",
        to_id=state_id,
        edge_types=["PARENT_OF", "BRANCHED_FROM"],
    )
```

---

### 5. 睡眠巩固（保留触发机制，语义变更）

每 100 次存储操作自动执行：

```python
def consolidate():
    """
    KL9-RHIZOME 重组：遍历所有活跃概念，基于其张力历史重新计算折叠状态。
    不删除、不衰减，只重新组织。

    v1.0: 指数衰减 + weight < 0.05 → 归档 → 死亡
    v2.0:
      1. 图压缩：沿 PARENT_OF 边检测连续 3+ 节点无实质性张力变化 → 合并为单节点
      2. TensionBus.publish("pseudo_suspension_pattern.detected", ...)
         # 不再报告给 orchestrator，而是发布到 TensionBus
      3. 更新书目 temporal_weight（保留）
      4. 清理过期共振缓存（>30 天未访问的记忆节点降冷）
    """
    # 图压缩
    redundant_chains = _detect_redundant_fold_chains()
    for chain in redundant_chains:
        _merge_chain_into_single_node(chain)

    # 发布伪悬置模式
    patterns = _detect_pseudo_suspension_patterns()
    for pattern in patterns:
        TensionBus.publish("pseudo_suspension_pattern.detected", pattern)

    # 降冷
    _cool_dormant_nodes(days_threshold=30)
```

---

## 规则

### R1: 图原生存储，消除树状关系表

旧（v1）：sessions 表（树状 DualState，parent_state_id 链）、feedback 表、reading_list 表
新（v2）：fold_nodes 表（每个 DualState 作为图节点）、fold_edges 表（节点间关系边）、feedback_records 表（增加 tension_context 字段）、reading_list 表（保留）

边类型：PARENT_OF（父子折叠）、BRANCHED_FROM（A/B视角分叉）、FEEDBACK_ON（反馈关联）、TENSION_RESONATES（张力共振）

### R2: 消除归档门控，所有记忆保持活跃

共振度公式决定浮现：
```
resonance = jaccard(tension_types_current, tension_types_memory)
          × exp(-λ × days_since_recorded)
          × min(1.0, fold_depth / avg_fold_depth)
```
所有记忆始终可检索——只是共振度低的记忆在无匹配张力时不浮现。

### R3: 记忆持续参与 DualState 构建

v2 的关键改造：memory 不再等待「会话结束后记录」，而是在每次 dual_fold() 期间通过 TensionBus 回流——过去的共振折叠经验注入下一轮折叠的 activated_dialogue。

### R4: 折叠深度反馈

反馈记录包含完整 tension_context，使其可被后续折叠检索和共振匹配。

### R5: 会话折叠树

树结构通过图边 PARENT_OF 表达，`get_fold_paths()` 返回从根到该节点的所有可能路径。

### R6: 睡眠巩固

图压缩替代归档，伪悬置模式通过 TensionBus 发布，由订阅者自行决定响应。

### R7: 书目检索（保留 v1）

```python
books = MEM.search_reading_list(query, top_k=3)
# → [{title, author, field, year, impact_note, temporal_weight, tension_affinity}, ...]
```

---

## 数据库

`<KL9-RHIZOME_DIR>/skills/kailejiu-shared/storage/memory.db`（SQLite，与 v1 兼容迁移）

v2 新增：
- `fold_edges` 表
- `tension_resonance_cache` 表
- `feedback_records.tension_context` 列

v2 schema 迁移（非破坏性 ALTER）：
```sql
ALTER TABLE edges ADD COLUMN fold_depth REAL DEFAULT 1.0;
ALTER TABLE edges ADD COLUMN fold_history TEXT DEFAULT '[]';
ALTER TABLE edges ADD COLUMN tension_type TEXT DEFAULT '';
ALTER TABLE edges ADD COLUMN reversible INTEGER DEFAULT 1;
ALTER TABLE nodes ADD COLUMN tension_activation REAL DEFAULT 0.5;
ALTER TABLE nodes ADD COLUMN dormant_since TEXT;
ALTER TABLE nodes ADD COLUMN boundary_perspective TEXT;
```

---

## 与 rhizome_engine.py 接口对齐

```
rhizome_engine.recursive_dual_fold()
  → TensionBus → memory.store_dual_state()
  → TensionBus → memory.retrieve_relevant_memories()
                # 共振记忆回流到下一轮折叠

rhizome_engine._attempt_suspension() 后的评估
  → TensionBus → memory.record_fold_feedback(assessment)

rhizome_engine.express_from_suspension()
  → memory 提供历史悬置案例作为风格参考（可选，由 tension_context 共振度决定）

assess_suspension_heuristic()
  → 其输出 SuspensionAssessment 直接对接 memory.record_fold_feedback()
```

---

## 树状结构示意（保留，边类型更新）

```
session_id: "uuid-123"
└── root_state (depth=0, tension_type=none)
    ├── fold_1 (depth=1, suspended=False)          # PARENT_OF
    │   ├── fold_1.1 (depth=2, suspended=False)    # PARENT_OF
    │   │   └── fold_1.1.1 (depth=3, suspended=True, forced=True)
    │   └── fold_1.2 (depth=2, suspended=True)     # BRANCHED_FROM (A/B分叉)
    └── fold_2 (depth=1, suspended=True)
        └── FEEDBACK_ON → pseudo_suspension        # 反馈边
```

---

*KL9-RHIZOME v2.0 — 基于 kailejiu-memory v1.0、CORE_CONCEPTS.md、rhizome_engine.py 改造*
*改造日期: 2025-07*
