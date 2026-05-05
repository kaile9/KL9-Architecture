---
name: kailejiu-learner
version: "2.0"
description: |
  KL9-RHIZOME v1.5 · 二重学习 — 迭代学习。
  张力悬置评估驱动的迭代学习、视角扩展、自我对弈。
  订阅 TensionBus (FoldCompleteEvent)，由 orchestrator 在会话结束后调用 record，
  用户触发 feedback 时调用 process_feedback。
---

# 开了玖 · 学习层（KL9-RHIZOME v2.0）

## 架构声明

本模块是 KL9-RHIZOME 网状架构的**迭代学习层**。学习不是单向的「修正」，而是概念 Perspective 映射的丰富化。一个概念不以「正确/错误」评价，而记录它被锚定在哪个 Perspective、存在于哪个 Tension 之中。这是**二重学习**（dual learning）。

**核心跃迁**：

| v1.0（离散、线性、集中式、启发式） | v2.0（连续、同时、涌现式、语义级） |
|:---|:---|
| RLHF 反馈 → score_map 离散四值 {0.0, 0.4, 0.5, 1.0} | FoldWeight 连续可逆折叠权重 + correction_vector |
| 课程等级 → 三级枚举 (easy/medium/hard) | DifficultySpectrum 连续难度谱 (0.0–1.0) + 三维分解 |
| feedback→memory→graph→curriculum 线性因果链 | simultaneous_fold 四维同时折叠投影 |
| generate_curriculum_queries(n) 集中式自对弈 | 张力梯度网络涌现 — 弱概念张力梯度触发相邻节点查询生成 |
| 正则+硬编码名单+zip 启发式概念提取 | SemanticCoParse — 距离窗口语义共现绑定 + Perspective 锚定 |

---

## 核心角色：迭代学习

### 定位

学习层是 KL9-RHIZOME 的「事后优化」层。不参与主循环的认知推理，仅负责事后优化。v2 的关键转变：学习不再是线性因果链（先写记忆→再更新权重→再更新课程），而是同一折叠事件的四个投影面——以 DualState 为统一容器同时折叠。

```
用户反馈
    │
    └── simultaneous_fold(session_id, feedback_type, text, corrected_concepts)
            │
            ├── [面1: memory_projection]   MEM.record_feedback()
            ├── [面2: weight_projection]   GB.update_concept_weight(fw.effective_weight())
            ├── [面3: curriculum_projection] DifficultySpectrum 再计算
            └── [面4: tension_projection]  检测并记录结构性张力
```

### 激活方式

```python
# v1.0: 顺序调用链
# MEM.record_feedback() → GB.update_concept_weight() → _update_curriculum_level()

# v2.0: 同时折叠
L.process_feedback(session_id, feedback_type, text, corrected_concepts)
# → simultaneous_fold() → 四面同时投影
```

---

## 三种学习机制

### 1. RLHF（用户反馈驱动）

**触发器**: 用户说「那不对」「对」「其实是…」时

```python
result = L.process_feedback(
    session_id="当前会话ID",
    feedback_type="wrong",      # correct / wrong / correction / clarification
    text="用户的具体纠正内容"
)
# 返回: {"action": "ask_clarification", "prompt": "哪里不对？"}
# 或:   {"action": "stored", "fold_trace": {...}}
```

**折叠权重链** — 替代 v1.0 的 `score_map`：

```python
# 旧: score_map = {"explicit_correct": 1.0, "explicit_wrong": 0.0, ...}
# 新: FEEDBACK_CORRECTION_MAP（连续修正向量）
FEEDBACK_CORRECTION_MAP = {
    "explicit_correct":      0.15,    # 正向折叠增量
    "explicit_wrong":       -0.20,    # 负向折叠增量
    "explicit_correction":  -0.10,    # 轻微负向折叠
    "implicit":              0.02,    # 几乎不影响的中性折叠
}
```

---

### 2. 课程学习（绩效驱动）

系统追踪最近20回反馈的平均分数，但从旧的三级枚举（easy/medium/hard）升级为 **DifficultySpectrum** 连续难度谱：

