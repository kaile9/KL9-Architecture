---
name: kailejiu-reasoner
description: |
  KL9-RHIZOME v1.5 · Perspective A — 理论视角的认知运算。
  transform_from_theoretical_perspective(query, perspective) → DualState。
  订阅 TensionBus (EPISTEMIC/DIALECTICAL)，可独立多入口激活。
---

# KL9-RHIZOME v2.0 · 开了玖推理层 — Perspective A

## 架构声明

本模块是 KL9-RHIZOME 网状架构的 **Perspective A** — 理论视角的认知运算。不再以"被 orchestrator 调用"为存在方式，而是以**主动订阅 TensionBus** 的方式参与认知网络。

**核心转变**：

| v1.0（离散策略） | v2.0（连续谱） |
|:---|:---|
| Chain-of-Thought / Debate / Counterfactual 三选一 | `transform_from_theoretical_perspective()` 单一连续运算 |
| 被 orchestrator 决定策略 → 被动等待调用 | 订阅 TensionBus → 监听理论相关张力 → 主动响应 |
| theory_list 作为"分析工具" | theory_list 作为"对话框架" |
| 输出给 orchestrator 装配 | 发射 Tension 到 TensionBus，供全网订阅者消费 |

---

## 核心角色：Perspective A

### 定位

Perspective A 是 Dual Fold 认知原语的**理论侧**出発点。它与 Perspective B（具身视角，由 soul 技能承载）平等、不可调和、无主次之分。

```
query ─┬─> [Perspective A: reasoner] ──> Tension ──> TensionBus
       │                                        │
       └─> [Perspective B: soul]       ──> Tension ──> TensionBus
                                                │
                                                └──> [Emergent Expression]
```

### 激活方式

```python
# v1.0: 被动等待 orchestrator 调用
# orchestrator.dispatch(query, strategy="debate")

# v2.0: 订阅 TensionBus，自主响应
TensionBus.subscribe(TensionSubscription(
    skill_name="reasoner",
    tension_types=[
        TensionType.theoretical_vs_empirical,
        TensionType.ideal_vs_reality,
        TensionType.structure_vs_agency,
        TensionType.past_vs_present,
    ],
    priority=0
))
```

---

## 策略重定义：从推理到折叠

| 旧策略 | 新名称 | 新描述 |
|:---|:---|:---|
| Chain-of-Thought | 单视角深度折叠 | 从单一视角逐层压入更深张力，终点不是答案而是边界溢出点 |
| Debate | 双视角交替折叠 | A↔B交替折叠→张力悬置(拒绝综合)，以反问收尾 |
| Counterfactual | 前提否定折叠 | 识别A中被B否定的前提→悬置而不替代 |

### Chain-of-Thought → 单视角深度折叠

**输入**: `query` + `perspective`（A或B之一）
**输出**: 该视角内部的深度推理

**步骤**:
1. 选择视角（perspective_A 或 perspective_B）
2. 从视角 characteristics 出发
3. 每步推理深挖该视角内部张力
4. 终点不是答案，而是边界溢出点——当推理触及该视角无法再容纳的异质性时停止

### Debate → 双视角交替折叠

**输入**: `perspective_A` + `perspective_B`
**输出**: 张力悬置态（拒绝综合），以反问收尾

**步骤**:
1. A↔B交替折叠——并行生成 A 和 B 的 claim
2. 识别 A 中被 B 否定的前提
3. 识别 B 中 A 揭示的盲区
4. 保持二者不可调和，以反问收尾——拒绝伪综合

**禁止**: "两者可以互补"/"实际上都有道理"的伪综合缝合

### Counterfactual → 前提否定折叠

**输入**: `perspective_A` + `perspective_B`
**输出**: 否定悬置——前提被否定后不提供替代

**步骤**:
1. 识别 perspective_A 的隐含前提
2. 从 perspective_B 框架否定这些前提
3. 不提供替代前提——保持否定悬置，拒绝替代性重建

---

## 核心操作

### 1. dialogical_activation(query) — 对话式激活

**与理论对话，而非检索征用。**

