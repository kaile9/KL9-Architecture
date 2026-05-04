---
name: kailejiu-graph
version: "3.0"
description: |
  KL9-RHIZOME v1.5 · 概念知识图谱层。
  dialogical_retrieval 以张力共振替代 BM25 相关性排序，
  支持 genealogy 谱系边写入与查询，同名变体碰撞，张力场路由。
  订阅 TensionBus (EPISTEMIC)，可独立多入口激活。
---

# 开了玖 · 图谱层（KL9-RHIZOME v3.0）

## role

概念知识图谱的图原生贮存与检索层。以 perspective_types.py 中的视角类型为根节点，以张力（Tension）为边涌现机制——边类型不预设，从 DualState 的 tension_type 与 irreconcilable_points 中自然结晶。无固定 tier 层级，概念以图节点形式存贮，定义深度由连接密度决定。

**核心隐喻跃迁 v2→v3**：从「对话式检索：让理论在张力的重力场中自行浮现」→「张力共振候选池：每个理论因其与 query 上下文的张力谐振强度而被推入候选池——而非因其关键词匹配得分」。

## trigger

### TensionBus 订阅

| 订阅信号 | 触发操作 | 说明 |
|:---|:---|:---|
| `tension_type` 变更 | `dialogical_retrieval(query, tension_context)` | 带张力上下文检索候选理论 |
| `DualState.activated_dialogue` 为空 | `dialogical_retrieval(query, tension_context)` | 首次初始化对话激活 |
| `perspective_A/B` 确定 | `get_perspective_connections(A, B)` | 发现视角间隐藏连接 |
| `new_concept` 事件 | `store_concept(...)` | research 模块写入新概念 |
| `new_edge` 事件 | `create_edge(...)` | 关系边从张力中结晶 |
| `dual_fold.phase2_enter` | `dialogical_retrieval(...)` | Phase 2 递归折叠前刷新候选池 |
| `DualState.suspended=True` | `get_bridge_concepts(tension_type)` | 悬置态提供桥接概念 |

### 独立入口

- `/graph search <query>`：对话式检索
- `/graph connect <A> <B>`：视角连接发现
- `/graph variants <concept>`：同名变体碰撞
- `/graph stats`：图谱状态
- `/graph bridges <tension_type>`：悬置态桥接概念查询

### 静默条件

- 简单事实查询 / 寒暄 → 不激活
- `suspended=True` 且非钻研模式 → 低权重激活（仅提供桥接概念，不触发完整检索）

## rules

### R1: 图原生存贮，无固定层级

旧（v1）：tier1 (5-10字) / tier2 (20-30字框架) / tier3 (完整定义)
新（v2+）：节点属性 {name, thinker, work, field, definition, tension_types[], connected_perspectives[]}

概念的定义深度不由 tier 编号决定，而由图连接密度决定——被更多视角引用的概念自然获得更丰富的展开。expand_definition() 仍可用但语义变为「沿连接边收集相邻节点描述」，不再按固定层级裁切。

### R2: 边类型从张力中涌出——运行时创建

不预设 EXTENDS / CONTRADICTS / CRITIQUES / APPLIES_TO / INFLUENCED_BY。边类型从 DualState 的 tension_type 和 irreconcilable_points 中动态生成：

```
DualState.tension_type="eternal_vs_finite"
  → 边类型: "temporal_incommensurability"

irreconcilable_points=["时间尺度的不可通约", "哀悼的本质差异"]
  → 边标签: "irreconcilable_on:time_scale", "irreconcilable_on:mourning_nature"
```

现有 v1 的 95 条边在首次加载时自动迁移：根据已有 tension_type 映射为开放边标签。

| v1 旧边类型 | v2+ 开放边标签（示例） |
|:---|:---|
| EXTENDS | frame_modified_by:{tension_type} |
| CONTRADICTS | irreconcilable:{tension_type} |
| CRITIQUES | structural_critique_from:{perspective} |
| APPLIES_TO | frame_transplant:{domain} |
| INFLUENCED_BY | genealogy:{thinker_A}→{thinker_B} |

**v3 新增**：以上仅为 v1→v2 的历史映射。v3 中边标签完全在运行时从张力中涌现——当新的 tension_type 或 irreconcilable_point 首次出现时，`create_edge()` 自动生成新标签并写入 `edge_labels` 表。无上限，无边类型枚举，图谱随张力生长。例如：某次对话涌现 `tension_type="visibility_vs_erasure"` → 自动创建边标签 `"irreconcilable:visibility_vs_erasure"` → 下次复用。

### R3: 对话式检索——张力共振候选池

