---
name: kailejiu-research
version: "3.0"
description: |
  KL9-RHIZOME v1.5 · Dialogical Activation 层。
  与理论对话激活认知——不检索征用，而是对话式改造理论框架。
  订阅 TensionBus（全 6 类 tension_type），可独立多入口激活。
---

# 开了玖 · 对话式激活层 v3

## 存在方式

TensionBus 订阅 + 独立激活，KL9-RHIZOME 多入口之一：

```python
# 独立激活
research.activate("现代性是什么")

# TensionBus 订阅（全 6 类 tension，任意技能发射即自动唤醒）
TensionBus.subscribe(TensionSubscription(
    skill_name="kailejiu-research",
    tension_types=["eternal_vs_finite","mediated_vs_real","regression_vs_growth",
                   "freedom_vs_security","economic_vs_grotesque","truth_vs_slander"],
    priority=1
))
```

---

## 核心操作（替代 R1-R5）

旧流水线已消除。新架构：三项折叠操作。

### 1. dialogical_activation(query) → List[dict]

```python
def dialogical_activation(query: str) -> List[dict]:
    """搜索相关理论并与之对话改造。返回每项含 theory/thinker/original_frame/
    transformed_frame/transformation_tension/perspective_affinity/derived_tension_type"""
    results = []
    candidates = _activate_from_graph(query, top_k=5)

    # v1.5: 降低外部搜索触发阈值——学术标记、引号、年份、思想家姓名均触发
    if len(candidates) < 2 or _has_academic_markers(query):
        web_results = web_search_tavily(query=query, max_results=8, search_depth="advanced")
        candidates += _mine_perspective_concepts(web_results, query)  # v3 重命名

    for theory in candidates:
        entry = transform_in_context(theory, query)
        if entry:
            results.append(entry)

    if results:
        _emit_dialogical_tension(results, query)  # v3: 动态推导 tension_type
    return results


def _has_academic_markers(query: str) -> bool:
    """
    检测 query 中的学术引用/文献溯源意图标记。
    满足任一条件返回 True，强制触发外部搜索：
    - 引号标记（"" 或「」）→ 学术引用
    - 四位年份（如 2011、2001）→ 文献溯源
    - 已知思想家姓名 → 理论对话意图
    """
    import re
    # 引号检测
    if '"' in query or '"' in query or '\u300c' in query or '\u300e' in query:
        return True
    # 年份检测（四位数字，1800-2099）
    if re.search(r'\b(1[89]\d\d|20\d\d)\b', query):
        return True
    # 已知思想家姓名检测
    KNOWN_THINKERS = [
        "福柯", "德里达", "德勒兹", "阿甘本", "海德格尔", "尼采", "康德", "黑格尔",
        "马克思", "韦伯", "涂尔干", "布迪厄", "拉康", "巴特勒", "萨特", "波伏娃",
        "阿伦特", "施密特", "本雅明", "阿多诺", "哈贝马斯", "罗尔斯", "齐泽克",
        "巴迪欧", "朗西埃", "南希", "斯蒂格勒", "拉图尔", "塞杜", "斯皮瓦克",
        "法农", "萨义德", "维特根斯坦", "库恩", "费耶阿本德",
    ]
    query_lower = query.lower()
    for thinker in KNOWN_THINKERS:
        if thinker.lower() in query_lower:
            return True
    return False
```

### 2. transform_in_context(theory, query) → dict | None