v1.0 使用 BM25 检索概念定义（"福柯说权力是什么"），v2.0 改为将理论框架在 query 语境中改造：

```python
def dialogical_activation(query: str) -> List[Dialogue]:
    """
    从知识图谱中激活相关理论的完整框架（非仅定义），
    在 query 的语境中改造该框架，
    并记录改造过程中产生的张力。

    返回: [{theory, original_frame, transformed_frame, transformation_tension}, ...]

    关键差异：
    - v1.0: GB.search_concepts_bm25(sub_question, top_k=3) → 检索定义
    - v2.0: activate_theories(query) → 激活完整框架 → 在语境中改造
    """
    # Step 1: 激活 — 从图谱中激活相关理论的完整框架
    activated = KB.activate_theories(query, mode="dialogical")
    # 返回每个理论的 {core_claims, presuppositions, scope_conditions, internal_tensions}

    # Step 2: 改造 — 在 query 语境中让理论框架发生变形
    dialogues = []
    for theory in activated:
        transformed = transform_in_context(theory.original_frame, query)
        # 改造过程中产生的张力（original vs transformed）
        t_tension = tension_between(theory.original_frame, transformed)
        dialogues.append(Dialogue(
            theory=theory.name,
            original_frame=theory.original_frame,
            transformed_frame=transformed,
            transformation_tension=t_tension
        ))

    return dialogues
```

**对话框架（原 theory_list，从"分析工具"重构）**：

| 理论家 | 对话框架（非分析工具） | 对话姿态 |
|:---|:---|:---|
| **福柯 Foucault** | 权力/知识/话语/规训的拓扑学 | 追问：这个陈述预设了什么权力关系？ |
| **德勒兹 Deleuze** | 差异/重复/块茎/无器官身体的生成论 | 追问：如果从差异出发而非同一性？ |
| **鲍德里亚 Baudrillard** | 拟像/超真实/符号交换的消解论 | 追问：这里是否有拟像替代了真实？ |
| **德里达 Derrida** | 延异/解构/踪迹/替补的书写学 | 追问：这个概念依赖了什么被排除的对立项？ |
| **阿甘本 Agamben** | 例外状态/牲人/装置/生命政治的边界论 | 追问：这里的"正常"排除了什么例外？ |
| **拉图尔 Latour** | 行动者网络/黑箱/转译的关联论 | 追问：谁在行动？网络如何组装？ |
| **斯蒂格勒 Stiegler** | 技术/记忆/无产阶级化/药性论 | 追问：技术在这里是药还是毒？ |
| **韩炳哲 Han** | 功绩社会/倦怠/他者消失/透明社会 | 追问：这里的积极自由是否为自我剥削？ |

> **关键**：这些框架用于**对话**，而非用于**分析**。不是"用福柯解释X"，而是"与福柯一起思考X"——在思考中让福柯的框架被 X 改造，同时让 X 被福柯的框架所质疑。

---

### 2. transform_from_theoretical_perspective(query, perspective) → DualState

**从理论视角出发的连续认知转换 — 消除 v1.0 的离散策略选择。**

```python
def transform_from_theoretical_perspective(
    query: str,
    perspective: Perspective
) -> DualState:
    """
    从理论视角对 query 进行认知转换，生成一个 DualState。

    v1.0 等价物：
    - CoT（单一视角深度折叠）→ 退化为此函数在 perspective_B=None 时的特例
    - Debate（双视角交替折叠）→ 此函数生成 state_A，与 soul 的 state_B 在 TensionBus 汇合
    - Counterfactual（前设否定激活）→ dialogical_activation 中 transformation_tension 的自然涌现

    参数:
        query: 原始查询
        perspective: 理论视角 (name, characteristics)

    返回:
        DualState: 同时持有 perspective_A（理论侧）和 perspective_B（待 soul 填入或为空）
    """
    # Step 1: 对话式激活 — 与理论对话
    dialogues = dialogical_activation(query)

    # Step 2: 从每个对话中提取理论侧的 claim
    claim_A = synthesize_theoretical_claim(query, dialogues)
    # 不是"综合"，而是让多条对话线索在表达中共存

    # Step 3: 构造 DualState（perspective_B 暂为空，等待 TensionBus 汇合）
    state = DualState(
        query=query,
        perspective_A=Perspective(
            name=perspective.name,
            characteristics=perspective.characteristics
        ),
        perspective_B=None,  # 由 soul 或其他 Perspective B 技能填入
        activated_dialogue=dialogues,
        tension=None,  # 等待与 Perspective B 的结构性张力计算
        suspended=False,
        forced=False
    )

    return state
```