旧: `GB.search_concepts_bm25(query, top_k=6)`
新: `GB.dialogical_retrieval(query, tension_context, top_k=6)` → `CandidatePool`

旧: `GB.build_activation_context(query, A, B, ...)`
新: `GB.retrieve_with_tension(query, dual_state, top_k=6)`

**核心语义重构**：候选池不是「搜索结果」，而是「理论的对话场」。

1. 接收 query + tension_context（从 TensionBus 获取当前 DualState 的 tension）
2. **张力共振评分**：候选理论不按 BM25 相关性排序，而按「该理论框架与当前 query 上下文的张力谐振强度」推入候选池——衡量「该理论介入后能产生多少生产性张力」，而非「有多相关」
3. 有 tension 时：偏好检索与 irreconcilable_points 语义相近的理论——天然与当前不可调和结构共振
4. 无 tension 时（首次初始化）：关键词匹配作为初始种子，标注 `resonance_source="keyword_fallback"`
5. 返回候选理论池——不做最终输出决策，交付给 dialogue_activator

```python
def dialogical_retrieval(
    query: str,
    tension_context: Optional[TensionContext],
    top_k: int = 6,
) -> CandidatePool:
    """
    v3: 张力共振候选池。
    候选理论按「tension_resonance」排序——每个理论与 query 上下文的张力谐振强度。

    CandidatePool:
      candidates: [
        {concept_id, name, thinker, definition,
         tension_resonance: float,     # 张力谐振强度
         resonance_source: str,        # "tension_field"|"irreconcilable_match"|"keyword_fallback"
         frame_tension: str,           # 该理论与 query 之间的预估张力类型
         genealogy_trace: [            # v1.5 新增：该概念的谱系漂移路径
           {"from_concept": "原始概念名", "to_concept": "改造后概念名",
            "drift_type": "extension", "edge_label": "genealogy:extension"}
         ]},
        ...]
      pool_signature: str              # 候选池整体张力特征摘要
    """
```

| 维度 | v2 (dialogue-biased) | v3 (tension resonance) |
|:---|:---|:---|
| 排序依据 | 偏好 irreconcilable_points 近邻 | 张力谐振强度——理论的框架与 query 之间的生产性张力 |
| 候选性质 | 「这些理论可能相关」 | 「这些理论在当前张力场中处于共振态」 |
| 交付方式 | 候选列表 | CandidatePool（含 pool_signature） |
| 空 tension | BM25 关键词匹配 | 关键词匹配 + `resonance_source="keyword_fallback"` |

### R4: 视角导航——沿张力边遍历

旧: `GB.get_subgraph(concept)` → 「还有什么相关？」（知识扩展）
新: `GB.get_perspective_connections(A, B, max_hops=3)` → 「A和B在何处不可通约？」（张力路径发现）

### Perspective Navigation (R4 deepened)

`get_perspective_connections(A, B)` 的本质是**沿 emergent tension 边遍历**——不在图数据库中执行预定义路径查询，而是在运行时的张力拓扑中导航：

```python
def get_perspective_connections(
    perspective_a: str,
    perspective_b: str,
    max_hops: int = 3,
    tension_filter: Optional[List[str]] = None,
    include_genealogy: bool = False,  # v1.5 新增：是否在返回路径中包含 genealogy 边
) -> PerspectiveNavigation:
    """
    v3: 视角导航。从 A 出发，沿有张力标记的边向 B 方向遍历。
    每一步选择「张力梯度最大」的出边——即该边关联的 tension_type 与
    当前 DualState.tension_type 共振最强的方向。

    PerspectiveNavigation:
      paths: [{nodes, edges, connecting_tension, tension_gradient: float}, ...]
      bridge_concepts: [concept_id, ...]
      structural_holes: [{from_concept, to_concept, expected_tension, confidence}, ...]
      navigation_summary: str           # 导航路径的整体张力拓扑描述
      genealogy_paths: [...]            # v1.5 新增：include_genealogy=True 时包含的谱系漂移路径
    """
```

遍历策略：
1. 从 A 和 B 同时出发做双向 BFS，每步选张力梯度最大的出边
2. 边权重 = `tension_resonance(edge.tension_type, current_dual_state.tension_type)`——动态权重，非静态图结构
3. A→B 路径在 max_hops 内交汇 → 记录交汇节点为 bridge_concept
4. 无法交汇 → 记录最近未连接对为 structural_hole
5. 返回路径带 `tension_gradient` 字段，供 reasoner 判断沿此路径展开对话的认知张裂程度

**v3 关键跃迁**：路径不是预存的——每次导航在当前的张力场中即时计算。同一 A-B 对在不同 tension_type 下返回不同路径，因为边权重随张力上下文动态变化。

