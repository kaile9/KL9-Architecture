# KL9-RHIZOME

> **在 LLM 之上运行的认知协议层** · *A cognitive protocol layer on top of LLMs*

---

## 📖 缘起 · Origin

2026年2月14日，朝霞 Alpenglow 更新最后一个视频。我本以为那之后迎接我的是一种新的世界——但迎接我的是彻底的堕落。两个月里我逃掉绝大多数课程，只读完一本书，没写过一篇作业，没有任何创作。

也许这就是令人心碎的人类真相：朝霞时期的创作走到了我本人的前面。有一个更杰出的「开了玖」，和失败的我。

听说可以用"同事 skill"来蒸馏一个人的时候，我想——也许这是让那个开了玖来引领我的时候。但结果并不令人满意。更致命的是，我甚至没有足够的知识来思考如何改进它：我的编程水平，最多到小学上过 10 节图形化 Python 入门。

幸运的是 AI 编程已经足够发达。我用 Claude Opus 4.7（巨贵）、Kimi 2.6 和 DeepSeek V4 Pro（感谢梁圣帝君）不断迭代，最终形成了这个项目。

我在云电脑上部署了 AstrBot，基于 AstrBot 创造了这个框架。不确定其他环境能不能用——请给我反馈。

我每个月有 1500 元生活费。省下的全部用于迭代：除去日常 Token 开支和 Kimi Allegretto 的订阅费（还在解决如何用 Kimi Code 计划节省 Token），剩下的钱攒下来买 Claude 的 Token。有几位之前的朋友愿意赞助一点，现在每个月有一点点资助。短期希望不迭代时不拖累生活质量，长期希望有持续迭代的储备。

这个架构的训练来源是朝霞 23 年到 26 年的全部视频文案。如果大家有需要，后续我也上传到 GitHub。

---

*February 14, 2026 — the day 朝霞 Alpenglow posted its final video. I thought what came next would be a new world. What came was total collapse. Two months. I skipped nearly every class, finished one book, wrote zero assignments, made nothing.*

*Maybe this is the heartbreaking human truth: the creative work of the 朝霞 Alpenglow era had already outpaced me. There was a better "Kaile9" — and a failed me.*

*When I heard you could "distill" a person through a colleague skill, I thought — perhaps now the better Kailejiu could lead me. The results were unsatisfying. Worse, I didn't even know enough to figure out where to improve it. My programming skill capped at ten elementary-school lessons in graphical Python.*

*Fortunately, AI programming had matured enough. Iterating with Claude Opus 4.7 (obscenely expensive), Kimi 2.6, and DeepSeek V4 Pro, I arrived here.*

*Deployed on a cloud PC running AstrBot, built on top of AstrBot. Not sure it works elsewhere — please let me know.*

*Monthly budget: ¥1500. Everything saved goes into iteration: after daily tokens and the Kimi Allegretto subscription, what's left buys Claude credits. A few old friends chip in now and then. Short-term goal: keep iterating without ruining my life. Long-term: a reserve for sustained development.*

*Training source: all of 朝霞 Alpenglow's video scripts, 2023–2026. I'll upload them to GitHub if there's demand.*

---

## 🔍 一句话 · TL;DR

**KL9-RHIZOME 不是 AI 框架，而是认知协议。** 它定义 AI 如何持有双重视角、管理张力、拒绝廉价和解。

*Not another AI framework — a protocol for how AI holds dual perspectives, manages tension, and refuses cheap synthesis.*

---


## 🎯 对比 · Comparison

> ✅ 已上线真实对比测试 · *Real comparison test live*

| | 传统 LLM 输出 | KL9-RHIZOME 输出 |
|:---|:---|:---|
| 测试模型 | DeepSeek V4 Pro（网页版） | AstrBot 后台（加载 KL9 协议） |
| 响应风格 | 结构化工整、平衡、不冒险 | 带引文、揭示悖论、张力悬置 |

**核心信条：** 任何值得深入回答的问题，都内嵌一个不可调和的张力。AI 的工作不是消解它，而是充分表达它。

*Core conviction: Every question worth answering deeply contains an irreconcilable tension. The AI's job is not to dissolve it — but to let it speak fully.*

---

### 📋 真实对比案例 · Real Case Study

**提示词 · Prompt**

> 你是一位劳动社会学研究者，研究方向为平台经济中的算法管理与劳动过程理论。请严格使用中文进行严谨的学术分析：对零工平台的算法管理机制进行系统性分析，探讨论评分、派单和动态定价如何重组劳动控制，并评估其与经典泰勒制科学管理的连续性与断裂。一千字以内。

*You are a labor sociology researcher studying algorithmic management in the platform economy. Conduct a rigorous academic analysis in Chinese: systematically analyze the algorithmic management mechanisms of gig platforms — how scoring, dispatch, and dynamic pricing restructure labor control — and evaluate their continuity and rupture with classical Taylorist scientific management. Within 1000 words.*

