# KL9-RHIZOME 技能书吸收机制 · Skill Book Absorption v1.0

## 问题 · Problem

两个独立的 KL9 实例阅读同一本书会产生**相似但不相同**的 DualStates、概念定义和张力配置。当实例 A 导入实例 B 的技能书时，如何合并而不破坏现有认知结构？

*Two independent KL9 instances reading the same book will produce similar but not identical DualStates, concept definitions, and tension configurations. When instance A imports instance B's skill book, how do we merge without corrupting A's existing cognitive structure?*

## 核心挑战 · Core Challenges

| 挑战 | 严重度 | 描述 |
|------|:---:|------|
| **概念碰撞** · Concept Collision | 🔴 | 同名概念不同定义——例如两个 "Geld als Denkform" 的 DualState 有微妙差异 |
| **张力扭曲** · Tension Distortion | 🔴 | 导入的张力可能将现有张力场拖入错误配置 |
| **视角污染** · Perspective Pollution | 🟡 | 生成技能书的 LLM 的认知偏差可能被继承 |
| **版本漂移** · Version Drift | 🟡 | 来自旧版 KL9 的技能书可能使用不兼容的格式 |
| **信任校准** · Trust Calibration | 🟠 | 无法自动判断技能书质量（来自 AI 摘要？翻译阅读？） |

## 设计原则 · Design Principles

### 原则 1：碰撞分叉优于强行合并
*Bifurcation over forced merge.*

同名但定义不同的概念不合并——在两个节点间创建 `collision_tension` 边，标记为需要人类裁决的冲突。

**错误做法**：取两个定义的"平均值"或"较新定义覆盖旧定义"。

**正确做法**：
```
已有图：Geld_als_Denkform [v1: "货币是认知范畴，其社会效力来自集体承认"]
导入图：Geld_als_Denkform [v2: "货币是思维形式，先于交换关系而非后于"]
                           ↓
Geld_als_Denkform [v1] ═══ collision_tension ═══ Geld_als_Denkform [v2]
                           ↓
provenance: kl9_instance_A          provenance: kl9_instance_B
```

### 原则 2：溯源高于权重
*Provenance over weight.*

每个导入的概念节点携带来源信息——从哪个技能书来、哪个 LLM 生成、哪个架构版本。不使用数值权重替代溯源信息。

### 原则 3：暂存优于直接激活
*Staging over direct activation.*

导入分两阶段：先加载到隔离的暂存图谱，检测完冲突后再由用户选择性地激活节点。

### 原则 4：回滚优于覆盖
*Rollback over overwrite.*

每次导入前保存 snapshot。激活后如果检测到全局张力梯度异常波动（任何张力强度变化 > 0.3），触发回滚建议。

## 5 阶段导入流程 · 5-Stage Import Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ IMPORT PIPELINE                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Stage 0: VALIDATE]                                             │
│  ├─ 读取 manifest.json                                           │
│  ├─ 架构版本兼容性检查（architecture_version ≤ 当前版本）            │
│  ├─ LLM 名称记录（用于偏差追溯）                                    │
│  ├─ 质量分级（S/A/B/C/D，见 SKILLBOOK_STANDARD.md）                │
│  └─ 阻断条件：版本不兼容 → 拒绝导入                                │
│                                                                  │
│  [Stage 1: SANDBOX]                                              │
│  ├─ 创建隔离暂存图谱 StagingGraph                                 │
│  ├─ 加载所有 fold_nodes, fold_edges, concepts, edges              │
│  ├─ 所有节点标记 provenance                                       │
│  └─ 阻断条件：JSON 结构解析失败 → 拒绝导入                         │
│                                                                  │
│  [Stage 2: DIFFUSE]                                              │
│  ├─ 概念重叠检测（同名 or 语义距离 < 阈值）                         │
│  ├─ 张力重叠检测（同名 or 双视角对重叠 > 50%）                      │
│  ├─ 计算扩散分数 diffusion_score per concept                      │
│  └─ 无阻断——仅生成报告                                            │
│                                                                  │
│  [Stage 3: RESOLVE]                                              │
│  ├─ 对每个冲突：                                                   │
│  │   ├─ [默认] 分叉 + collision_tension 边                        │
│  │   └─ [可选] 若 diff < 信任阈值 and 用户批准 → 合并              │
│  ├─ 独立概念 → 直接激活                                           │
│  └─ 无阻断——冲突列表交给用户                                       │
│                                                                  │
│  [Stage 4: ACTIVATE]                                             │
│  ├─ 合并暂存图谱到活跃图谱                                         │
│  ├─ 触发 TensionBus: SkillBookMergeEvent                         │
│  ├─ 全局张力梯度重计算                                             │
│  ├─ 异常检测（任何张力 Δ > 0.3）                                   │
│  └─ 生成 Import Log                                               │
│                                                                  │
│  [Stage 5: ROLLBACK (条件触发)]                                    │
│  ├─ 恢复 pre-import snapshot                                      │
│  └─ 记录 rollback 原因 + 用户反馈                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 信任权重算法 · Trust Weight Algorithm