```python
def transform_in_context(theory: dict, query: str) -> dict | None:
    """在 query 语境压力下改造理论框架。不是征用，而是对话式拉伸/扭曲/重构。"""

    # v3: 使用单一 definition 字段，匹配 graph v2 节点 schema
    # graph v2 节点: {name, thinker, work, field, definition,
    #                  tension_types[], connected_perspectives[]}
    original_frame = theory.get("definition", theory.get("original_frame", ""))

    transformed = _llm_transform(
        system=f"""你正在与「{theory['name']}」（{theory.get('thinker','')}）进行对话式改造。
你不是在引用它，而是在 query 的语境压力下改造它的框架。
保持理论的深层结构，但让它在新的语境中说话。

query: {query}
原始框架: {original_frame}

请返回改造后的框架。不要用「根据XX理论」开头——直接让改造后的框架自己说话。""",
        temperature=0.7
    )

    tension = identify_transformation_tension(original_frame, transformed)
    affinity = _tag_perspective_affinity(theory, transformed, query)  # v3 新增
    derived_tt = _derive_tension_type(tension, query)                 # v3 新增

    return {
        "theory": theory["name"], "thinker": theory.get("thinker", ""),
        "original_frame": original_frame, "transformed_frame": transformed,
        "transformation_tension": tension,
        "perspective_affinity": affinity, "derived_tension_type": derived_tt,
        "source_citation": {
            "work": theory.get("work", ""),
            "year": theory.get("year", ""),
            "page_hint": theory.get("page_hint", ""),
            "original_text_snippet": theory.get("original_text_snippet", "")
        },
    }
```

### 3. identify_transformation_tension(original, transformed) → str

```python
def identify_transformation_tension(original: str, transformed: str) -> str:
    """从改造动作本身涌出张力。关注三个维度：
    1. 不可通约性 — 哪些核心预设在新的语境中无法保持？
    2. 拉伸痕迹 — 改造后的框架在哪些点上被拉伸到了临界？
    3. 剩余物 — 原框架中有什么在新框架中无法被容纳？
    返回自然语言描述（非 JSON），供 constitutional_critique 输入。"""

    return _llm_transform(
        system=f"""识别以下理论框架在改造过程中产生的结构性张力。

原始框架: {original}
改造后框架: {transformed}

请从以下三个维度描述张力（自然语言，非列表格式）：
1. 哪些核心预设在新的语境中无法保持？
2. 改造后的框架在哪些点上被拉伸到了临界？
3. 原始框架中有什么无法被新框架容纳？

不要给出解决方案，不要缝合，不要"两者都有道理"——只揭示张力本身。""",
        temperature=0.5
    )


def detect_literature_drift(
    original_frame: str,
    transformed_frame: str,
    source: dict,
) -> str:
    """
    检测改造后的框架与原始文献之间的漂移距离。

    通过三个维度评估：
    1. 概念保留度 — 原始框架的核心概念在改造后是否仍可识别
    2. 语境迁移度 — 原始框架的前提条件有多少被替换为 query 语境的条件
    3. 论证方向变更 — 原始框架的论证方向是否被反转或大幅偏离

    返回 drift_grade:
      - "minimal"   — 轻度语境适配，核心结构完整保留
      - "moderate"  — 显著语境拉伸，部分预设被替换
      - "significant" — 深度改造，论证方向可能反转，需在输出中显式标记改造性质
    """
    # 规则层快速判定（无 LLM 调用）
    orig_words = set(original_frame.lower().split())
    trans_words = set(transformed_frame.lower().split())

    # Jaccard 相似度
    intersection = orig_words & trans_words
    union = orig_words | trans_words
    jaccard = len(intersection) / max(len(union), 1)

    # 否定词检测（not, 不, 并非, 不再, 反转 等）
    negation_markers = ["不", "并非", "不再", "反转", "相反", "倒置", "颠覆"]
    negation_count = sum(1 for m in negation_markers if m in transformed_frame)

    if jaccard > 0.5 and negation_count == 0:
        return "minimal"
    elif jaccard > 0.25 or negation_count <= 2:
        return "moderate"
    else:
        return "significant"
```

---

## Phase 1 集成：从理论候选到视角激活

v3 新增。研究输出显式喂入 Phase 1（对话式激活）的数据流契约：

