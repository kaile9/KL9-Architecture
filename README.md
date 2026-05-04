<p align="center">
  <img src="assets/logo.png" alt="KL9-RHIZOME" width="200"/>
</p>

<h1 align="center">KL9-RHIZOME</h1>
<h3 align="center">让AI从对话开始就持有不可调和的两种视角</h3>
<h4 align="center">A dual-dialectical cognitive architecture that holds two irreconcilable perspectives from the very start — no synthesis, no third way.</h4>

<p align="center">
  <i>中文 · <a href="README.en.md">English</a></i>
</p>

---

## 🧬 缘起 · Why I Built This

> **一个考研人的深夜随笔，最终长成了这套认知架构。**

2025年秋天，我在备考社会学研究生。每天的生活很简单：早上数学，下午英语，晚上专业课。但在那些深夜——复习完福柯的"规训"、德勒兹的"块茎"、鲍德里亚的"拟像"之后——我发现自己无法入睡。

不是因为焦虑，而是因为这些思想家在我的脑子里打仗。

福柯说权力无处不在，德勒兹说差异才是本真，鲍德里亚说真实已经死了……它们谁都没错，但谁也说服不了谁。而我每天使用的AI，却总是给出 "both sides have their merits, a balanced approach is recommended" 这种四平八稳的答案。

**这不是思考，这是和稀泥。**

所以我开始了一个"不务正业"的项目：能不能让AI不只是"换位思考"（先站一边再假裝站另一边），而是从一开始就同时持有两种不可调和的视角，并且**不缝合它们**？

KL9-RHIZOME 就是从这个问题长出来的。它不是什么正规的学术项目，只是一个考研人深夜的胡思乱想，被代码和文档认真对待了。

> *A late-night thoughts project from a graduate-school exam candidate, turned into actual code.*

---

## 🔍 一句话 · TL;DR

**KL9-RHIZOME 是在 LLM 之上运行的认知操作系统。** 它不是又一个 AI 框架，而是一套协议——规定 AI 应该如何持有双重视角、如何管理张力、如何拒绝廉价的和解。

它不是教 AI 做什么，而是教 AI **如何存在**。

> *KL9-RHIZOME is a cognitive operating system that runs on top of LLMs. It's not another AI framework — it's a protocol for how AI should hold dual perspectives, manage tension, and refuse cheap synthesis.*

---

## 🎯 不用 KL9 vs 用 KL9 —— 一个对比

| | 传统 AI | 用了 KL9-RHIZOME |
|---|---|---|
| **用户问** | "自由主义和社群主义哪个更合理？" | 同一问题 |
| **AI 答** | "两者各有道理……在实践中可以互补……建议根据具体情况权衡" | ❌ **缝合** |
| **KL9 答** | — | "自由主义的前提（个人先于社会）被社群主义的前提（社会先于个人）直接否定。这两种前提没有调和的空间——不是谁对谁错，而是它们不在同一个层面上说话。" |
| **读者感受** | 平衡、安全、但毫无启发 | **撕裂感、不安、但开始思考** |

**核心信条：** 任何值得深入回答的问题，都内嵌一个不可调和的张力。AI 的工作不是消解这个张力，而是**充分表达它**。

> *Core conviction: Every question worth answering deeply contains an irreconcilable tension. The AI's job is not to dissolve it — but to let it speak fully.*

---

## 🚀 快速开始 · Quick Start

### 作为 AstrBot / Claude Code Skill 使用（推荐）

```bash
# 只需三步：
# 1. 把 kailejiu-core 放到你的 skills 目录
cp -r skills/kailejiu-core ~/.agents/skills/

# 2. 告诉你的 AI："请激活 kailejiu-core skill"
# 3. 问一个复杂的问题
```

### 作为 Python 库使用

```python
from kl9_core import dialogical_activation

# 加载两个不可调和的视角
state = dialogical_activation("人工智能有意识吗？")
# → DualState loaded: 科学视角 vs 现象学视角
# → 两个视角已就位，随时开始双面思考
```

### 最短可行的例子（30 秒）

```python
# demo_minimal.py
from kl9_core.perspective_types import PERSPECTIVE_TYPES

# 看看有哪些视角对可用
for pair in PERSPECTIVE_TYPES.recommended_dualities:
    print(f"  {pair['perspective_A']}  ↔  {pair['perspective_B']}")
    print(f"  张力类型: {pair['tension']}")
    print()
# 输出：
#   temporal.human  ↔  temporal.elf
#   张力类型: eternal_vs_finite
#   existential.immediate  ↔  existential.mediated
#   张力类型: mediated_vs_real
#   ...
```

---

## 🧠 核心概念（只有3个）

### 1. DualState — 双视角状态

在推理发生之前，先加载两个平等的、不可调和的视角。不是"先站A再反思B"，而是从第一时刻就同时持有A和B。

> *Before reasoning begins, load two equal, irreconcilable perspectives. Not "stand on A then reflect on B" — hold A and B simultaneously from the start.*

### 2. TensionBus — 张力总线