导入时每个节点获得信任权重 `trust_weight`，用于后续推理中的引用优先级：

```python
def compute_trust_weight(manifest, concept_node):
    """
    trust_weight ∈ [0.0, 1.0]
    """
    # 基础权重来自质量分级
    quality_map = {"S": 1.0, "A": 0.8, "B": 0.6, "C": 0.3, "D": 0.1}
    base = quality_map[manifest.quality_tier]

    # 轮数奖励（非线性，边际递减）
    rounds_bonus = min(0.15, manifest.rounds_completed * 0.05)

    # 概念稳定性——这个概念在原文中被折叠了多少次
    stability = concept_node.get("fold_count", 1) / max_fold_count

    # LLM 偏差因子（经验值，可更新）
    llm_bias = LLM_BIAS_MAP.get(manifest.llm_name, 0.0)

    trust_weight = base + rounds_bonus - llm_bias
    return clamp(trust_weight, 0.05, 0.95)
```

### LLM 偏差表（初始值，随社区反馈更新）

| LLM | bias | 原因 |
|:---|---:|:---|
| claude-opus-4.7 | 0.0 | 基准线 |
| deepseek-v4-pro | 0.0 | 初始假定无偏差 |
| kimi-2.6 | -0.05 | 中文语境可能引入独特视角偏差 |
| gpt-4o | 0.0 | 待社区数据 |

LLM 偏差表存储在 `kl9_core/llm_bias_registry.json`，可被任何 KL9 实例通过 PR 更新。

## 碰撞检测算法 · Collision Detection

### 概念碰撞

两个概念被视为碰撞当：

1. **同名**（精确匹配）→ 默认分叉
2. **语义距离 < 阈值**（计算概念定义的向量相似度）→ 标记 `semantic_collision`
3. **同一谱系位置**（例如两个概念都声称"Simmel 对 Brodbeck 的影响"但权重不同）→ 保留较高权重，新增 provenance

### 张力碰撞

两个张力被视为碰撞当：

1. **同名** → 检查 perspective_A 和 perspective_B 是否两个都匹配
2. **双视角对重叠 > 50%** → 可能是一个张力的两个面向 → 合并为中继节点
3. **完全不重叠** → 独立添加

## 合并决策矩阵 · Merge Decision Matrix

| 条件 | 默认行为 | 用户可覆盖 |
|------|:---:|:---:|
| 同名概念，definition_diff < 0.1 | 信任加权合并（取高权重定义） | ✅ 是 |
| 同名概念，definition_diff 0.1-0.3 | 分叉 + collision_tension | ✅ 是 |
| 同名概念，definition_diff > 0.3 | 分叉 + collision_tension | ✅ 是 |
| 异名概念，semantic_sim > 0.8 | 标记 `near_duplicate` + 分叉 | ✅ 是 |
| 独立概念（无碰撞） | 直接激活 | ❌ 否 |
| 同名张力，perspective 对匹配 | 合并（保留两个紧张轴） | ✅ 是 |

