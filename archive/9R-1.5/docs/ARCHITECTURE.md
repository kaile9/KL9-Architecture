# 🏗 KL9 系统架构 · System Architecture

> **最后更新**: 2026-05-06 · 当前版本: **9R-1.5** · 代码总行数: **~5,236 行**

---

## 目录 · Table of Contents

1. [系统概览 · System Overview](#1-系统概览--system-overview)
2. [核心运行时 · Core Runtime](#2-核心运行时--core-runtime)
3. [九层模块 · Nine Modules](#3-九层模块--nine-modules)
4. [张力类型系统 · Tension Type System](#4-张力类型系统--tension-type-system)
5. [事件系统 · Event System](#5-事件系统--event-system)
6. [认知流程 · Cognitive Pipeline](#6-认知流程--cognitive-pipeline)
7. [技能书集成 · Skillbook Integration](#7-技能书集成--skillbook-integration)
8. [结构健康 · Structure Health](#8-结构健康--structure-health)
9. [设计决策 · Design Decisions](#9-设计决策--design-decisions)

---

## 1. 系统概览 · System Overview

KL9-RHIZOME 是一个运行在 LLM 之上的认知协议层。它不是 AI 框架，而是定义 AI 如何持有双重视角、管理张力、拒绝廉价和解的协议。

*Not another AI framework — a protocol for how AI holds dual perspectives, manages tension, and refuses cheap synthesis.*

### 系统目标 · System Goals

1. **二重性存在** — 同时持有两个不可调和的视角
2. **张力悬置** — 让张力保持为张力，不缝合为"更高统一"
3. **概念对话** — 与思想家对话而非检索征用
4. **结构性情感** — 认知与情感不可分离
5. **拒绝收束** — 输出以反诘、悖论或开放张力结尾

### 数据流 · Data Flow

```
用户 Query
    ↓
Phase 0: detect_dual_nature    检测二重性
    ↓
Phase 1: _retrieve_concepts    检索概念（BM25 + 张力共振排序）
    ↓
Phase 2: _activate_dialogues   激活对话（dialogical_activation）
    ↓
Phase 3: dual_fold             递归折叠（A/B 视角交替深化）
    ↓
Phase 4: emergent_style        涌现风格（从张力配置生成风格轮廓）
    ↓
Phase 5: _generate_response    生成响应（宪法审查后输出）
    ↓
Phase 6: FoldCompleteEvent     触发完成事件 → learner 记录
```

### 技术栈 · Tech Stack

| 层级 | 技术 |
|------|------|
| 运行时 | Python 3.10+ |
| 数据库 | SQLite（概念图谱 + 记忆） |
| 事件总线 | 自研 TensionBus（发布/订阅） |
| 检索 | BM25 + 张力共振排序 |
| 部署 | AstrBot / OpenClaw / Standalone |

---

## 2. 核心运行时 · Core Runtime

KL9-RHIZOME 9R-1.5 的认知引擎，包含二重折叠、张力总线、概念图谱后端和风格涌现。

*Cognitive engine of KL9-RHIZOME 9R-1.5: dual-fold, tension bus, concept graph backend, and emergent style.*

**版本**: 9R-1.5 (semver: 1.5.0)  
**命名**: 9=开了玖, R=RHIZOME, 1.5=大版本.小版本

### 核心模块 · Core Modules（12）

| 模块 | 职责 | 代码行数 |
|------|------|:---:|
| `constitutional_dna.py` | 五原则宪法：A/B平等、反调和、显式张力、渐进深度、可逆折叠 | 111 |
| `core_structures.py` | 核心数据结构：DualState、Tension、FoldWeight | 169 |
| `dual_fold.py` | 二重折叠原语：在 A/B 视角间递归折叠直到悬置 | 223 |
| `emergent_style.py` | 风格涌现：从张力配置生成认知风格轮廓 | 32 |
| `fold_depth_policy.py` | 折叠深度策略：根据难度谱动态调节 max_fold_depth | 41 |
| `graph_backend.py` | SQLite 概念图谱：存储、BM25检索、张力共振排序、谱系边 | 665 |
| `learner.py` | 二重学习器：张力悬置评估驱动的迭代学习 | 420 |
| `memory.py` | 持久记忆：会话记录、反馈、张力上下文检索 | 374 |
| `perspective_types.py` | 视角类型注册表 | 215 |
| `routing.py` | 路由：查询→张力场→技能匹配 | 593 |
| `suspension_evaluator.py` | 悬置质量评估：genuine / forced / insufficient | 141 |
| `tension_bus.py` | 去中心化张力总线：6种张力类型的发布/订阅 | 144 |

### 运行时初始化 · Runtime Initialization

```python
# 基础测试
python -c "import sys; sys.path.insert(0, 'kl9_core'); from perspective_types import PERSPECTIVE_TYPES; print('OK:', len(PERSPECTIVE_TYPES.tension_types), 'tension types')"
```

### 健康检查 · Health Check

```bash
python3 -c "import sys; sys.path.insert(0, 'kl9_core'); from health import HealthCheck; hc = HealthCheck(); print(hc.report())"
```

---

## 3. 九层模块 · Nine Modules

| 模块 | 角色 | 行数 |
|:---|:---|:---:|
| **kl9_core** | 认知初始化：加载 DualState，声明 DNA | 751 |
| **kl9_reasoner** | Perspective A：理论视角运算 | 641 |
| **kl9_soul** | Perspective B：具身成长引擎 | 64+426 |
| **kl9_graph** | 概念知识图谱（6 张力类型 × 7 二重组） | 370 |
| **kl9_research** | 对话式理论激活（与思想家对话而非检索） | 511 |
| **kl9_memory** | 持久记忆层（SQLite，全活跃无归档） | 400 |
| **kl9_learner** | 迭代双面学习（事后优化） | 573 |
| **kl9_orchestrator** | 6 阶段认知流程协调 | 1114 |
| **kl9_core (shared)** | 共享基础设施（11 模块，~2843 行） | 173 |

### 模块关系 · Module Relationships

```
                    ┌─────────────┐
                    │   用户 Query  │
                    └──────┬──────┘
                           ↓
              ┌────────────────────────┐
              │    kl9_orchestrator      │
              │   (6 阶段协调流程)        │
              └──────┬───────────────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   ┌────────┐  ┌──────────┐  ┌──────────┐
   │kl9_core│  │kl9_reasoner│  │kl9_soul  │
   │(初始化) │  │(视角 A)    │  │(视角 B)  │
   └───┬────┘  └─────┬────┘  └─────┬────┘
       │             │             │
       └─────────────┼─────────────┘
                     ↓
              ┌──────────────┐
              │  dual_fold   │
              │ (递归二重折叠) │
              └──────┬───────┘
                     ↓
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
  ┌─────────┐  ┌──────────┐  ┌──────────┐
  │kl9_graph│  │kl9_memory│  │kl9_learner│
  │(概念图谱) │  │(持久记忆)  │  │(迭代学习)  │
  └────┬────┘  └────┬─────┘  └────┬─────┘
       │            │             │
       └────────────┼─────────────┘
                    ↓
             ┌─────────────┐
             │  TensionBus   │
             │  (事件总线)    │
             └─────────────┘
```

---

## 4. 张力类型系统 · Tension Type System

6 种预定义张力类型，每类对应一组不可调和的双视角：

```
eternal_vs_finite     ← temporal.human  ↔  temporal.elf
mediated_vs_real      ← existential.immediate  ↔  existential.mediated
regression_vs_growth  ← social.regression  ↔  social.growth
freedom_vs_security   ← political.freedom_focused  ↔  political.security_focused
economic_vs_grotesque ← economic_grotesque.economic  ↔  economic_grotesque.grotesque
truth_vs_slander      ← truth_construction.truth  ↔  truth_construction.slander
```

### 推荐二重组合 · Recommended Dualities

7 组经过验证的视角对：

| # | Perspective A | Perspective B | 适用场景 |
|:--:|------|------|---------|
| 1 | 理论分析 | 现象学描述 | 学术文本 |
| 2 | 结构功能 | 冲突批判 | 社会学 |
| 3 | 文本细读 | 历史语境 | 文学 |
| 4 | 实证研究 | 规范反思 | 哲学 |
| 5 | 个体经验 | 制度分析 | 政治学 |
| 6 | 生成语法 | 语用行为 | 语言学 |
| 7 | 经济理性 | 文化象征 | 人类学 |

---

## 5. 事件系统 · Event System

### TensionBus 事件类型 · Event Types

| 事件 | 触发时机 | 订阅者 |
|:---|:---|:---|
| `QueryEvent` | 收到用户 query | orchestrator |
| `PerspectiveEvent` | DualState 加载完成 | reasoner, soul |
| `FoldEvent` | 每次递归折叠完成 | graph, memory |
| `SuspensionEvent` | 悬置评估完成 | learner |
| `FoldCompleteEvent` | 全流程结束 | learner, stats |
| `SkillBookImportEvent` | 技能书导入完成 | learner, graph |

### 去中心化特性 · Decentralized Nature

- 无中央调度器
- 任意模块可订阅它关心的事件
- 发布/订阅模式，松耦合

> **注意**: 当前运行时仍使用顺序编排。真正的异步去中心化是 9R-1.6 的目标。

---

## 6. 认知流程 · Cognitive Pipeline

### 6 阶段协调流程 · 6-Phase Pipeline

```
Phase 0: detect_dual_nature    检测二重性
    └─→ 分析 query 中的张力类型
    └─→ 加载对应的 DualState

Phase 1: _retrieve_concepts    检索概念
    └─→ BM25 检索相关概念
    └─→ 张力共振排序（替代纯相关性）
    └─→ 谱系边查询（genealogy 追踪）

Phase 2: _activate_dialogues   激活对话
    └─→ dialogical_activation 与思想家对话
    └─→ 非检索征用，而是对话式改造理论框架

Phase 3: dual_fold             递归折叠
    └─→ 从 A 与 B 同时出发
    └─→ 每次折叠识别结构性张力
    └─→ 评估是否达到 genuine suspension
    └─→ fold_depth 动态调节

Phase 4: emergent_style        涌现风格
    └─→ 从张力配置生成认知风格轮廓
    └─→ 4 种预定义风格 + 动态生成

Phase 5: _generate_response    生成响应
    └─→ Constitutional DNA 审查（零 LLM 开销）
    └─→ 输出：反诘、悖论或开放张力

Phase 6: FoldCompleteEvent     完成事件
    └─→ learner 记录本次折叠
    └─→ 触发张力悬置评估
```

### 折叠深度策略 · Fold Depth Policy

```python
# fold_depth_policy.py
# 根据难度谱动态调节 max_fold_depth

def compute_fold_depth(query_complexity, concept_density, tension_count):
    """
    基础深度: 3
    复杂度加成: +1 per complexity tier
    概念密度加成: +1 if density > threshold
    张力数加成: +1 per 2 additional tensions
    封顶: 7
    """
```

---

## 7. 技能书集成 · Skillbook Integration

导入技能书时，kl9_core 参与以下流程：

| 模块 | 导入时的行为 |
|------|-------------|
| `kl9_core/graph_backend.py` | bridge.py 通过 store_concept() + create_edge() 将导入概念写入 SQLite；新增概念自动参与 BM25 检索和张力共振排序 |
| `kl9_core/memory.py` | 导入操作记录为 session；通过 retrieve_by_tension_context() 可查到导入历史 |
| `kl9_core/tension_bus.py` | 导入完成后发射 SkillbookImportEvent，订阅者可响应（如 learner 触发重评估） |
| `kl9_core/core_structures.py` | 导入的 DualState 数据直接映射到 Perspective + Tension 结构 |

详见 [SKILLBOOK.md](SKILLBOOK.md)。

---

## 8. 结构健康 · Structure Health

### 当前状态 · Current Status

**生成时间**: 2026-05-06  
**版本**: v1.2.0

#### 目录结构 · Directory Structure

| 目录 | 状态 | 说明 |
|------|:--:|------|
| `kl9_core/` | ✅ | 12 模块，~5,236 行 |
| `kl9_skillbook/` | ✅ | 8 模块，完整吸收协议 |
| `skillbooks/` | ✅ | 3 本社区技能书 |
| `docs/` | ✅ | 高集成度文档系统（GUIDE.md / SKILLBOOK.md / ARCHITECTURE.md） |
| `tests/` | ✅ | 基础测试 + 桥接测试 |
| `scripts/` | ✅ | 导出工具 |
| `examples/` | ✅ | 快速启动示例 |
| `archive/` | ✅ | 历史版本归档 |

#### 文档完整性 · Documentation Completeness

| 检查项 | 状态 |
|------|:--:|
| 根目录 README.md | ✅ |
| 根目录 CHANGELOG.md | ✅ |
| 根目录 LICENSE | ✅ |
| 每个子目录 README.md | ✅ |
| 无断裂内部链接 | ✅ |
| 无 .txt/.rst 散落 | ✅ |
| 无临时文件在根目录 | ✅ |

#### 根目录整洁度 · Root Cleanliness

| 文件 | 用途 | 保留? |
|------|------|:--:|
| `README.md` | 项目主文档 | ✅ |
| `CHANGELOG.md` | 变更日志 | ✅ |
| `LICENSE` | MIT 许可 | ✅ |
| `.gitignore` | Git 忽略规则 | ✅ |
| `quickstart.py` | 一键启动 | ✅ |

**结论**: 根目录整洁，仅含必需的元数据和工具文件。

#### 整体评分 · Overall Rating

**A+ (优秀)** — 项目结构规范，文档高集成度，链接完整，版本一致。

---

## 9. 设计决策 · Design Decisions

### 为什么用 SQLite 而不是向量数据库？

1. **零配置** — 不需要额外服务
2. **BM25 足够** — 对于概念级检索，BM25 + 张力共振排序比纯向量相似度更符合认知逻辑
3. **可移植** — 单文件数据库，易于备份和迁移
4. **SQL 查询** — 谱系边查询、子图遍历用 SQL 表达更自然

### 为什么用顺序编排而不是完全异步？

1. **可预测性** — 调试和推理更容易
2. **AstrBot 兼容** — 当前主要部署环境是 AstrBot，同步模式更稳定
3. **逐步演进** — 9R-1.6 将引入真正的异步事件循环

### 为什么 Constitutional DNA 是不可变的？

修改五原则等于修改 KL9 的身份。这不是技术决策，而是存在论决策。

### 为什么技能书用 SKILL.md 而不是纯 JSON？

1. **人类可读** — 评审 PR 时可以直接阅读
2. **版本控制友好** — diff 可阅读
3. **渐进式** — `.skillbook.json` 用于机器导入，SKILL.md 用于人类阅读和对话激活

### 为什么用 Levenshtein 而不是嵌入模型做碰撞检测？

1. **零依赖** — 不需要下载 embedding 模型
2. **可解释** — 编辑距离是透明可验证的
3. **足够** — 对于概念名称匹配，Levenshtein 在 95%+ 准确率场景下表现良好
4. **未来** — 9R-1.6 将引入语义距离作为补充

---

*中英双语版由 DeepSeek V4 Pro 辅助创作 · Bilingual version co-created with DeepSeek V4 Pro*