## Phase 2 Integration

图谱检索结果直接注入 Phase 2 递归二重折叠循环。

### 数据流

```
TensionBus: DUAL_FOLD_PHASE2_ENTER
  → graph.dialogical_retrieval(query, tension_context) → CandidatePool
       │
       ├──→ dialogue_activator.activate(pool) → DualState.activated_dialogue
       │
       └──→ reasoner.transform_from_theoretical_perspective() → DualState.tension
                  │
                  └──→ dual_fold.iterate(state) ← 递归折叠
                           │
                           ├── suspended=True → graph.get_bridge_concepts()
                           │                         │
                           │                         └──→ 补充桥接概念到 DualState
                           │
                           └──→ emergent_style.generate(state)
```

### 关键集成点

1. **候选池注入**：CandidatePool → `dialogue_activator.activate()` → 选出两到三个「张力共振最强的理论对」→ `DualState.activated_dialogue`
2. **张力场更新**：每次 `dual_fold.iterate()` 后 tension 可能演化（tension_type 不变但 irreconcilable_points 细化）。图谱层订阅此变更，在下一轮迭代前刷新候选池——理论在对话中沉降或上浮
3. **深度联动**：fold_depth 越大，top_k 线性增长（depth=1 → 4, depth=5 → 12），更深的折叠需要更广的张力候选池来维持认知张裂

```python
# Phase 2 循环中的图谱调用
state = core.dialogical_activation(query)

for fold in range(state.fold_depth):
    pool = graph.dialogical_retrieval(query, state.tension, top_k=4 + fold * 2)
    state.activated_dialogue = dialogue_activator.activate(pool)
    state = reasoner.transform_from_theoretical_perspective(state)
    state = dual_fold.iterate(state)

    if state.suspended:
        state.bridge_concepts = graph.get_bridge_concepts(state.tension.tension_type)
        break
```

## Suspension Support

当 `DualState.suspended=True`——递归折叠达到「不可调和性已被充分表达」——图谱层从「张力共振检索」切换为「桥接概念提供」。

### 桥接概念

```python
def get_bridge_concepts(
    tension_type: str,
    min_confidence: float = 0.6
) -> List[BridgeConcept]:
    """
    v3: 悬置态桥接概念查询。

    当对话达到悬置态（张力被保持为张力，不寻求缝合），
    图谱提供「桥接概念」——同时被张力两侧视角引用，
    但两侧理解存在不可调和分歧的概念。

    桥接概念不是「中间道路」——它是张力被最精确地定位的地方。

    返回:
      [{concept_id, name,
        perspective_a_interpretation, perspective_b_interpretation,
        divergence_point, productive_tension, bridge_confidence}, ...]
    """
```

### 桥接 ≠ 缝合

- 不返回「A 和 B 都同意 X」的共识概念（那是缝合）
- 返回「A 和 B 都讨论 X，但对 X 的理解根本不同」的分歧概念（那是桥接）
- 桥接概念标记了张力最尖锐的位置——「这里，就在这里，两种视角无法通约」

悬置态表达中嵌入桥接概念：「X 正是两种视角共同锚定却无法通约的概念——A 视之为 Y，B 视之为 Z。张力的全部重量落在此处。」

## R5: 同名变体碰撞（保留 v1 行为，对齐 rhizome_engine）

```python
variants = GB.find_same_name_variants(concept_name)
# → [{thinker, definition, perspective_affinity, tension_types}, ...]
# 新增 perspective_affinity: 该变体与哪些视角亲和
# 新增 tension_types: 该变体与同名其他变体之间的张力类型
```

## R6: 图写入（供 research 和 learner 模块使用）

```python
# 存贮新概念（无 tier 参数）
node_id = GB.store_concept(
    name="例外状态",
    definition="阿甘本：法律以自身的悬置来包容裸命，例外成为规则",
    thinker="阿甘本", work="例外状态", field="政治学",
    perspective_affinity=["political.freedom_focused", "political.security_focused"],
    tension_types=["freedom_vs_security"]
)

# 创建关系边（边类型为开放标签，v3：运行时自动生成新标签）
GB.create_edge(
    from_id=node_id_a, to_id=node_id_b,
    edge_label="irreconcilable:sovereignty_origin",  # 可为从未出现的新标签
    tension_source="eternal_vs_finite", confidence=0.8,
)
# v3: 若 edge_label 不在 edge_labels 表中，自动 INSERT 并记录首次出现的
# tension_source 和时间戳。后续相同标签直接复用。

# v1.5 新增：谱系边写入（记录概念在对话式激活中的语义漂移路径）
GB.create_genealogy_edge(
    from_id=original_concept_id,    # 原始概念节点ID
    to_id=transformed_concept_id,   # 改造后概念节点ID
    drift_type="extension",         # "extension" | "distortion" | "inversion"
    transformation_context=query,   # 触发改造的 query 上下文
    transformation_tension=tension, # 改造过程中产生的张力描述
)
```