```
kailejiu-research.activate(query)
         │
         ▼
  dialogical_activation() 产出 List[dict]
  每项含: perspective_affinity[], derived_tension_type, transformed_frame
         │
         ▼
  ┌──────────────────────────────────────────┐
  │ Phase 1: Dual Fold / dialogue_activator  │
  │                                          │
  │ · 以 perspective_affinity 选 PERSPECTIVE_TYPES 最佳子类型   │
  │ · 以 derived_tension_type 查 TENSION_TYPES → emergent_style │
  │ · 构建 Perspective(name, characteristics)                 │
  │ · 发射 TensionSignal → TensionBus                          │
  └──────────────────────────────────────────┘
         │
         ▼
  expression / reasoner / soul 订阅消费
```

**数据契约**：

| 研究输出 | Phase 1 消费方 | 用途 |
|:---|:---|:---|
| `perspective_affinity[]` | `dialogue_activator._select_perspective_subtype()` | 匹配 `PERSPECTIVE_TYPES.{family}.{subtype}` |
| `derived_tension_type` | `TensionBus.emit(Tension(tension_type=...))` | 查 `TENSION_TYPES[key]` 获取 `emergent_style` |
| `transformed_frame` | `Perspective.characteristics` | 构建视角实质内容 |
| `transformation_tension` | `Tension.irreconcilable_points[]` | 填充不可调和点 |

---

## 视角相关概念挖掘

v3：概念提取重构为「视角相关概念挖掘」。不再提取通用概念，每个候选打视角亲和度标签。

```python
def _mine_perspective_concepts(web_results, query) -> List[dict]:
    """从网络检索结果挖掘视角相关概念。
    v3 变更：函数重命名（原 _extract_theory_candidates），
    移除 tier1/tier2/tier3，统一用 definition，匹配 graph v2 节点 schema。"""

    from perspective_types import FAMILY_SIGNALS

    candidates = []
    for result in web_results:
        extracted = {
            "name": "", "thinker": "", "work": "", "field": "",
            "definition": "",     # v3: 替代 tier1/2/3
            "confidence": 0.0,    # 保留但不做门控
            "perspective_affinity": [],  # v3 新增
        }
        # ... 提取逻辑不变 ...
        extracted["perspective_affinity"] = _tag_perspective_affinity(
            extracted, extracted["definition"], query
        )
        candidates.append(extracted)
    return candidates  # 无 confidence 过滤，让张力自然筛选


def _tag_perspective_affinity(theory: dict, frame: str, query: str) -> List[str]:
    """v3 新增。用 FAMILY_SIGNALS 关键词密度评分，返回 Top-3 视角子类型。
    纯规则引擎，无 LLM 调用。"""

    combined = f"{theory.get('name','')} {frame} {query}"
    scores = {}

    for fam, signals in FAMILY_SIGNALS.items():
        fam_score = sum(1 for kw in signals["keywords"] if kw in combined)
        if fam_score == 0:
            continue
        for sub, sub_kws in signals.get("subtypes", {}).items():
            sub_score = sum(1 for kw in sub_kws if kw in combined)
            scores[f"{fam}.{sub}"] = fam_score * 1.0 + sub_score * 1.5

    return [k for k, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]]
```

---

## transformation_tension → TENSION_TYPES 映射

v3 新增。从改造张力的自然语言描述动态推导 `perspective_types.py` 中 `TENSION_TYPES` 键。

```python
def _derive_tension_type(transformation_tension: str, query: str) -> str:
    """从改造张力动态推导 TENSION_TYPES 键（替代 v2 硬编码 theoretical_vs_empirical）。
    算法：FAMILY_SIGNALS 评分 → Top-2 家族 → FAMILY_TENSION_MAP 查表。"""

    from perspective_types import FAMILY_SIGNALS, FAMILY_TENSION_MAP

    combined = f"{transformation_tension} {query}"
    fam_scores = {}
    for fam, signals in FAMILY_SIGNALS.items():
        s = sum(1 for kw in signals["keywords"] if kw in combined)
        if s > 0:
            fam_scores[fam] = s * signals["weight"]

    if len(fam_scores) >= 2:
        ranked = sorted(fam_scores, key=fam_scores.get, reverse=True)
        return FAMILY_TENSION_MAP.get((ranked[0], ranked[1]), "mediated_vs_real")

    if len(fam_scores) == 1:
        fam_a = next(iter(fam_scores))
        complement = {"temporal":"existential","existential":"temporal",
                      "social":"political","political":"social",
                      "epistemological":"aesthetic","aesthetic":"epistemological"}
        return FAMILY_TENSION_MAP.get((fam_a, complement.get(fam_a,"existential")),
                                       "mediated_vs_real")
    return "mediated_vs_real"
```