```python
@dataclass
class DifficultySpectrum:
    """
    连续难度谱。不再是枚举，而是一个连续浮点值 + 维度分解。
    从 DualState 的张力强度和 FoldWeight 的张力方差中导出。
    """
    value: float              # 连续难度值 (0.0 = 最易, 1.0 = 最难)
    tension_component: float  # 张力贡献分量 — 来自概念修正的方向摇摆
    breadth_component: float  # 广度贡献分量 — 来自概念图的跨领域连接数
    depth_component: float    # 深度贡献分量 — 来自 subgraph 的层级

    def from_fold_weights_and_graph(
        fold_weights: List[FoldWeight],
        graph_stats: dict,
    ) -> 'DifficultySpectrum':
        """从折叠权重和图谱统计中计算连续难度。"""
        # 张力分量 = 平均张力强度
        t_comp = (
            sum(fw.tension_strength() for fw in fold_weights) /
            max(len(fold_weights), 1)
        ) if fold_weights else 0.0

        # 广度分量 = 跨领域连接比例
        total_edges = graph_stats.get('edges', 0)
        cross_field = graph_stats.get('cross_field_edges', 0)
        b_comp = cross_field / max(total_edges, 1)

        # 深度分量 = 平均节点层级
        avg_depth = graph_stats.get('avg_depth', 1.0)
        d_comp = min(1.0, avg_depth / 5.0)

        # 加权合成: 0.4×tension + 0.3×breadth + 0.3×depth
        value = 0.4 * t_comp + 0.3 * b_comp + 0.3 * d_comp

        return DifficultySpectrum(
            value=round(value, 4),
            tension_component=round(t_comp, 4),
            breadth_component=round(b_comp, 4),
            depth_component=round(d_comp, 4),
        )

    def to_legacy_level(self) -> str:
        """向下兼容：映射到旧的三级枚举。"""
        if self.value >= 0.70: return "hard"
        elif self.value >= 0.40: return "medium"
        else: return "easy"

    def query_style_params(self) -> dict:
        """从连续难度谱导出查询风格参数（替代固定模板）。"""
        v = self.value
        return {
            "comparison_bias":  round(0.3 + 0.4 * self.breadth_component, 3),
            "critique_bias":    round(0.2 + 0.5 * self.tension_component, 3),
            "genealogy_bias":   round(0.1 + 0.6 * self.depth_component, 3),
            "definition_bias":  round(max(0.05, 0.5 - 0.5 * v), 3),
        }
```

| 谱值 | 旧等级 | 合成查询风格 |
|:---|:---|:---|
| ≥ 0.70 | hard | 思想谱系/跨领域嫁接/张力存在 |
| ≥ 0.40 | medium | 比较分析/批判/限定 |
| < 0.40 | easy | 基础定义/单一概念 |

---

### 3. 自我对弈（合成查询生成）— 网络创发型

```python
queries = L.generate_curriculum_queries(n=5)
# 返回: [{query, target_concept, target_thinker, difficulty, difficulty_value,
#          tension_type, tension_hint, emergence_source, gradient, ...}]
```

**弱概念判定** — 从「weight 低 + 分数低」扩展为多轴排序：

- **Perspective anchor 缺失**: 概念未锚定到任何 Perspective → 高优先级
- **Tension strength 高**: FoldWeight 修正向量有方向摇摆 → 结构性张力 → 高优先级
- **跨领域连接数低**: 概念图与其他领域的边少 → 孤立 → 高优先级

**创发型查询生成** — 替代 v1.0 的集中式选择 + 模板填充：

```
弱概念 → 计算张力梯度 → 沿边传播 1-2 hops
  → 相邻节点对梯度「响应」→ 从局部创发查询
  → 按梯度强度排序 → 返回 top-n
```

查询按 `tension_type` 分类：
- `"self_inquiry"` — 无邻居，自我发问
- `"neighbor_response"` — 相邻节点的响应型查询
- `"cross_perspective"` — 跨领域张力中的查询

---

## 核心数据结构

### FoldWeight — 连续可逆折叠权重