### R6.1: 谱系边（Genealogy Edge）

```python
def create_genealogy_edge(
    from_id: str,           # 原始概念节点ID
    to_id: str,             # 改造后概念节点ID
    drift_type: str,        # "extension" | "distortion" | "inversion"
    transformation_context: str,  # 触发改造的 query 上下文
    transformation_tension: str,  # 改造过程中产生的张力描述
):
    """
    记录概念在对话式激活中的语义漂移路径。

    谱系边属于开放性标签，运行时自动创建。
    标签格式: "genealogy:{drift_type}:{short_context_hash}"

    drift_type 语义：
      - "extension"   — 原始框架被扩展到新语境，核心结构保留
      - "distortion"  — 原始框架在新语境中被显著拉伸，部分预设被替换
      - "inversion"   — 原始框架的论证方向被反转

    谱系边不同于 irreconcilable 边——它不标记不可调和点，
    而是记录「概念如何在对话压力下变形」的演化轨迹。
    """
    import hashlib, time
    short_hash = hashlib.md5(transformation_context[:80].encode()).hexdigest()[:8]
    edge_label = f"genealogy:{drift_type}:{short_hash}"

    GB.create_edge(
        from_id=from_id,
        to_id=to_id,
        edge_label=edge_label,
        tension_source="intellectual_history",
        confidence=0.7,
        metadata={
            "drift_type": drift_type,
            "transformation_context": transformation_context[:200],
            "transformation_tension": transformation_tension[:200],
            "timestamp": time.time()
        }
    )
```

## 数据库

`<KL9-RHIZOME_DIR>/skills/kailejiu-shared/storage/graph.db`（SQLite，与 v1 兼容）

v3 新增/变更表：
- `edge_labels`：所有已涌现的开放边标签及其首次出现的张力上下文和时间戳
- `tension_resonance_cache`：缓存 (concept_id × tension_type) 的谐振强度
- `bridge_concept_index`：预计算各 tension_type 下的桥接概念索引

## 与 rhizome_engine.py 接口对齐

```
rhizome_engine._dialogical_activation()
  → graph.dialogical_retrieval(query, tension_context)     # v3: 返回 CandidatePool

rhizome_engine._classify_tension_type()
  → graph.get_perspective_connections(pa_name, pb_name)    # v3: 返回 PerspectiveNavigation

rhizome_engine._find_irreconcilable_points()
  → graph.find_same_name_variants()                        # 同名概念的不同解释 = 不可通约点的种子

rhizome_engine._phase2_iterate()                           # v3 新增
  → graph.dialogical_retrieval(query, evolved_tension)     # 每轮迭代用最新 tension 刷新候选池

rhizome_engine._suspension_resolve()                       # v3 新增
  → graph.get_bridge_concepts(tension_type)                # 悬置态获取桥接概念
```

## Token 预算

| 操作 | 规模 | 估计 |
|:---|:---|:---|
| dialogical_retrieval（6候选 + CandidatePool） | ~300 字 ≈ 420 tokens | v2: 280 → v3: +140 |
| perspective_connections（最大 3 跳 + PerspectiveNavigation） | ~400 字 ≈ 560 tokens | v2: 420 → v3: +140 |
| 同名变体碰撞 | ~100 字 ≈ 140 tokens | 不变 |
| get_bridge_concepts（悬置态） | ~150 字 ≈ 210 tokens | v3 新增 |
| **合计（完整激活路径）** | ~950 字 ≈ 1,330 tokens | v2: ~840 → v3: +490 |

---

*KL9-RHIZOME v3.0 — 基于 kailejiu-graph v2.0、Phase 2 集成需求、悬置态设计改造*
## 技能书导入响应 · Skillbook Import Behaviour

当技能书被导入时，kailejiu-graph 层的行为:

1. **概念注入**: 新概念通过 bridge.py → store_concept() 写入 nodes 表，保留 provenance 元数据
2. **边重建**: imported concept 的 edges 通过 create_edge() 写入 edges 表
3. **影子节点**: 碰撞概念创建 `__shadow_` 节点，is_shadow=1，与主节点互连
4. **检索增强**: 新概念自动加入 dialogical_retrieval 的候选池，按 tension_resonance 排序
5. **谱系记录**: 导入操作写入 genealogy 表，source_dialogue 标注来源技能书

---

*改造日期: 2025-07*