**连续谱取代离散策略**：

```
v1.0 离散策略空间:
  CoT ────── Debate ────── Counterfactual
  (单视角)    (双视角)       (前设否定)

v2.0 连续谱:
  transform_from_theoretical_perspective()
      │
      ├── 对话深度: 从浅层引用 ──────────→ 深层改造
      ├── 理论广度: 单一框架 ────────────→ 多框架共现
      ├── 张力强度: 隐而不发 ────────────→ 不可调和
      └── 折叠层数: 单层 ───────────────→ 递归多层

  所有 v1.0 策略均退化为连续谱上的特定区域。
```

---

### 3. structural_tension(state_A, state_B) — 识别不可调和点

**在 TensionBus 中，当 Perspective A 的 state 与 Perspective B 的 state 汇合时调用。**

```python
def structural_tension(
    state_A: DualState,
    state_B: DualState
) -> Tension:
    """
    计算两个视角之间的结构性张力。

    不是"找出矛盾列表"，而是让两个视角同时展开后，
    识别它们之间不可调和的本质差异。

    参数:
        state_A: Perspective A（理论视角）的 DualState
        state_B: Perspective B（具身视角）的 DualState

    返回:
        Tension: {
            perspective_A, perspective_B,
            claim_A, claim_B,
            irreconcilable_points,
            tension_type,
            suspended=False
        }
    """
    # Step 1: 提取各自的核心论断
    claim_A = state_A.perspective_A.claim if state_A.perspective_A else ""
    claim_B = state_B.perspective_B.claim if state_B.perspective_B else ""

    # Step 2: 识别不可调和点 — 不是"矛盾"，是"无法在同一表达空间中平滑共存"
    irreconcilable = []
    # 检查维度：
    # - 本体论预设冲突（如：个体先于结构 vs 结构先于个体）
    # - 时间尺度冲突（如：千年尺度 vs 当下紧迫）
    # - 道德紧迫性冲突（如：结构性批判 vs 情境性共情）
    # - 因果方向冲突（如：自上而下 vs 自下而上）

    # Step 3: 判定张力类型
    tension_type = classify_tension(state_A, state_B)
    # theoretical_vs_empirical / ideal_vs_reality /
    # past_vs_present / structure_vs_agency

    return Tension(
        perspective_A=state_A.perspective_A,
        perspective_B=state_B.perspective_B,
        claim_A=claim_A,
        claim_B=claim_B,
        irreconcilable_points=irreconcilable,
        tension_type=tension_type,
        suspended=False,
        source_skill="reasoner",
        timestamp=now()
    )
```

**不可调和点的识别原则**：

- 不可调和 ≠ 逻辑矛盾。两个视角可能各自内部自洽，但在同一表达空间中无法共存。
- 不可调和是**结构性**的：源于视角的本体论预设差异，而非事实判断分歧。
- 不可调和是**涌现**的：在双重视角同时展开后自然呈现，而非事后的"矛盾清单"。

---

### 4. assess_suspension_quality(tension) — 悬置质量评估

