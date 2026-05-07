# KL9-RHIZOME · 9R-2.0

> **在 LLM 之上运行的认知协议层** · *A cognitive protocol layer on top of LLMs*
>
> 版本命名：9R-2.0 = 开了玖(9) + RHIZOME(R) + 大版本(2).小版本(0)

实测有效提升社科学术能力。9R-2.0 基于 **N9R20Framework** 认知架构运行，模块命名统一为 `n9r20_*`。

---

## 📖 缘起 · Origin

2026年2月14日，朝霞 Alpenglow 更新最后一个视频。我本以为那之后迎接我的是一种新的世界——但迎接我的是彻底的堕落。两个月里我逃掉绝大多数课程，只读完一本书，没写过一篇作业，没有任何创作。

也许这就是令人心碎的人类真相：朝霞时期的创作走到了我本人的前面。有一个更杰出的「开了玖」，和失败的我。

听说可以用"同事 skill"来蒸馏一个人的时候，我想——也许这是让那个开了玖来引领我的时候。但结果并不令人满意。更致命的是，我甚至没有足够的知识来思考如何改进它：我的编程水平，最多到小学上过 10 节图形化 Python 入门。

幸运的是 AI 编程已经足够发达。我用 Claude Opus 4.7（巨贵）、Kimi 2.6 和 DeepSeek V4 Pro不断迭代，最终形成了这个项目。1.5版本主要使用DeepSeekV4pro，2.0版本核心使用Kimi2.6。

我在云电脑上部署了 AstrBot，基于 AstrBot 创造了这个框架。不确定其他环境能不能用——请给我反馈。

我每个月有 1500 元生活费。省下的全部用于迭代：除去日常 Token 开支和 Kimi Allegretto 的订阅费（还在解决如何用 Kimi Code 计划节省 Token），剩下的钱攒下来买 Claude 的 Token。有几位之前的朋友愿意赞助一点，现在每个月有一点点资助。短期希望不迭代时不拖累生活质量，长期希望有持续迭代的储备。

