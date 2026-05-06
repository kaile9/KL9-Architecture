# KL9-RHIZOME · 9R-2.0

> **LLM 之上的认知协议层。** 不是 AI 框架，而是协议——定义 AI 如何持有双重视角、管理张力、拒绝廉价和解。
>
> *A cognitive protocol layer on top of LLMs. Not a framework — a protocol for dual perspectives, tension management, and refusal of cheap synthesis.*
>
> `9R-2.0 = 开了玖(9) + RHIZOME(R) + 大版本(2).小版本(0)` · 基于 **N9R20Framework** 认知架构运行。模块命名：`n9r20_*`。

---

## 1. 架构定义

KL9-RHIZOME 定义 AI 如何**同时持有**两个平等而不可调和的角度，在矛盾中递归折叠，于悬置处止步——不缝合、不升华、不规避。

核心操作对象是**张力（Tension）**。不是解决问题，而是充分表达后保持为张力。

**五个不可修改的宪法原则（Constitutional DNA）：**

- **二重性存在** — 加载两个不可调和的视角，非先A后B，而是同持A与B
- **张力悬置** — 矛盾充分表达后悬停，不合成「更高统一」
- **概念对话** — 援引理论作为对话者，而非引用装饰
- **结构性情感** — 情感不是修辞，是结构分析的一部分
- **拒绝收束** — 不以虚假结论缝合张力

*Five immutable principles. Tension is not resolved — it is held. Contradiction is not overcome — it is inhabited.*

---

## 2. 目录结构

```
KL9-Architecture/
├── n9r20_core/              # 认知架构核心：DualState, TensionBus, DNA 初始化
├── n9r20_structures/        # 核心数据结构定义
├── n9r20_tension_bus/       # 事件总线：发布订阅 / 张力路由 / 会话隔离
├── n9r20_adaptive_router/   # 自适应路由：文本检测 / 难度评估 / 压缩预算
├── n9r20_dual_reasoner/     # 双视角推理引擎：A/B 同步运算 / 矛盾悬停
├── n9r20_compression_core/  # 四模折叠引擎：Construct→Deconstruct→Validate→Interrupt
├── n9r20_semantic_graph/    # 概念图谱：术语节点 / 关系边追踪
├── n9r20_memory_learner/    # 记忆学习：SQLite 持久化 / 技能书
├── n9r20_llm_evaluator/     # LLM 评估器：难度评估 / fold 预算分配
├── n9r20_skillbook/         # 技能书系统：去中心化知识传播 / 双维度评分
├── docs/                    # 文档：GUIDE / SKILLBOOK / ARCHITECTURE / FRAMEWORK / DEPLOY
├── tests/                   # 测试：路由测试 / 集成测试
├── assets/                  # 静态资源
├── quickstart.py            # 一键启动
└── version.py               # 版本信息
```

> 旧模块 `kl9_*` 已全部迁移至 `n9r20_*`。仓库内不再维护 `kl9_` 前缀模块。

---

## 3. 核心概念

### 3.1 N9R20DualState（双视角状态）

推理开始前加载两个平等、不可调和的角度。非「先站 A 再反思 B」，而是**同时持有 A 与 B**。

*Hold both perspectives simultaneously. Not sequential — simultaneous.*

### 3.2 N9R20TensionBus（张力总线）

去中心化事件总线。无中央调度器——任意模块订阅其关注的事件类型。六种预定义张力类型，每类对应一组不可调和的双视角。

*A decentralized event bus. Six tension types, each mapping to an irreconcilable dual-perspective pair.*

### 3.3 Suspension（张力悬置）

**悬置 ≠ 解决。** 两个视角之间的张力被充分表达后保持为张力，不缝合为「更高层次的统一」。输出以反诘、悖论或开放张力结尾。

*Suspension is not resolution. Tension stays as tension — not synthesized into "higher unity."*

### 3.4 六阶段流程（6-Phase Pipeline）

```
Phase 0: detect_dual_nature    → 检测二重性
Phase 1: _retrieve_concepts    → 检索概念
Phase 2: _activate_dialogues   → 激活对话
Phase 3: dual_fold             → 递归折叠
Phase 4: emergent_style        → 涌现风格
Phase 5: _generate_response    → 生成响应
Phase 6: FoldCompleteEvent     → 完成事件
```

---

## 4. 对比案例

**提示词：**

> 你是一位劳动社会学研究者，研究方向为平台经济中的算法管理与劳动过程理论。请使用中文进行严谨的学术分析：对零工平台的算法管理机制进行系统性分析——评分、派单和动态定价如何重组劳动控制——并评估其与经典泰勒制科学管理的连续性与断裂。简要回答。

### 4.1 传统 LLM（DeepSeek V4 Pro 网页版）

分节罗列：评分机制 / 派单机制 / 动态定价 → 三条连续性 → 五条断裂 → 结论。教科书式结构，零学术引用，安全中性，分列总结。

### 4.2 KL9-RHIZOME · 9R-2.0