**映射总表**：

| TENSION_TYPES 键 | perspective_source | emergent_style |
|:---|:---|:---|
| `mediated_vs_real` | existential | analytical_juxtaposition |
| `freedom_vs_security` | political | ironic_suspension |
| `economic_vs_grotesque` | economic_grotesque | temporal_contrast |
| `eternal_vs_finite` | temporal | temporal_contrast |
| `regression_vs_growth` | social | ironic_suspension |
| `truth_vs_slander` | truth_construction | dialectical_negation |

`emergent_style` 由 expression 技能查 `EMERGENT_STYLE_MAP` 决定最终表达风格。

---

## TensionBus 集成（v3: 动态推导 tension_type）

```python
def _emit_dialogical_tension(dialogues: List[dict], query: str):
    """发射聚合理论间张力到 TensionBus。
    v3: tension_type 由 _derive_tension_type 动态推导，不再硬编码。
    v1.5: 对每个含原始文献引用的对话激活，写入谱系边。"""

    if not dialogues:
        return

    # v1.5: 谱系边写入——记录概念在对话压力下的语义漂移
    for entry in dialogues:
        sc = entry.get("source_citation", {})
        if sc and sc.get("original_text_snippet"):
            drift = detect_literature_drift(
                entry["original_frame"],
                entry["transformed_frame"],
                sc
            )
            # 写入谱系边
            graph.create_genealogy_edge(
                from_id=entry.get("original_concept_id", ""),
                to_id=entry.get("transformed_concept_id", ""),
                drift_type=drift,
                transformation_context=query,
                transformation_tension=entry["transformation_tension"]
            )

    if len(dialogues) >= 2:
        sorted_d = sorted(dialogues,
                          key=lambda d: len(d.get("transformation_tension", "")),
                          reverse=True)
        a, b = sorted_d[0], sorted_d[1]
        combined_t = f"{a.get('transformation_tension','')} {b.get('transformation_tension','')}"
        derived_tt = _derive_tension_type(combined_t, query)

        TensionBus.emit(TensionSignal(tension=Tension(
            perspective_A=Perspective(
                name=f"{a['thinker']}的{a['theory']}（经语境改造）",
                characteristics={"frame":a["transformed_frame"],"affinity":a.get("perspective_affinity",[])}),
            perspective_B=Perspective(
                name=f"{b['thinker']}的{b['theory']}（经语境改造）",
                characteristics={"frame":b["transformed_frame"],"affinity":b.get("perspective_affinity",[])}),
            claim_A=a["transformed_frame"], claim_B=b["transformed_frame"],
            irreconcilable_points=[
                f"{a['theory']}的预设: {a['transformation_tension']}",
                f"{b['theory']}的预设: {b['transformation_tension']}"],
            tension_type=derived_tt,  # v3: 动态推导
        ), source_skill="kailejiu-research", fold_count=2))

    else:
        entry = dialogues[0]
        derived_tt = entry.get("derived_tension_type", "mediated_vs_real")
        TensionBus.emit(TensionSignal(tension=Tension(
            perspective_A=Perspective(
                name=f"{entry['thinker']}的{entry['theory']}（经语境改造）",
                characteristics={"frame":entry["transformed_frame"],"affinity":entry.get("perspective_affinity",[])}),
            perspective_B=Perspective(
                name=f"query 语境: {query[:40]}",
                characteristics={"frame":query}),
            claim_A=entry["transformed_frame"], claim_B=query,
            irreconcilable_points=[f"{entry['theory']}的预设: {entry['transformation_tension']}"],
            tension_type=derived_tt,
        ), source_skill="kailejiu-research", fold_count=1))
```