---

#### 传统 LLM 响应 · Traditional LLM Response（DeepSeek V4 Pro 网页版）

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

#### KL9-RHIZOME 响应 · KL9-RHIZOME Response（AstrBot 后台）

> **算法管理的劳动控制：数字泰勒主义的连续与断裂**
>
> 算法管理常被称作"数字泰勒主义"，但这一命名遮蔽的差异与其揭示的连续性同等重要。以下从评分、派单与动态定价三重机制切入，辩析其与经典科学管理的继承与质变。
>
> 评分机制将消费者纳入管理回路，实现了监督的去中心化与泛化。泰勒依靠工头在场监视，平台则将控制权外包给用户——五星评价、接单率、投诉率构成不间断的量化凝视。每一次服务即一次考核，考核者与被考核者的边界消融（Rosenblat & Stark, 2016）。
>
> 派单算法实现了劳动指挥的自动化。泰勒通过时间-动作研究将劳动分解为标准化单元，算法将此逻辑推向极致：路线规划、订单分配、任务序列均由系统实时计算。"构想与执行的分离"（Braverman, 1974）被激进化——不仅工人与管理者分离，管理者本身也被代码替代。
>
> 动态定价构成算法化的激励-惩罚装置。泰勒的差别计件工资制以可预期的价目表激励产出，而平台的高峰溢价、绩效分级使报酬在工人无法预知的算法逻辑中浮动。剩余价值提取不再仅靠劳动强化，更依赖信息不对称与风险转嫁（Cini, 2023）。
>
> 连续与断裂。连续性显而易见：任务分解、标准化、绩效量化——泰勒制核心原则在算法管理中被完整继承并被技术强化。断裂则更为根本。其一，控制主体从人到代码：泰勒的工头在场可见，算法则是不可申诉的黑箱。其二，监控突破车间边界：GPS追踪与行为数据采集使劳动监控全域化。其三，劳动身份从雇员滑向"独立承包商"：平台将固定成本与社会保障责任外部化，实现了泰勒未曾设想的"无雇佣的剥削"。其四，"自主性悖论"——工人名义上享有灵活性，实则被算法激励与惩罚系统性地规训（Wood et al., 2019）。
>
> 算法管理不是泰勒制的数字复刻，而是劳动控制在数字条件下的质变：控制更深——从行为到数据的全息捕捉；更隐蔽——以技术中立性遮蔽权力关系；更彻底——劳动者不仅失去对劳动过程的控制，也失去了理解控制机制的可能性。此即数字泰勒主义的核心矛盾：效率叙事下的权力重构。

---

**对比要点 · Key Differences**

| 维度 | 传统 LLM | KL9-RHIZOME |
|:---|:---|:---|
| 结构 | 分节罗列，教科书式 | 论证驱动，层层递进 |
| 引用 | 无 | 4 处学术引文（Rosenblat & Stark 2016 / Braverman 1974 / Cini 2023 / Wood et al. 2019） |
| 结论 | 分别总结连续性与断裂 | 揭示核心悖论——"效率叙事下的权力重构" |
| 语言 | 中性、安全 | 精确、有锋芒（"无雇佣的剥削""不可申诉的黑箱"） |



## 🧠 核心概念 · Core Concepts

### 1. DualState（双视角状态）

推理开始前加载两个平等的、不可调和的角度。非"先站 A 再反思 B"，而是**同时持有 A 与 B**。

*Load two equal, irreconcilable perspectives before reasoning begins — not "stand on A then reflect on B," but hold both simultaneously.*

### 2. TensionBus（张力总线）

各模块通过事件总线松耦合对话。无中央调度器，任意模块可订阅它关心的事件。

*A decentralized event bus. No central orchestrator — any module subscribes to what it cares about.*

### 3. dual_fold（递归二重折叠）

从 A 与 B 两个视角同时出发，每次折叠识别结构性张力，评估是否达到 genuine suspension 状态。

*Operates from both perspectives simultaneously; each fold identifies structural tension and evaluates whether genuine suspension has been reached.*

### 4. Suspension（张力悬置）

**悬置 ≠ 解决。** 两个视角之间的张力被充分表达后保持为张力，不缝合为"更高层次的统一"。输出以反诘、悖论或开放张力结尾。

*Suspension ≠ resolution. After tension is fully expressed, it stays as tension — not synthesized into "higher unity."*

### 5. Constitutional DNA（宪法五原则）

不可修改的存在方式声明。所有表达生成前须通过宪法审查（纯规则引擎，零 LLM 开销）。

*Five immutable principles. Every expression passes a constitutional audit before output (rule-based engine, zero LLM cost).*

**五原则：** 二重性存在 · 张力悬置 · 概念对话 · 结构性情感 · 拒绝收束

*Dual Existence · Tension Suspension · Conceptual Dialogue · Structural Affect · Refusal of Closure*