各模块通过事件总线松耦合对话。不需要中央调度器——任何模块都可以订阅它关心的事件。

> *Modules talk through an event bus. No central orchestrator needed — any module subscribes to what it cares about.*

### 3. Suspension — 张力悬置

**悬挂 ≠ 解决。** 两个视角的张力被充分表达后，保持为张力，不缝合为"更高层次的统一"。读者应该感到撕裂感，而非平衡感。

> *Suspension ≠ resolution. After the tension between two perspectives is fully expressed, it stays as tension — not synthesized into "higher unity." The reader should feel torn, not balanced.*

| 概念 | 中文 | English |
|:---|:---|:---|
| DualState | 双视角状态 | Dual perspective state |
| TensionBus | 张力总线 | Tension event bus |
| Suspension | 张力悬置 | Tension suspension |

---

## 📦 模块一览 · Modules

| 模块 | 职责 | Lines |
|:---|:---|:---:|
| **kailejiu-core** | 认知初始化 —— 加载 DualState，声明宪法 DNA | 751 |
| **kailejiu-reasoner** | Perspective A —— 理论视角的认知运算 | 641 |
| **kailejiu-soul** | Perspective B —— 具身成长引擎 | 64+426 |
| **kailejiu-graph** | 概念知识图谱 —— 6 种张力类型 + 7 组推荐二重组合 | 370 |
| **kailejiu-research** | 对话式理论激活 —— 与思想家对话而非检索定义 | 511 |
| **kailejiu-memory** | 持久记忆层 —— 所有记忆保持活跃，无归档门控 | 400 |
| **kailejiu-learner** | 迭代学习层 —— 概念 Perspective 映射的丰富化 | 573 |
| **kailejiu-orchestrator** | 协调器 —— 6 阶段认知流程 | 1114 |
| **kailejiu-shared** | 共享基础设施 —— 11 个 Python 模块，2843 行 | 173 |

---

## 🏗 整体架构 · Architecture

```
                    ┌─────────────────────────────┐
                    │        TensionBus            │
                    │    (事件总线 · Event Bus)      │
                    └──────┬──────┬──────┬────────┘
                           │      │      │
              ┌────────────┘      │      └────────────┐
              ▼                   ▼                   ▼
      ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
      │  kailejiu-   │   │  kailejiu-   │   │  kailejiu-   │
      │   reasoner   │   │    soul      │   │    graph     │
      │ (Perspective │   │ (Perspective │   │  (知识图谱)   │
      │    A · 理论)  │   │   B · 具身)   │   │              │
      └──────────────┘   └──────────────┘   └──────────────┘
              │                                      │
              └──────────────┬──────────────┬────────┘
                             ▼              ▼
                     ┌────────────┐  ┌────────────┐
                     │ kailejiu-  │  │ kailejiu-  │
                     │  memory    │  │  learner   │
                     │ (记忆层)    │  │ (学习层)    │
                     └────────────┘  └────────────┘
```

**设计原则：**
- **去中心化**：没有中央大脑，7 个技能通过 TensionBus 直接对话
- **任意入口**：任何一个技能都可以作为入口被激活
- **剪断任意节点不影响整体**：去掉某个技能，其他技能照常工作
- **不可调和的两个视角** 从认知起点就同时存在

---

## 📚 深入阅读 · Further Reading

| 文档 | 说明 |
|:---|:---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 全局架构详解 —— 7 技能 + 6 阶段流程 |
| [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) | 哲学根基 —— Constitutional DNA 五原则 |
| [docs/CONCEPTS.md](docs/CONCEPTS.md) | 概念详解 + 术语表 |
| [docs/CONSTITUTIONAL_DNA.md](docs/CONSTITUTIONAL_DNA.md) | 宪法 DNA —— 不可修改的存在方式声明 |
| [examples/astrbot.md](examples/astrbot.md) | 在 AstrBot 中部署 |
| [examples/claude-code.md](examples/claude-code.md) | 在 Claude Code 中部署 |
| [examples/minimal.md](examples/minimal.md) | 最短可用示例 |

---

## 🤝 如何贡献 · Contributing

**你不必会写代码来贡献。**

| 你能做什么 | 怎么做 |
|:---|:---|
| 💬 **使用并反馈** | 用 KL9 问一个问题，告诉我你的感受 |
| 📝 **写文档** | 帮我翻译、简化、补充 |
| 🧪 **写测试** | 帮我写 `assert` 来保证代码质量 |
| 🐛 **报 bug** | 告诉我哪里崩了 |
| 💡 **提 Idea** | 你觉得 DualState 还能怎么改进？ |
| 🌐 **翻译** | 帮我翻译成其他语言 |

详细指南见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📜 许可 · License

MIT

---

<p align="center">
  <i>始于一个考研人的深夜 · Started from a late-night exam prep session</i><br>
  <i>你不是在寻找答案——你是在学习如何更好地持有问题。</i><br>
  <i>You are not looking for answers — you are learning to hold questions better.</i>
</p>