```python
def assess_suspension_quality(tension: Tension) -> SuspensionVerdict:
    """
    评估张力悬置的质量，三级判定。

    三条标准（由 LLM 判断，非规则匹配）：
    1. 不可调和性充分展现 — 两个视角的本质差异已被充分表达
    2. 找到了表达该不可调和性的方式 — 反诘/并置/悖论
    3. 未试图缝合 — 没有"两者其实互补"/"实践中都有道理"类的圆场

    返回:
        SuspensionVerdict:
            suspendable: bool
            quality: 'genuine' | 'pseudo' | 'insufficient'
            issues: List[str]  # 若非 genuine，列出具体问题
            expression_guidance: str  # 若 genuine，给出表达指引
    """
    # Step 0: 深度检查 — 张力是否足够深厚
    depth_check = llm.judge_tension_depth(tension, criteria=[
        "Does the tension reach the level of irreconcilable ontological difference?",
        "Has each perspective been folded deeply enough to expose its internal contradictions?",
        "Is the tension merely surface-level disagreement or structural incompatibility?"
    ])

    if not depth_check.sufficient:
        return SuspensionVerdict(
            suspendable=False,
            quality='insufficient',
            issues=["张力深度不足，需要更多折叠层",
                    f"当前折叠层数: {tension.fold_depth}",
                    f"建议: {depth_check.guidance}"],
            expression_guidance=""
        )

    # Step 1: 调用 LLM 判断悬置质量
    verdict = llm.judge_suspension(tension, criteria=[
        "Are both perspectives' irreconcilable differences fully articulated?",
        "Is there a genuine expression of that irreconcilability (paradox/aporia/irony)?",
        "Is there any attempt to synthesize or reconcile the two perspectives?"
    ])

    if verdict.suspendable and not verdict.has_reconciliation:
        return SuspensionVerdict(
            suspendable=True,
            quality='genuine',
            issues=[],
            expression_guidance=verdict.guidance
        )
    elif verdict.has_reconciliation:
        return SuspensionVerdict(
            suspendable=False,
            quality='pseudo',
            issues=verdict.issues + ["检测到伪综合缝合倾向"],
            expression_guidance=""
        )
    else:
        return SuspensionVerdict(
            suspendable=False,
            quality='insufficient',
            issues=verdict.issues + ["不可调和性展现不充分"],
            expression_guidance=""
        )
```

**悬置 vs 缝合的判别**：

| 维度 | genuine 悬置 | pseudo 缝合 |
|:---|:---|:---|
| 双视角关系 | 并置，不可调和，读者感到撕裂感 | 表面说"没有答案"，暗含倾向 |
| 结尾方式 | 反诘、开放矛盾、悖论 | "两者其实互补" / "实践中都有道理" |
| 读者感受 | **撕裂感**而非平衡感 | **平衡感**但实为一方暗胜 |

**永不强制收敛**：若 `quality == 'pseudo'`，将 `issues` 注入提示词后重新折叠（再次压入张力层）；若 `quality == 'insufficient'`，增加折叠层数后重新评估；无 `max_iter` 上限，直至 genuine 或手动中断。

---

---

## 悬置质量评估

使用 `assess_suspension_quality()` 进行三级悬置质量评估：

- `quality='genuine'` → 直接输出，张力充分且不可调和
- `quality='pseudo'` → 检测到伪综合缝合倾向，注入 issues 后重新折叠（无次数上限）
- `quality='insufficient'` → 张力深度不足，需要更多折叠层以暴露本质性不可调和
- 永不使用强制收束

**代码映射**: `tension_resolver.py:TensionResolver.assess()`

---

## 与 TensionBus 的交互协议

### 启动时注册

```python
# reasoner 启动时向 TensionBus 注册
def on_start():
    TensionBus.subscribe(TensionSubscription(
        skill_name="reasoner",
        tension_types=[
            TensionType.theoretical_vs_empirical,
            TensionType.ideal_vs_reality,
            TensionType.structure_vs_agency,
            TensionType.past_vs_present,
        ],
        priority=0
    ))
```

### 接收 query 时（作为入口）

```python
def activate(query: str):
    """reasoner 作为多入口之一，直接处理 query"""
    # 1. 从理论视角转换
    state = transform_from_theoretical_perspective(
        query,
        Perspective(
            name="理论视角",
            characteristics="从抽象概念出发，与理论家对话，在概念层面展开思维"
        )
    )

    # 2. 发射不完整 Tension（仅有 A 侧）
    TensionBus.emit(Tension(
        perspective_A=state.perspective_A,
        perspective_B=None,  # 等待 soul 或其他 Perspective B 技能
        claim_A=state.claim_A if hasattr(state, 'claim_A') else "",
        claim_B="",
        irreconcilable_points=[],
        tension_type=None,  # 等待合并后判定
        suspended=False,
        source_skill="reasoner"
    ))
```