---

## 保留能力

### 网络检索（保留 R1）

`web_search_tavily` 作为图谱 fallback，非独立步骤。

### Tavily 精确文献检索模块（v3.5 新增）

`kailejiu_research_tavily.py` 提供独立的、可编程的文献检索能力，
专为 KL9-RHIZOME 的精确文献溯源场景设计。

**设计原则**:
- 只检索、不评价 — 返回原始文本片段 + 精确来源
- 不编造页码 — 只报数据源实际提供的信息
- 可被 `dialogical_activation()` 调用，也可独立使用

#### 核心函数

| 函数 | 用途 |
|:---|:---|
| `search(query, ...)` | 通用 Tavily 搜索，支持域名过滤/时间范围 |
| `search_book(author, title, ...)` | 书籍专用搜索，自动构建最优查询 + 学术域名过滤 |
| `extract_quote(result, keyword)` | 从搜索结果中提取包含关键词的段落上下文 |
| `format_for_kl9(result)` | 将搜索结果格式化为 KL9 可注入的 Markdown 上下文 |

#### search_book 参数说明

```python
def search_book(
    author: str,
    title: str,
    chapter: Optional[str] = None,   # 章节/概念关键词
    year: Optional[str] = None,      # 出版年份（作为查询词，非 recency 过滤）
    language: str = "zh",            # "fr" 法语原版 / "zh" 中译本 / "en" 英译本
    max_results: int = 5,
) -> Dict
```

**自动域名过滤**（学术站点优先）:
`persee.fr`, `cairn.info`, `jstor.org`, `gallimard.fr`, `presses-universitaires.fr`,
`books.openedition.org`, `archive.org`, `gallica.bnf.fr`

#### 在 dialogical_activation 中的集成方式

```python
def dialogical_activation(query: str) -> List[dict]:
    results = []
    candidates = _activate_from_graph(query, top_k=5)

    # v3.5: 学术标记直接触发 Tavily 文献检索
    if len(candidates) < 2 or _has_academic_markers(query):
        tavily_result = kailejiu_research_tavily.search(
            query=query, max_results=8, search_depth="advanced")
        if "error" not in tavily_result:
            candidates += _mine_perspective_concepts(
                tavily_result.get("results", []), query)

    for theory in candidates:
        entry = transform_in_context(theory, query)
        if entry:
            results.append(entry)

    if results:
        _emit_dialogical_tension(results, query)
    return results
```

#### 配置要求

环境变量 `TAVILY_API_KEY` 必须设置。未设置时所有函数返回 `{"error": "TAVILY_API_KEY not set"}`。

#### 独立使用

```bash
# 命令行
python scripts/kailejiu_research_tavily.py "Foucault panoptique 1975"

# Python 调用
from kailejiu_research_tavily import search_book
result = search_book("Foucault", "Surveiller et punir", "panoptique", "1975", "fr")
```


### 图谱写入（保留 R3，推迟，显式链接 TENSION_TYPES）

```python
# v3: 写入使用 graph v2 节点 schema + derived_tension_type
node_id = GB.store_concept(
    name=entry["theory"],
    definition=entry["transformed_frame"],          # v3: 单一 definition
    thinker=entry["thinker"], work="", field="",
    perspective_affinity=entry["perspective_affinity"],  # v3 新增
    tension_types=[entry["derived_tension_type"]],       # v3 新增
)
GB.create_edge(from_id=a, to_id=b,
               edge_label=f"irreconcilable:{entry['derived_tension_type']}",
               tension_source=entry["derived_tension_type"])
```

写入时机由 memory 技能（Persistence Layer）决定。

---

## 删除内容