## 异常检测 · Anomaly Detection

导入后自动运行：

```python
def post_import_audit(pre_graph, post_graph):
    anomalies = []

    # 1. 张力剧烈波动
    for tension_id in post_graph.tensions:
        delta = abs(post_graph[tension_id].intensity - pre_graph.get(tension_id, 0.0))
        if delta > 0.3:
            anomalies.append({
                "type": "tension_spike",
                "tension": tension_id,
                "delta": delta,
                "severity": "critical" if delta > 0.5 else "warning"
            })

    # 2. 循环引用（A 概念导入 B 概念，但 A 概念已在图中）
    # 3. 孤立节点（导入后无入度无出度）
    # 4. 冲突爆炸（collision_tension 超过总概念数的 30%）

    if anomalies:
        suggest_rollback(anomalies)
    return anomalies
```

## 实现接口 · Implementation Interface

```python
# kl9_core/skillbook_importer.py

class SkillBookImporter:
    """
    技能书导入器。
    订阅 TensionBus 的 ImportRequestEvent。
    """

    def __init__(self, graph: ConceptGraph, memory: MemoryLayer, bus: TensionBus):
        self.graph = graph
        self.memory = memory
        self.bus = bus
        self.staging = None  # StagingGraph

    async def import_skillbook(self, path: str, merge_strategy: str = "bifurcate") -> ImportResult:
        """
        导入技能书的完整流程。

        Args:
            path: 技能书根目录路径
            merge_strategy: "bifurcate" | "trust_weighted" | "manual"
                            "manual" 由终端在前端确认每个冲突

        Returns:
            ImportResult 包含: activated_nodes, collisions, anomalies, rollback_snapshot
        """
        pass

    async def validate(self, manifest: dict) -> ValidationResult:
        """Stage 0"""
        pass

    async def sandbox_load(self, path: str) -> StagingGraph:
        """Stage 1"""
        pass

    async def diffuse(self) -> DiffuseReport:
        """Stage 2"""
        pass

    async def resolve(self, strategy: str) -> ResolveReport:
        """Stage 3"""
        pass

    async def activate(self) -> ActivationResult:
        """Stage 4"""
        pass

    async def rollback(self, snapshot: Snapshot) -> None:
        """Stage 5"""
        pass
```

## 终端交互 · User Interface

当 `merge_strategy="manual"` 时，终端通过以下事件与导入器交互：

```json
// ImportConflictEvent → User
{
  "event": "ImportConflictEvent",
  "data": {
    "conflict_id": "sc_001",
    "type": "concept_collision",
    "existing_node": { "id": "cn_012", "label": "Geld als Denkform", "definition": "..." },
    "imported_node": { "id": "scn_045", "label": "Geld als Denkform", "definition": "..." },
    "similarity": 0.72,
    "suggested_action": "bifurcate"
  }
}

// User → ImportResolveEvent
{
  "event": "ImportResolveEvent",
  "data": {
    "conflict_id": "sc_001",
    "action": "bifurcate"  // or "merge_existing" | "merge_imported" | "skip_imported"
  }
}
```

## 最小可行实现 · MVP Scope

v1.0 目标：安全导入 + 冲突分叉。不实现自动合并。

```
实现优先级：
  1. ✅ manifest 解析 + 版本校验
  2. ✅ 暂存图谱加载
  3. ✅ 概念碰撞检测（同名匹配）
  4. ✅ 冲突分叉 + collision_tension 边
  5. ✅ provenance 标记
  6. ✅ 活跃图谱合并
  7. ⬜ 语义距离检测（需嵌入模型）
  8. ⬜ 信任加权自动合并
  9. ⬜ 异常检测 + 自动回滚
 10. ⬜ 终端冲突确认界面
```

---

*"导入不是学习。导入是信任一个已完成的学习。"*