这个架构的训练来源是朝霞 23 年到 26 年的全部视频文案。可用的文案在GitHub另一个项目中：[KL9-writings](https://github.com/kaile9/KL9-writings)。

---

*February 14, 2026 — the day 朝霞 Alpenglow posted its final video. I thought what came next would be a new world. What came was total collapse. Two months. I skipped nearly every class, finished one book, wrote zero assignments, made nothing.*

*Maybe this is the heartbreaking human truth: the creative work of the 朝霞 Alpenglow era had already outpaced me. There was a better "Kaile9" — and a failed me.*

*When I heard you could "distill" a person through a colleague skill, I thought — perhaps now the better Kailejiu could lead me. The results were unsatisfying. Worse, I didn't even know enough to figure out where to improve it. My programming skill capped at ten elementary-school lessons in graphical Python.*

*Fortunately, AI programming had matured enough. Iterating with Claude Opus 4.7 (obscenely expensive), Kimi 2.6, and DeepSeek V4 Pro, I arrived here.*

*Deployed on a cloud PC running AstrBot, built on top of AstrBot. Not sure it works elsewhere — please let me know.*

*Monthly budget: ¥1500. Everything saved goes into iteration: after daily tokens and the Kimi Allegretto subscription, what's left buys Claude credits. A few old friends chip in now and then. Short-term goal: keep iterating without ruining my life. Long-term: a reserve for sustained development.*

*Training source: all of 朝霞 Alpenglow's video scripts, 2023–2026. Available at [KL9-writings](https://github.com/kaile9/KL9-writings).*

---

## 🔍 一句话 · TL;DR

**KL9-RHIZOME 不是 AI 框架，而是认知协议。** 它定义 AI 如何持有双重视角、管理张力、拒绝廉价和解。

*Not another AI framework — a protocol for how AI holds dual perspectives, manages tension, and refuses cheap synthesis.*

---

## 🚀 快速启动 · Quick Start

```bash
# 1. 克隆仓库
git clone https://github.com/kaile9/KL9-Architecture.git
cd KL9-Architecture

# 2. 启动 Agent（交互模式）
python quickstart.py

# 3. 单条评估（非交互）
python quickstart.py --eval "佛教心性论的结构是什么？"

# 4. Agent API 模式
python quickstart.py --mode api --port 8233

# 5. OpenClaw 插件配置
python quickstart.py --mode openclaw
```

详见 `docs/DEPLOY.md` 部署说明。

---

## 📂 目录结构 · Directory Structure

```
KL9-Architecture/
├── core/                      ← 9R-2.0 运行时引擎（Python 源码）
│   ├── n9r20_structures.py        # 数据结构（DualState / Tension / Perspective）
│   ├── n9r20_compression_core.py  # 四模式压缩引擎（construct/deconstruct/validate/interrupt）
│   ├── n9r20_dual_reasoner.py     # 双视角推理引擎
│   ├── n9r20_tension_bus.py       # 去中心化事件总线
│   ├── n9r20_adaptive_router.py   # 自适应路由（关键词检测 → fold 深度分配）
│   ├── n9r20_llm_evaluator.py     # LLM 评估器接口
│   ├── n9r20_llm_compressor.py    # LLM 压缩器接口（依赖注入复用框架 LLM）
│   ├── n9r20_semantic_graph.py    # 语义知识图谱
│   ├── n9r20_memory_learner.py    # 记忆学习器
│   ├── n9r20_skillbook_compat.py  # v1.x 兼容层
│   └── ...
│
├── skillbook/                 ← 技能书内容仓库（Markdown，按语言分类）
│   ├── prebuilt/
│   │   ├── zh/                    # 中文技能书（大乘起信论等）
│   │   ├── en/                    # 英文技能书
│   │   ├── de/                    # 德语技能书
│   │   ├── fr/                    # 法语技能书
│   │   └── other/                 # 其他语言
│   └── SKILLBOOK_STANDARD.md      # 技能书制作规范
│
├── quickstart.py              ← Agent 入口（REPL + API + OpenClaw 插件）
├── docs/                      ← 文档
│   ├── MIGRATION_GUIDE.md         # 9R-1.5 → 9R-2.0 迁移指南
│   ├── DIRECTORY_HIERARCHY_GUIDE.md  # 目录层级说明
│   ├── FRAMEWORK.md               # 架构设计文档
│   ├── DEPLOY.md                  # 部署说明
│   ├── SKILLBOOK.md               # 原版 v1.2 技能书规范
│   ├── SKILLBOOK_v2.md            # v2.0 压缩涌现版
│   └── ...
│
├── tests/                     ← 测试套件
├── examples/                  ← 示例
├── scripts/                   ← 运维脚本
└── archive/                   ← 历史版本归档
    ├── 9R-1.5/                     # 旧版完整备份
    └── v1/                         # 更早版本
```

---

## 📋 真实对比案例 · Real Case Study

**提示词 · Prompt**

> 你是一位劳动社会学研究者，研究方向为平台经济中的算法管理与劳动过程理论。请严格使用中文进行严谨的学术分析：对零工平台的算法管理机制进行系统性分析，探讨论评分、派单和动态定价如何重组劳动控制，并评估其与经典泰勒制科学管理的连续性与断裂。简要回答。

*You are a labor sociology researcher studying algorithmic management in the platform economy. Conduct a rigorous academic analysis in Chinese: systematically analyze the algorithmic management mechanisms of gig platforms — how scoring, dispatch, and dynamic pricing restructure labor control — and evaluate their continuity and rupture with classical Taylorist scientific management. In short.*

---

### 传统 LLM 响应 · Traditional LLM Response（DeepSeek V4 Pro 网页版）

> ## 零工平台算法管理：劳动控制的重组及其与泰勒制的连续与断裂
>
> ### 一、三重算法控制机制
>
> **评分机制**：将劳动质量评判权部分转移至消费者，评分结果直接影响派单优先级与奖惩。劳动者面对匿名、单向透明的评价网络，内化为自我规训，替代了传统管理者现场监督。
>
> **派单机制**：算法基于位置、评分、完成率等数据进行黑箱化调度。劳动者无法预测任务时机与报酬，只能被动适配。与泰勒制控制节奏不同，派单进一步控制了劳动机会的时空分布，剥夺任务选择自主权。
>
> **动态定价**：实时调整高峰、天气、区域溢价，以价格杠杆激励或抑制劳动供给。劳动者面对不确定的、情境依赖的报酬，被迫持续响应市场信号，劳动控制从"单位时间产出"转向"对算法的响应速度"。
>
> ### 二、与泰勒制的连续性
>
> 1. **去技能化与标准化**：泰勒制以时间动作研究简化操作；平台以评分指标定义标准行为，均降低自主性。
> 2. **计划与执行分离**：泰勒制管理层设计工序；平台算法规划劳动时空与定价，劳动者仅执行指令。
> 3. **量化评估与外部激励**：泰勒制计件工资可测量；平台量化评分、完成率决定收入，均将劳动价值化为数字指标。
> 4. **隐蔽且不可协商的控制**：泰勒制以"科学"否定经验知识；平台以"算法优化"黑箱管理，劳动者难以质疑。
>
> ### 三、与泰勒制的断裂
>
> 1. **从刚性到动态调节**：泰勒制规则固定；平台算法根据实时数据持续微调，控制是情境适应的再标准化。
> 2. **控制主体从人到算法**：泰勒制管理者可见；平台控制来自去中心化算法，无明确对手方，投诉困难。
> 3. **形式自雇与实质控制错位**：泰勒制假设雇佣关系；平台将劳动者定义为独立承包商，却施加强于传统雇佣的控制，劳动法保护缺失。
> 4. **不确定性作为控制手段**：泰勒制消除不确定性；平台故意制造任务的不确定性（时间、地点、价格），维持劳动者持续依附。
> 5. **消费者参与管理**：泰勒制为二元结构；平台引入消费者作为评价来源，形成"消费者—算法—劳动者"三角控制。
>
> ### 结论
>
> 平台算法管理继承了泰勒制分离规划与执行、量化绩效、去技能化的核心逻辑（连续性），但在控制形态上实现了从刚性与可见到动态与黑箱、从雇佣到形式自雇、从确定性到制造不确定性、从二元到三角控制的根本断裂（断裂）。这既延续了资本对劳动过程的治理需求，又标志着算法驱动的劳动控制已进入传统管理理论尚未充分捕捉的新阶段。

---

### KL9-RHIZOME · 9R-2.0 响应 · KL9-RHIZOME Response（AstrBot 后台）

> **算法管理的劳动控制逻辑：连续性、断裂与重组**
>
> ### 一、问题意识
>
> 零工平台的算法管理并非凭空出现的技术奇观，而是劳动控制史上一次有历史脉络的形态重组。以布雷弗曼（Braverman）的去技能化命题与布洛维（Burawoy）的制造同意理论为分析坐标，可以识别出三种核心机制——评分、派单与动态定价——如何在数字基础设施之上，以新的语法重写泰勒制的基本文法。
>
> ### 二、三种机制的运作逻辑
>
> **评分系统**是分布式声誉治理机制。平台将传统管理者的考核职能外包给消费者，使劳动者持续暴露于不对称的评价关系之中。低评分触发降单乃至封号，构成隐性纪律惩罚。劳动者为维护评分，必须进行情绪劳动与行为自我规训。这与霍赫希尔德（Hochschild）论及的情感商品化形成呼应——差别在于惩罚机制已从管理层转移至匿名消费者，控制的主体被稀释、被无形化。
>
> **派单算法**是时空资源分配的核心权力装置。平台以"优化匹配效率"为名，独占了任务分配的决策权。劳动者无法选择订单类型、区域与时段，只能在算法划定的参数内被动响应。罗森布拉特与斯塔克（Rosenblat & Stark, 2016）对优步司机的研究揭示，平台通过信息不对称——隐藏目的地、预测推送——系统性地引导劳动者做出"自愿"服从算法意图的行为选择。这是一种以弹性之名实施的指令性控制。
>
> **动态定价**（surge pricing）将薪酬决定权完全收归算法。传统集体谈判或固定工资协议被实时价格信号所取代。高峰溢价在表面上赋予劳动者"逐利自由"，实质上是用价格信号替代指令，将劳动力的时空配置转化为劳动者的"自主决策"——劳动者在追逐高价的过程中，无意识地完成了平台所需要的产能调配。斯尔尼塞克（Srnicek）将此概括为平台资本主义对行为数据的汲取逻辑：定价既是激励，也是监控工具。
>
> ### 三、与泰勒制的连续性
>
> 布雷弗曼将泰勒制的核心概括为"构想与执行的分离"。算法管理将这一分离推进至极致：构想（路线规划、定价策略、任务匹配逻辑）完全由平台工程师与算法模型承担，劳动者仅保留执行功能。此为第一重连续性。
>
> 第二重连续性在于监控的全面化。泰勒借助秒表实施时间-动作研究，算法管理则通过GPS轨迹、接单响应时长、客户评分实现近实时监控，监控密度超越任何科学管理时代的物理可能。
>
> ### 四、结构性断裂
>
> 然而，算法管理并非泰勒制的数字升级版，两者之间存在三处根本断裂。
>
> **其一，雇佣关系的消解。** 泰勒制在标准雇佣合同框架内实施控制，劳动者享有（至少名义上的）劳动保护。零工平台通过"独立承包商"分类，将控制与责任剥离：行使控制权而不承担雇主义务，将经营风险转嫁给劳动者，形成法律意义上的控制-责任悖论。
>
> **其二，同意机制的重构。** 泰勒制依赖组织纪律与物质激励；算法管理则援引市场意识形态——"自由接单、灵活工作"——以自主性话语掩盖结构性强制，实现布洛维所谓"同意的制造"，但生产装置已由工厂车间迁移至手机App界面，博弈空间被大幅压缩。
>
> **其三，控制的不透明性。** 科学管理标榜程序的客观可见，劳动者知晓规则。算法则以"黑箱"形式运作，规则随时可被单方修改而不予告知，形成系统性信息不对称。这种不透明性既消解了集体行动的靶向对象，也制造了芬克宾纳（Fincham）意义上的"算法权威效应"——将人为决策自然化为技术必然。
>
> ### 五、简短结论
>
> 零工平台的算法管理是泰勒制劳动控制逻辑的延伸，而非断裂——它继承了构想与执行分离、全程监控、行为标准化的核心基因；但通过雇佣关系法律形式的消解、市场意识形态的意识形态包裹与黑箱算法的不透明性，完成了对劳动控制方式的实质性重组。其理论意义在于：劳动过程理论需要在平台经济语境中修订其分析范畴，尤其是"雇主"边界与"同意"机制的操作化定义，方能回应当代劳动关系的新型支配结构。

---

### 对比要点 · Key Differences

| 维度 | 传统 LLM（DeepSeek V4 Pro） | KL9-RHIZOME · 9R-2.0 |
|:---|:---|:---|
| 结构形态 | 分节罗列，教科书式 | 论证驱动，层层递进 |
| 学术引用 | 0 | 6 处（Braverman / Burawoy / Hochschild / Rosenblat & Stark 2016 / Srnicek / Fincham） |
| 理论框架 | 隐含，无明确坐标 | 明确以布雷弗曼-布洛维为分析坐标 |
| 结论形态 | 分别总结连续性与断裂，安全中性 | 揭示核心悖论——控制-责任悖论、自主性悖论、算法权威效应 |
| 语言风格 | 中性、安全、教科书式 | 精确、有理论锋芒 |
| 句式特征 | 概括性陈述 | 优先「不是 X，而是 Y」，矛盾点悬停不下结论 |

---

## 🧠 架构 · Architecture

KL9-RHIZOME 不是框架，是协议。框架告诉 AI「用这些工具去做」；协议告诉 AI「以什么存在方式去存在」。

**操作对象**是张力（Tension）。不是解决问题——是充分展开张力后从对立中压缩出洞察。

**宪法原则（Constitutional DNA）：**

- **二重性存在** — 不是先A后B再综合，而是同时同持A与B
- **压缩涌现** — 不是解决矛盾，而是通过四模式折叠从张力中压缩出洞察
- **概念对话** — 不是引用理论装饰，而是以理论作为对话者推进分析
- **结构性情感** — 不是修辞点缀，是结构分析的内在维度
- **拒绝收束** — 不以虚假结论消解张力

### 9R-2.0 核心流程

```
用户输入
    ↓
N9R20AdaptiveRouter — 检测学术标记，分配 fold 深度
    ↓
N9R20DualState — 初始化查询 + 目标压缩参数
    ↓
N9R20TensionBus — 发射 QueryEvent，通知各子系统
    ↓
N9R20DualReasoner — 生成 A/B 双视角 + 张力点
    ↓
N9R20LLMFoldEvaluator — LLM 评估查询复杂度（一次调用）
    ↓
N9R20CompressionCore — 四模式压缩（规则引擎，零 LLM token）
    ↓
  ├─ Construct: 构建 A 视角论证
  ├─ Deconstruct: 构建 B 视角反驳
  ├─ Validate: 宪法原则检查
  └─ Interrupt: 检测廉价综合，强制重折叠
    ↓
N9R20LLMCompressor — 语义精修（复用框架 LLM）
    ↓
输出结构化洞察
    ↓
N9R20MemoryLearner — 保存会话到 SQLite
    ↓
N9R20SemanticGraph — 更新语义节点关系
```

### 宪法检查规则

```python
CONSTITUTIONAL_RULES = [
    "无'我'",
    "无'你应当'",
    "无鸡汤",
    "无 AI 套话",
    "不问句结尾",
    "优先使用'不是 X，而是 Y'句式",
    "矛盾点悬停不下结论",
    "理论引用大于概括性陈述",
]
```

---

## 📊 运行数据 · Runtime Stats

截至 2026-05-06，在 DeepSeek V4 Pro 上累计处理 **~6.0 亿 tokens**。输入 Prompt Caching 命中率稳定在 **~95%**。

| 指标 | 数值 |
|:---|:---:|
| 累计处理 tokens | ~600,000,000 |
| 输入（命中缓存） | ~490,000,000 |
| 输入（未命中缓存） | ~23,000,000 |
| 输出 | ~5,000,000 |
| **输入缓存命中率** | **~95%** |

---

## 📚 文档索引

| 文档 | 内容 |
|------|------|
| `docs/MIGRATION_GUIDE.md` | 9R-1.5 → 9R-2.0 迁移指南 |
| `docs/DIRECTORY_HIERARCHY_GUIDE.md` | 目录层级说明（core/ skillbook/ archive/） |
| `docs/FRAMEWORK.md` | 架构设计文档（从悬置到压缩涌现） |
| `docs/DEPLOY.md` | 部署说明（AstrBot / OpenClaw / Standalone） |
| `docs/SKILLBOOK.md` | 技能书规范 v1.2（原版） |
| `docs/SKILLBOOK_v2.md` | 技能书规范 v2.0（压缩涌现版） |

---

## 🤝 贡献

见 `docs/README.md` 贡献指南。

---

*KL9-RHIZOME · 不是又一个 AI 框架，而是一个认知协议。*