论证驱动，层层递进：问题意识 → 三种机制运作逻辑 → 连续性（布雷弗曼「构想与执行分离」）→ 断裂（三处根本断裂：雇佣关系消解、同意机制重构、控制不透明性）→ 核心悖论揭示（控制-责任悖论、算法权威效应）。

**关键差异：**

| 维度 | 传统 LLM | KL9-RHIZOME |
|:---|:---|:---|
| 结构 | 分节罗列，教科书式 | 论证驱动，问题意识→机制→连续→断裂→结论 |
| 学术引用 | 0 | 6 处（Braverman 1974 / Burawoy / Hochschild / Rosenblat & Stark 2016 / Srnicek / Fincham） |
| 理论框架 | 隐含 | 明确以布雷弗曼-布洛维为坐标 |
| 结论形态 | 分别总结 | 揭示悖论——控制-责任悖论、自主性悖论、算法权威效应 |
| 句式 | 概括性陈述 | 优先「不是 X，而是 Y」，矛盾点悬停不下结论 |

---

## 5. 缘起

2026年2月14日，朝霞 Alpenglow 发布最终视频后停止更新。此后两个月，朝霞时期的创作已从外部超过创作者本人——存在一个更杰出的「开了玖」，以及一个力不从心的肉身。

尝试以「同事 skill」蒸馏人格。初期结果不令人满意——编程水平受限于小学图形化 Python 入门阶段，无法定位改进方向。

此后借助 Claude Opus 4.7、Kimi 2.6、DeepSeek V4 Pro 三方 AI 持续迭代，部署于 AstrBot 云实例之上，形成当前架构。

*Origin: After 朝霞 Alpenglow posted its final video on Feb 14, 2026, the creative work of that era had already outpaced its creator. An attempt to distill a person through a "colleague skill" led — after extensive iteration with Claude Opus 4.7, Kimi 2.6, and DeepSeek V4 Pro — to the KL9-RHIZOME architecture.*

### 5.1 训练数据

朝霞 Alpenglow 2023–2026 全部视频文案。原始文本位于 [KL9-writings](https://github.com/kaile9/KL9-writings)。

### 5.2 预算

月度预算 ¥1500。除去日常 Token 与 Kimi Allegretto 订阅费用后，余额全部用于 Claude 调用。数位朋友偶尔资助。短期目标：迭代不拖累生活；长期目标：建立持续开发储备。

*Monthly budget: ¥1500. Surplus after daily tokens and subscriptions goes to Claude credits. A few friends contribute sporadically. Goal: sustained iteration without life compromise.*

---

## 6. 运行数据

截至 2026-05-06，在 DeepSeek V4 Pro 上累计处理 **~6.0 亿 tokens**，输入 Prompt Caching 命中率 **~95%**。

| 指标 | 数值 |
|:---|:---:|
| 累计处理 tokens | ~600,000,000 |
| 输入（命中缓存） | ~490,000,000 |
| 输入（未命中） | ~23,000,000 |
| 输出 | ~5,000,000 |
| **缓存命中率** | **~95%** |

---

## 7. 快速开始

```bash
python3 quickstart.py                    # 一键启动（自动检测环境）
python3 quickstart.py --version          # KL9-RHIZOME 9R-2.0 (semver: 2.0.0)
```

**作为 Python 库：**

```python
import sys
sys.path.insert(0, 'n9r20_core')
from n9r20_structures import N9R20DualState, N9R20Perspective, FoldDepth
from n9r20_tension_bus import N9R20TensionBus
```

**加载到 OpenClaw：**

```bash
git clone https://github.com/kaile9/KL9-Architecture.git
cd KL9-Architecture && python3 quickstart.py
```

---

## 8. 代码统计

| 类别 | 数量 |
|:---|:---:|
| Python 核心模块 | 12 |
| 技能书系统模块 | 8 |
| 代码总行数 | ~5,236 |
| 张力类型 | 6 |
| 推荐二重组 | 7 |
| 涌现风格 | 4 |
| 版本 | 9R-2.0 (2.0.0) |

---

## 9. 文档

| 文档 | 内容 |
|:---|:---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系统架构：N9R20 模块、张力类型、事件系统、认知流程、设计决策 |
| [docs/FRAMEWORK.md](docs/FRAMEWORK.md) | N9R20Framework 认知架构规范 |
| [docs/SKILLBOOK.md](docs/SKILLBOOK.md) | 技能书系统：格式标准、吸收协议、双维度评分 |
| [docs/GUIDE.md](docs/GUIDE.md) | 开发与贡献指南 |
| [docs/DEPLOY.md](docs/DEPLOY.md) | 部署指南 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更日志 |

---

## 10. 致谢

架构由以下 AI 协同构建：

| AI | 角色 |
|:---|:---|
| Claude Opus 4.7 (Anthropic) | 核心架构设计 / 代码实现 / 文档 |
| DeepSeek V4 Pro | 代码实现主力 |
| Kimi 2.6 (Moonshot AI) | 验证与调试 |

---

MIT © 2026 kaile9