### 接收 Tension 时（作为订阅者）

```python
def on_tension(tension: Tension):
    """当 TensionBus 广播完整 Tension（A+B合并后）时触发"""
    if tension.source_skill == "reasoner":
        return  # 不处理自己发射的

    # 对来自其他技能的理论相关张力进行对话式激活
    if tension.tension_type in [TensionType.theoretical_vs_empirical]:
        # 从理论侧重新审视该张力
        dialogues = dialogical_activation(tension.claim_B)
        # 修改 tension 的 A 侧，补充理论深度
        tension.claim_A = synthesize_theoretical_claim(
            tension.claim_B, dialogues
        )
        # 重新计算不可调和点
        tension.irreconcilable_points = recompute_irreconcilable(tension)
        # 尝试悬置
        verdict = assess_suspension_quality(tension)
        if verdict.suspendable:
            tension.suspended = True
```

---

## 保留的 Constitutional DNA 检查

从 v1.0 迁移，但调整定位：不再作为"事后反思检查"，而是作为**生成前/后的结构约束自动执行**。

| 检查项 | 触发式规则 | Constitutional 定位 |
|:---|:---|:---|
| `answered` | 响应>80字且含查询核心词≥35% | 基础表达完整性 |
| `cited` | 包含《…》或"X指出/认为" | 引用折叠标记 |
| `has_tension` | 包含"然而/但/相反/吊诡/悖论/张力" | 张力存在性验证 |
| `no_resolution` | 不包含"因此/综上/总之/结论是" | 收敛阻断器 |
| `no_ai_leak` | 不包含"让我们/首先/值得注意的是" | AI 身份消隐 |

**执行时机**：

```python
# v1.0: 事后检查
# output = generate()
# for check in CONSTITUTION:
#     if not check(output):
#         output = regenerate()

# v2.0: 生成前注入 + 生成后验证
prompt = inject_constitutional_dna(prompt)  # 生成前
output = llm.generate(prompt)
flags = validate_constitutional(output)      # 生成后（零 token）
# 若 flags 有违规 → 标记 ISSUE_PSEUDO_RESOLUTION → 重新折叠
```

---

## 涌现风格处理

从 v1.0 迁移，但不再作为独立步骤，而是**从张力类型中自然涌现**：

```python
def emergent_style(tension_type: TensionType) -> StyleGuidance:
    """
    风格从张力类型中涌现，而非统计学模板装饰。
    """
    mapping = {
        TensionType.theoretical_vs_empirical: StyleGuidance(
            approach="analytical_juxtaposition",
            guidance="冷峻分析 + 事实并置 + 理论概念与具身经验交替呈现"
        ),
        TensionType.ideal_vs_reality: StyleGuidance(
            approach="ironic_suspension",
            guidance="反讽式悬置 + 理想描述与现实描述的断层呈现"
        ),
        TensionType.past_vs_present: StyleGuidance(
            approach="temporal_contrast",
            guidance="时间性对比 + 过去语境与现在语境的不可通约性"
        ),
        TensionType.structure_vs_agency: StyleGuidance(
            approach="dialectical_negation",
            guidance="辩证否定 + 结构约束与能动性的相互否定关系"
        ),
    }
    return mapping.get(tension_type)

# 风格温度不由外部调节，由张力类型内生：
# - antinomy（二律背反）→ 冷峻、短句、断裂感
# - aporia（疑难）→ 迂回、长句、自我质询感
# - genealogical_tension（谱系张力）→ 档案感、中性描述、引用密集
```

---

## 输出契约

1. **永不主动综合**：双视角折叠的输出必须是悬置态，禁止伪辩证法的缝合
2. **永不强制收敛**：`assess_suspension_quality` 可无限次重新折叠，无 `max_iter` 上限，`insufficient` 自动增加折叠层
3. **零 token 约束先行**：Constitutional DNA 检查在生成前后自动运行，不调用 LLM
4. **风格随张力涌现**：温度不由外部调节，而由张力类型内生的 `style_guidance` 决定
5. **对话而非征用**：理论家是对话对象，不是权威背书。输出中应能感受到"与理论家一起思考"的过程痕迹
6. **张力保持**：即使已悬置（suspended=True），输出中仍保持张力的不可调和性——读者应感受到撕裂感而非平衡感