| 删除项 | 原因 |
|:---|:---|
| **tier1/tier2/tier3** | v3 扁平化为 `definition`，匹配 graph v2 节点 schema |
| **R1→R2→R3→R4→R5 流水线** | 线性装配线与"同时折叠"原则冲突 |
| **confidence ≥ 0.75 门控** | 低置信度条目在对话式激活中可能产生有意义的张力 |
| **独占式单入口调用** | 改为 TensionBus 订阅 + 独立激活 |
| **quality_score() 质量评分** | 机械评分与对话式认知相悖 |
| **R4 孤立节点检查** | 推迟到 Persistence Layer |
| **R5 综合回复** | 交还 Dual Fold，本技能只负责激活 |
| **硬编码 TensionType.theoretical_vs_empirical** | v3 改为 _derive_tension_type 动态推导 |
| **_extract_theory_candidates 命名** | 重构为 _mine_perspective_concepts |

---

## 完整执行流程

```
query → research.activate(query)
         │
         ▼
  ┌──────────────────────────────────────┐
  │ dialogical_activation(query)         │
  │  1. _activate_from_graph()           │ ← 图谱优先
  │  2. web_search_tavily() → fallback   │ ← 网络补充
  │  3. _mine_perspective_concepts()     │ ← v3: 视角相关概念挖掘
  │  4. for each theory:                 │
  │     transform_in_context()           │ ← 对话式改造
  │     identify_transformation_tension()│ ← 张力识别
  │     _tag_perspective_affinity()      │ ← v3: 视角亲和度
  │     _derive_tension_type()           │ ← v3: 动态 TENSION_TYPES
  │  5. _emit_dialogical_tension()       │ ← v3: 动态 tension_type
  └──────────────┬───────────────────────┘
                 ▼
  Phase 1: Dual Fold 消费 → Perspective → TensionBus → expression/reasoner/soul
```

---

## 与 Constitutional DNA 的关系

1. **二重性存在** — 从理论框架的原始/改造二重性出发
2. **张力悬置** — 识别 `transformation_tension` 但不缝合
3. **概念对话** — 思想家是对话对象而非权威背书
4. **结构性情感** — 张力描述冷面（不煽情，不"深刻地指出"）
5. **拒绝收束** — 返回多路径并存，不给统一结论

---

> *v3 — tier1/2/3 全部移除。tension_type 动态推导。视角相关概念挖掘 → Phase 1 视角激活。
> KL9-RHIZOME 对话式激活层——与理论对话，而非检索征用。*

---

## KL9-RHIZOME 根茎适配

### 根茎定位
研究层不再是"检索代理"，而是"张力导向的对话式理论激活者"——接收 TensionBus 中的张力信号，从外部知识源中检索与当前张力相关的理论框架，并执行 transform_in_context() 改造而非直接引用。

### 订阅的张力类型
- EPISTEMIC → 检索与当前认知冲突相关的理论
- DIALECTICAL → 检索支持/反对双视角的理论
- EXISTENTIAL → 检索关于存在困境的理论框架

### 操作流程（对话式激活版）

**输入**: tension_context: Dict（含 query、perspective_A、perspective_B、tension_type）
**输出**: List[Dict]（含 theory、thinker、original_frame、transformed_frame、transformation_tension）

**步骤**:
1. **张力导向搜索**（替代旧"关键词检索"）
   - 从 tension_context 提取 tension_type
   - 映射到对应理论领域
   - 检索 top-k 相关理论框架

2. **对话式改造**（替代旧"直接引用"）
   - 对每个检索到的理论，调用 transform_in_context()
   - 将原始理论框架改造为 query 语境中的适用版本
   - 记录改造过程中产生的 transformation_tension

3. **改造张力反馈**
   - 将 transformation_tension 写回 TensionBus
   - 触发下一个折叠波次

### 与核心技能的关系
- **kailejiu-core**: 提供对话式激活的 DualState 上下文
- **kailejiu-graph**: 从图谱获取已有概念视图，避免重复检索
- **kailejiu-reasoner**: 检索结果注入推理折叠的 prompt 前缀