```python
@dataclass
class FoldWeight:
    """
    不是「一个数值」而是「一个折叠态」。
    权重通过 base + correction_vector 的张力量值计算，
    且每次修正不是覆写而是折叠——保留修正历史，可逆。
    """
    base: float                     # 基础权重，从 graph_backend 的 concept weight 初始化
    correction_vector: List[float]  # 修正向量序列 [-1.0, 1.0]
    reversibility: float = 0.7      # 可逆性系数
    folded_at: str = ""             # 最终折叠时刻
    tension_ref: Optional[str] = None  # 关联 Tension 类型

    def effective_weight(self) -> float:
        """
        计算折叠后的有效权重。
        公式: base + Σ(correction_vector) / (1 + n) × reversibility
        - 分母 (1 + n) 确保修正序列越长越稳定（惯性）
        """
        if not self.correction_vector:
            return self.base
        n = len(self.correction_vector)
        correction_sum = sum(self.correction_vector)
        inertia = correction_sum / (1.0 + n)
        raw = self.base + inertia * self.reversibility
        return max(0.0, min(1.0, raw))

    def fold(self, correction: float) -> 'FoldWeight':
        """折叠一次修正。返回新 FoldWeight（不可变风格）。"""
        ...

    def unfold(self, steps: int = 1) -> 'FoldWeight':
        """回退最近 N 次折叠（可逆性）。"""
        ...

    def tension_strength(self) -> float:
        """
        从修正向量计算张力强度。
        张力强度 = 向量内部方差 / 向量长度。
        如果修正一直在同一方向（方差小），张力低——概念稳定。
        如果修正方向摇摆（方差大），张力高——概念处于结构性张力中。
        """
        if len(self.correction_vector) < 2:
            return 0.0
        mean = sum(self.correction_vector) / len(self.correction_vector)
        variance = sum((x - mean) ** 2 for x in self.correction_vector) / len(self.correction_vector)
        return min(1.0, variance * 3.0)
```

### simultaneous_fold — 同时折叠

```python
def simultaneous_fold(
    session_id: str,
    feedback_type: str,
    text: str = "",
    corrected_concepts: list = None,
) -> dict:
    """
    同时折叠：一次反馈同时投影到四个面。

    不再有「先写记忆→再更新权重→再更新课程」的时序锁。
    四个面共享同一个 FoldWeight，在概念层面同时折叠。

    返回：与 process_feedback 兼容的 dict + fold_trace 折叠追踪信息
    """
    correction = FEEDBACK_CORRECTION_MAP.get(
        type_map.get(feedback_type, "implicit"), 0.0
    )

    # 面1: 记忆投影
    MEM.record_feedback(session_id, ...)

    # 面2: 权重投影
    for cc in corrected_concepts:
        fw = FoldWeight(base=old_weight or 0.5)
        fw = fw.fold(correction)
        GB.update_concept_weight(concept_name, fw.effective_weight())

    # 面3: 课程投影
    spectrum = _recompute_spectrum()

    # 面4: 张力投影
    tension_detected = _detect_structural_tension(corrected_concepts or [])

    return {"action": "stored", "fold_trace": fold_trace}
```

---

## 概念修正流 — 语义级同时理解

```python
corrected = L.extract_concepts_from_correction(
    correction_text="用户输入的纠正文本",
    field="当前领域"
)
```

**语义共现解析** — 替代独立正则 + zip：

```
启发式（旧）：
  regex_books ──┐
  regex_quotes ──┼── zip ──→ extracted
  hard_list ────┘

语义级同时理解（新）：
  correction_text
      │
      ├── 语义共现分组 (co_occurrence_binding)
      │     「《存在与时间》中 海德格尔 的 '在世存在'」
      │     → [(work="存在与时间", thinker="海德格尔", concept="在世存在")]
      │
      ├── Perspective 锚定
      │     "在世存在" → existential.immediate 视角
      │
      └── Tension 识别
            "但萨特认为..." → existential.immediate vs existential.mediated
```

**提取流程**：

1. **语义共现分组** — 识别「作品-思想家-概念」三元组，使用滑动距离窗口（50字符以内视为共现）而非独立正则
2. **Perspective 锚定** — 将概念锚定到 KL9-RHIZOME 视角类别（基于 field 映射 + 概念名语义线索）
3. **Tension 识别** — 检测纠正文本中的结构性张力（转折词 → 视角对撞；纠正词 → 认知基底差异）

```python
for c in corrected:
    GB.store_concept(
        name=c['name'], tier1=c['tier1'],
        thinker=c.get('thinker',''),
        work=c.get('work',''), field=c['field']
    )
    # 新: Perspective 锚定记录
    if c.get('perspective_anchor'):
        _record_perspective_anchor(c['name'], c['perspective_anchor'])
    # 新: 张力记录
    if c.get('tension_detected'):
        _record_tension(c['name'], c['tension_detected'])
```

---

## 学习状态报告

### get_lean_summary() — v1.5 轻量摘要

