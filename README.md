# KL9-RHIZOME

> **在 LLM 之上运行的认知协议层** · *A cognitive protocol layer on top of LLMs*

让AI从对话开始就持有两种不可调和的角度，不缝合、不综合、不走第三条路。

*Enables AI to hold two irreconcilable perspectives from the very start — no synthesis, no third way.*

---

## 📖 缘起 · Origin（你来写）

> *// TODO: 留给你写自己的故事*

---

## 🔍 一句话 · TL;DR

**KL9-RHIZOME 不是 AI 框架，而是认知协议。** 它定义 AI 如何持有双重视角、管理张力、拒绝廉价和解。

*Not another AI framework — a protocol for how AI holds dual perspectives, manages tension, and refuses cheap synthesis.*

---

## 🎯 对比 · Comparison

| | 传统 AI 输出 · *Traditional AI* | KL9-RHIZOME 输出 |
|:---|:---|:---|
| 用户问 | "X 和 Y 哪个更合理？" | 同一问题 |
| AI 答 | "两者各有道理，需根据具体情况平衡" ❌ 缝合 | A 的前提被 B 直接否定——不在同一个层面上说话 |
| 读者感受 | 平衡、安全、无启发 | **撕裂感、开始思考** |

**核心信条：** 任何值得深入回答的问题，都内嵌一个不可调和的张力。AI 的工作不是消解它，而是充分表达它。

*Core conviction: Every question worth answering deeply contains an irreconcilable tension. The AI's job is not to dissolve it — but to let it speak fully.*

---

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
| **Claude** (Anthropic) | 核心架构设计、代码实现、文档编写 |
| **DeepSeek** | 提供推理支持与视角启发 |
| **Kimi** (Moonshot AI) | 提供创意碰撞与思路验证 |

---

## 📜 许可 · License

MIT © 2026 kaile9