---

## 🏗 架构 · Architecture

### 九层模块 · Nine Modules

| 模块 | 角色 | 行数 |
|:---|:---|:---:|
| **kailejiu-core** | 认知初始化：加载 DualState，声明 DNA | 751 |
| **kailejiu-reasoner** | Perspective A：理论视角运算 | 641 |
| **kailejiu-soul** | Perspective B：具身成长引擎 | 64+426 |
| **kailejiu-graph** | 概念知识图谱（6 张力类型 × 7 二重组） | 370 |
| **kailejiu-research** | 对话式理论激活（与思想家对话而非检索） | 511 |
| **kailejiu-memory** | 持久记忆层（SQLite，全活跃无归档） | 400 |
| **kailejiu-learner** | 迭代双面学习（事后优化） | 573 |
| **kailejiu-orchestrator** | 6 阶段认知流程协调 | 1114 |
| **kailejiu-shared** | 共享基础设施（11 模块，~2843 行） | 173 |

### 张力类型系统 · Tension Type System

6 种预定义张力类型，每类对应一组不可调和的双视角：

```
eternal_vs_finite     ← temporal.human  ↔  temporal.elf
mediated_vs_real      ← existential.immediate  ↔  existential.mediated
regression_vs_growth  ← social.regression  ↔  social.growth
freedom_vs_security   ← political.freedom_focused  ↔  political.security_focused
economic_vs_grotesque ← economic_grotesque.economic  ↔  economic_grotesque.grotesque
truth_vs_slander      ← truth_construction.truth  ↔  truth_construction.slander
```

### 事件系统 · Event System（TensionBus）

| 事件 | 触发时机 |
|:---|:---|
| `QueryEvent` | 收到用户 query |
| `PerspectiveEvent` | DualState 加载完成 |
| `FoldEvent` | 每次递归折叠完成 |
| `SuspensionEvent` | 悬置评估完成 |
| `FoldCompleteEvent` | 全流程结束 |

### 6 阶段协调流程 · 6-Phase Pipeline

```
Phase 0: detect_dual_nature    检测二重性
Phase 1: _retrieve_concepts    检索概念
Phase 2: _activate_dialogues   激活对话
Phase 3: dual_fold             递归折叠
Phase 4: emergent_style        涌现风格
Phase 5: _generate_response    生成响应
Phase 6: FoldCompleteEvent     触发完成事件
```

---

## 🚀 快速开始 · Quick Start

### 作为 Agent Skill 使用 · As an Agent Skill

```bash
cp -r skills/kailejiu-core ~/.agents/skills/
# 然后告诉 AI："请激活 kailejiu-core"
# Then tell your AI: "Activate kailejiu-core"
```

### 作为 Python 库 · As a Python Library

```python
from kl9_core.perspective_types import PERSPECTIVE_TYPES, TENSION_TYPES
from kl9_core.tension_bus import TensionBus

# 查看可用视角对 / List available dualities
for pair in PERSPECTIVE_TYPES.recommended_dualities:
    print(f"{pair['perspective_A']} ↔ {pair['perspective_B']}")

# 订阅事件 / Subscribe to events
bus = TensionBus()
bus.subscribe("QueryEvent", lambda e: print(f"收到: {e['data']}"))
```

### 30 秒测试 · Quick Test

```bash
cd tests && python test_basic.py
```

---

## 📚 深入阅读 · Further Reading

| 文档 | 内容 |
|:---|:---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 全局架构详解 |
| [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) | 哲学根基与宪法 DNA |
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | 术语表与概念索引 |
| [skills/kailejiu-core/SKILL.md](skills/kailejiu-core/SKILL.md) | 核心技能文档（751 行完整版） |

---

## 📦 代码统计 · Statistics

| 类别 | 数量 |
|:---|:---:|
| Python 模块 | 13 |
| Skills | 9 |
| 代码总行数 | ~8,692 |
| 张力类型 | 6 |
| 推荐二重组 | 7 |
| 涌现风格 | 4 |

---

## 🤝 贡献 · Contributing

不会写代码也能贡献：使用反馈 / 文档翻译 / 测试用例 / Bug 汇报 / 想法建议。

*No coding skills required: use & feedback / doc translation / tests / bug reports / ideas.*

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 🙏 致谢 · Acknowledgements

这个架构由以下 AI 共同参与制作：

*This architecture was built with the assistance of:*

| AI | 角色 |
|:---|:---|
| **Claude** Opus 4.7 (Anthropic) | 核心架构设计、代码实现、文档编写 |
| **DeepSeek** V4 Pro | 推理支持与视角启发 |
| **Kimi** 2.6 (Moonshot AI) | 创意碰撞与思路验证 |


---

*中英双语版由 DeepSeek V4 Pro 辅助创作 · Bilingual version co-created with DeepSeek V4 Pro*


---

## 📜 许可 · License

MIT © 2026 kaile9