```python
def get_lean_summary() -> dict:
    """
    返回轻量学习摘要，可在每次对话末尾注入。
    纯数据聚合，零额外 LLM 调用（不触发 LLM）。

    返回字段：
      - difficulty_value: 当前连续难度谱值
      - total_folds: 累计二重折叠次数
      - suspension_rate: 悬置率（suspended / total_folds）
      - tension_drift: 各张力类型的折叠深度趋势
      - dominant_tension: 当前主导张力类型
    """
    spectrum = _load_difficulty_spectrum()
    dual_stats = _load_dual_states_stats()
    tension_drift = _compute_tension_drift(dual_stats)

    total_folds = dual_stats.get("total_folds", 0)
    suspended_states = dual_stats.get("suspended_states", 0)

    return {
        "difficulty_value": spectrum.value if hasattr(spectrum, 'value') else 0.5,
        "total_folds": total_folds,
        "suspension_rate": suspended_states / max(total_folds, 1),
        "tension_drift": tension_drift,
        # tension_drift 示例: {"eternal_vs_finite": {"avg_depth": 2.8, "trend": "decreasing", "fold_count": 15}, ...}
        "dominant_tension": (
            max(tension_drift.items(), key=lambda x: x[1].get("fold_count", 0))[0]
            if tension_drift else None
        ),
    }


def _load_difficulty_spectrum():
    """从持久化存储加载当前 DifficultySpectrum。"""
    import json
    state_path = "<KL9-RHIZOME_DIR>/skills/kailejiu-shared/storage/learner_state.json"
    try:
        with open(state_path, 'r') as f:
            data = json.load(f)
        ds = data.get("difficulty_spectrum", {})
        # 返回类 DifficultySpectrum 的对象或简易容器
        return type('Spectrum', (), {
            'value': ds.get('value', 0.5),
            'tension_component': ds.get('tension_component', 0.0),
            'breadth_component': ds.get('breadth_component', 0.0),
            'depth_component': ds.get('depth_component', 0.0),
        })()
    except (FileNotFoundError, json.JSONDecodeError):
        return type('Spectrum', (), {
            'value': 0.5, 'tension_component': 0.0,
            'breadth_component': 0.0, 'depth_component': 0.0,
        })()


def _load_dual_states_stats() -> dict:
    """从持久化存储加载 DualState 统计。"""
    import json
    state_path = "<KL9-RHIZOME_DIR>/skills/kailejiu-shared/storage/learner_state.json"
    try:
        with open(state_path, 'r') as f:
            data = json.load(f)
        return data.get("dual_states", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _compute_tension_drift(dual_stats: dict) -> dict:
    """
    计算各张力类型的折叠深度趋势。
    从 dual_states 的 active_tensions 和 fold_history 中提取。
    """
    drift = {}
    active_tensions = dual_stats.get("active_tensions", [])
    fold_history = dual_stats.get("fold_history", [])

    for tt in active_tensions:
        tt_folds = [f for f in fold_history if f.get("tension_type") == tt]
        if tt_folds:
            depths = [f.get("fold_depth", 1) for f in tt_folds]
            avg_depth = sum(depths) / len(depths)
            # 趋势：最近 5 次 vs 全部
            recent_depths = depths[-5:] if len(depths) >= 5 else depths
            recent_avg = sum(recent_depths) / len(recent_depths)
            trend = "increasing" if recent_avg > avg_depth else "decreasing" if recent_avg < avg_depth else "stable"
            drift[tt] = {
                "avg_depth": round(avg_depth, 2),
                "trend": trend,
                "fold_count": len(tt_folds),
            }

    return drift
```

### get_learner_report()（保留）

```python
report = L.get_learner_report()
# 返回:
# {
#   curriculum_level: "medium",               # 旧兼容
#   difficulty_spectrum: {                     # 新: 连续谱
#     value: 0.62, tension: 0.15, breadth: 0.30, depth: 0.17
#   },
#   avg_score_window: 0.72,
#   top_weak_concepts: [
#     {"name": "父法", "fold_weight": 0.32, "perspective_anchor": "social.regression", "tension_strength": 0.45},
#     {"name": "决断主义", "fold_weight": 0.28, "perspective_anchor": null, "tension_strength": 0.72},
#   ],
#   graph: {concepts_active: 42, edges: 98, cross_field_edges: 12},
#   memory: {sessions: 15, avg_explicit_score: 0.72},
#   fold_weights_summary: {                    # 新: 折叠权重摘要
#     total_weighted_concepts: 35,
#     avg_tension_strength: 0.22,
#     high_tension_count: 4,
#   },
#   dual_states: {                             # 新: DualState 学习记录
#     total_folds: 67,
#     suspended_states: 23,
#     forced_states: 2,
#     active_tensions: ["eternal_vs_finite", "mediated_vs_real"],
#   },
#   next_curriculum_queries: [
#     {"query": "...", "target_concept": "父法", "tension_type": "regression_vs_growth", ...},
#   ]
# }
```