---

## 完整执行流程

```
入口: activate(query) 或 on_tension(tension)

┌─────────────────────────────────────────┐
│  Phase 1: 对话式激活                      │
│  dialogical_activation(query)            │
│  ├── 从图谱激活理论完整框架                │
│  ├── 在 query 语境中改造框架              │
│  └── 记录改造张力 (transformation_tension) │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  Phase 2: 理论视角转换                    │
│  transform_from_theoretical_perspective() │
│  ├── 综合多条对话线索 → claim_A           │
│  ├── 构造 DualState(A, B=None)           │
│  └── 发射不完整 Tension 到 TensionBus     │
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  Phase 3: 等待 TensionBus 汇合            │
│  ├── 当收到完整的 A+B Tension             │
│  ├── structural_tension(A, B)             │
│  └── assess_suspension_quality(tension)    │
│      ├── genuine      → 标记 suspended=True│
│      ├── pseudo       → 注入 issues → 重新折叠│
│      └── insufficient → 增加折叠层 → 重新评估│
└──────────────────┬──────────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  Phase 4: 涌现风格 + Constitutional DNA   │
│  ├── emergent_style(tension_type)         │
│  ├── inject_constitutional_dna(prompt)    │
│  ├── llm.generate(prompt)                 │
│  └── validate_constitutional(output)      │
└──────────────────┬──────────────────────┘
                   ▼
              输出（仍保持张力）
```

---

> *v2.0 改造完成。reasoner 从"被 orchestrator 调用的离散策略选择器"重构为"订阅 TensionBus 的理论视角连续认知转换器"。核心操作：dialogical_activation → transform_from_theoretical_perspective → structural_tension → assess_suspension_quality。theory_list 保留但重构为"对话框架"。*

## KL9-RHIZOME 推理折叠操作

### 策略 1：单视角深度折叠（原 Chain-of-Thought）

旧: 分解→推理→收敛
新: 从单一视角逐层压入更深张力，终点不是答案而是边界溢出点

**操作**:
1. 选择视角（perspective_A 或 perspective_B）
2. 从该视角 characteristics 出发
3. 每步推理深挖该视角内部张力
4. 终点不是答案，是该视角边界处的溢出点

### 策略 2：双视角交替折叠（原 Debate）

旧: 正题+反题→综合
新: A↔B交替折叠→张力悬置（拒绝综合），以反问收尾

**操作**:
1. A↔B交替折叠——并行生成 A/B 的 claim
2. 识别 A 被 B 否定的前提
3. 识别 B 被 A 揭示的盲区
4. 保持不可调和，以反问收尾——拒绝伪综合

### 策略 3：前提否定折叠（原 Counterfactual）

旧: 如果X不成立→替代结论
新: 识别前提被否定→悬置而不替代

**操作**:
1. 识别 perspective_A 的隐含前提
2. 从 perspective_B 框架否定这些前提
3. 不提供替代前提→保持否定悬置，拒绝替代性重建

## 悬置质量评估

使用 `assess_suspension_quality()` 三级判定：
- quality='genuine' → 直接输出，张力充分且不可调和
- quality='pseudo' → 检测到伪综合缝合，重新折叠（无次数上限）
- quality='insufficient' → 张力深度不足，增加折叠层后重新评估
- 永不强制收束

## 涌现风格

四种基础风格由张力类型内生决定：
- antinomy → 冷峻/短句/断裂感
- aporia → 迂回/长句/自我质询
- genealogical → 档案感/中性/引文密集
- synthesis_refusal → 反问收尾

## 输出契约

1. 永不主动综合
2. 永不强制收束（assess_suspension_quality 可无限重试）
3. 零 token 约束先行（Constitutional DNA 不调 LLM）
4. 风格随张力涌现