---

## 公共接口兼容性

| 接口 | 旧签名 | 新签名 | 兼容方式 |
|:---|:---|:---|:---|
| `process_feedback` | `(session_id, feedback_type, text, corrected_concepts) → dict` | 不变 | 内部调用 `simultaneous_fold`，返回值增加 `fold_trace`（optional） |
| `generate_curriculum_queries` | `(n=5) → list[dict]` | 不变 | 返回值 dict 增加 `difficulty_value`、`tension_type`、`emergence_source`、`gradient` |
| `extract_concepts_from_correction` | `(correction_text, field) → list[dict]` | 不变 | 返回值 dict 增加 `perspective_anchor`、`tension_detected` |
| `get_learner_report` | `() → dict` | 不变 | 增加 `difficulty_spectrum`、`fold_weights_summary`、`dual_states` |
| `identify_weak_concepts` | `(top_k=10) → list[dict]` | 不变 | 内部使用 FoldWeight + Perspective anchor 多轴排序 |

---

## 规则

### R1: 连续可逆折叠权重

`FoldWeight` 替代离散 `score_map`。修正不是覆写而是折叠——保留修正历史，支持 `unfold()` 回退。`effective_weight()` 通过 `base + Σ(correction_vector) / (1+n) × reversibility` 计算。

### R2: 连续难度谱

`DifficultySpectrum` 替代三级枚举。从 FoldWeight 的张力方差和图谱的跨领域连接统计中导出。`to_legacy_level()` 提供向后兼容。

### R3: 同时折叠

`simultaneous_fold()` 一次反馈同时投影到 memory / weight / curriculum / tension 四个面，消除线性因果链的时序锁。

### R4: 网络涌现自对弈

`generate_curriculum_queries()` 不再集中式选择弱概念 + 模板填充。弱概念的张力梯度沿边传播到相邻节点，相邻节点根据自身特性「响应」生成查询。

### R5: 语义共现解析

`extract_concepts_from_correction()` 使用距离窗口共现绑定替代独立正则 + zip。同时执行 Perspective 锚定和 Tension 识别。

---

## 数据库

`<KL9-RHIZOME_DIR>/skills/kailejiu-shared/storage/learner_state.json`（与 v1 兼容）

v2 新增字段：
```json
{
    "sessions_seen": 0,
    "avg_score_history": [],
    "curriculum_level": "easy",
    "difficulty_spectrum": {
        "value": 0.32,
        "tension_component": 0.0,
        "breadth_component": 0.1,
        "depth_component": 0.2
    },
    "fold_weights": {
        "父法": {
            "base": 0.45,
            "correction_vector": [-0.2, -0.1],
            "reversibility": 0.7,
            "tension_ref": null
        }
    },
    "fold_history": []
}
```

---

## 依赖关系

```
kailejiu-learner 依赖:
├── core_structures.py (DualState, Tension, Perspective, FoldWeight, DifficultySpectrum)
├── perspective_types.py (PERSPECTIVE_TYPES, TENSION_TYPES)
├── graph_backend.py (GB.search, GB.get_subgraph, GB.update_concept_weight, GB.get_stats)
├── memory.py (MEM.record_feedback, MEM.get_feedback_for_concepts, MEM.get_stats)
└── learner_state.json (learner 自身状态持久化)
```

---

## 与 rhizome_engine.py 接口对齐

```
rhizome_engine 会话结束后:
  → orchestrator 调用 L.record_session(session_id, dual_state)

用户反馈时:
  → orchestrator 调用 L.process_feedback(...)
    → simultaneous_fold() → 四面投影

弱概念发现:
  → identify_weak_concepts() → 多轴排序（Perspective 缺失 + Tension 强度 + 跨领域连接数）
    → generate_curriculum_queries() → 张力梯度网络涌现
```

---

> *学习是概念 Perspective 映射的丰富化。*
> *一次修正是折叠而非覆写。折叠是堆叠，不是擦除。*

*KL9-RHIZOME v2.0 — 基于 kailejiu-learner v1.0、CORE_CONCEPTS.md、P2_LEARNER_ADAPTATION 改造*
*改造日期: 2025-07*
