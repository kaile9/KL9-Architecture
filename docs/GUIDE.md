# 📚 KL9 开发指南 · Development Guide

> **最后更新**: 2026-05-06 · 当前版本: **9R-1.5**

---

## 目录 · Table of Contents

1. [项目概览 · Project Overview](#1-项目概览--project-overview)
2. [贡献指南 · Contributing](#2-贡献指南--contributing)
3. [AI 代理指南 · AI Agent Guidelines](#3-ai-代理指南--ai-agent-guidelines)
4. [开发路线图 · Development Roadmap](#4-开发路线图--development-roadmap)
5. [版本历史 · Release History](#5-版本历史--release-history)
6. [行为准则 · Code of Conduct](#6-行为准则--code-of-conduct)

---

## 1. 项目概览 · Project Overview

**KL9-RHIZOME** 是一个运行在 LLM 之上的认知协议层，定义 AI 如何持有双重视角、管理张力、拒绝廉价和解。

*A cognitive protocol layer on top of LLMs — defining how AI holds dual perspectives, manages tension, and refuses cheap synthesis.*

### 核心特性 · Key Features

| 特性 | 描述 |
|------|------|
| **DualState** | 双视角状态加载——同时持有 A 与 B，非先后 |
| **TensionBus** | 去中心化事件总线，无中央调度器 |
| **dual_fold** | 递归二重折叠，识别结构性张力 |
| **Constitutional DNA** | 五原则宪法审查（不可修改） |
| **技能书系统** | 去中心化知识传播机制 |

### 项目结构 · Repository Structure

```
KL9-Architecture/
├── kl9_core/          # 核心运行时（12 模块，~5,236 行）
├── skills/     # 技能书吸收协议（8 模块）
├── skills/        # 社区技能书库
├── docs/              # 文档
│   ├── GUIDE.md       # 本文件：开发指南
│   ├── SKILLBOOK.md   # 技能书系统完整规范
│   └── ARCHITECTURE.md # 系统架构详解
├── tests/             # 测试套件
├── scripts/           # 工具脚本
└── examples/          # 示例代码
```

### 快速开始 · Quick Start

```bash
python3 quickstart.py
```

详见 [README.md](../README.md) § 快速开始。

---

## 2. 贡献指南 · Contributing

**你不必会写代码来贡献。** / *You don't need to write code to contribute.*

### 💬 使用并反馈 · Use & Give Feedback

最简单但最有价值的贡献：用 KL9 问一个问题，然后告诉我你的感受。

> *The simplest but most valuable contribution: ask KL9 a question, then tell me how it felt.*

### 📝 写文档 · Write Documentation

- 帮我翻译成其他语言（English / 日本語 / 한국어 / …）
- 帮我简化难懂的部分
- 帮我补充使用场景

### 🧪 写测试 · Write Tests

测试文件在 `tests/` 目录。即使只加一个 `assert` 也有帮助。

> *Test files live in `tests/`. Even one `assert` helps.*

### 🐛 报 Bug · Report Bugs

在 [Issues](https://github.com/kaile9/KL9-Architecture/issues) 页面新建 issue，告诉我：
- 你做了什么
- 期望的结果
- 实际发生了什么

### 💡 提 Idea · Suggest Ideas

DualState 还能怎么改进？TensionBus 应该支持什么新事件类型？你说了算。

### 📚 贡献技能书 · Contribute a Skill Book

读完一本有深度的书后，在你的 KL9 实例上完成至少 1 轮完整学习，导出 → 填写 manifest → 提交到 `skills/` 目录。

详见 [SKILLBOOK.md](SKILLBOOK.md)。

⚠️ **技能书不是 AI 摘要。** 只接受精读原著后产生的学习记录。

### 🌐 翻译 · Translate

把 README 和文档翻译成你的语言。

### 如何提交 · How to Submit

**如果你会用 Git:**
1. Fork 这个仓库
2. 创建一个新分支
3. 提交你的修改
4. 发起 Pull Request

**如果你不会用 Git:**
直接在 [Issues](https://github.com/kaile9/KL9-Architecture/issues) 页面提交，我会处理。

---

## 3. AI 代理指南 · AI Agent Guidelines

### 项目概览 · Project Overview

KL9-RHIZOME is a dual-dialectical cognitive architecture for LLMs. It makes AI hold two irreconcilable perspectives simultaneously.

### 重要规则 · Important Rules

- **Constitutional DNA (5 principles) are IMMUTABLE.** Do not accept PRs that modify them.
- Everything else is open to improvement.
- The architecture is decentralized (TensionBus), but the current runtime still uses sequential orchestration. Moving towards true decentralization is a known TODO.

### 关键文件 · Key Files

| 目录 | 内容 |
|------|------|
| `kl9_core/` | Python 核心库（12 模块） |
| `skills/` | 技能书系统（8 模块） |
| `skills/` | 社区技能书库 |
| `docs/` | 架构和哲学文档 |

### 如何测试 · How to Test

```bash
cd /KL9-Architecture
python -c "import sys; sys.path.insert(0, 'kl9_core'); from perspective_types import PERSPECTIVE_TYPES; print('OK:', len(PERSPECTIVE_TYPES.tension_types), 'tension types')"
```

### 架构概览 · Architecture Overview

详见 [ARCHITECTURE.md](ARCHITECTURE.md)。

### 联系 · Contact

When in doubt, prefer keeping architectural integrity over convenience. This project has a philosophical backbone — don't break it for short-term gain.

---

## 4. 开发路线图 · Development Roadmap

> 当前版本: **9R-1.5** (semver: 1.5.0)

---

### ✅ 9R-1.0 → 9R-1.5 (已完成 · Completed)

#### 核心架构
- [x] DualState 双视角加载引擎
- [x] TensionBus 事件总线（发布/订阅）
- [x] dual_fold 递归二重折叠
- [x] Constitutional DNA 五原则宪法审查
- [x] 6 阶段认知协调流程（Phase 0–5）
- [x] 9 层模块架构（core, reasoner, soul, graph, research, memory, learner, orchestrator, shared）
- [x] 4 种涌现风格

#### 概念图谱
- [x] SQLite 概念图谱后端（BM25 检索 + 子图遍历）
- [x] 6 种张力类型 × 7 组推荐二重组合
- [x] 持久记忆层（sessions, feedback, reading_list）

#### 技能书系统
- [x] SKILLBOOK_STANDARD v1.2（格式规范 + 双维度评分 + 信任模型）
- [x] 技能书吸收协议（SQLite ↔ JSON 桥接、碰撞分叉、影子节点、张力重算）
- [x] 三源聚合评分（HLE + Arena Elo + Creative Writing）
- [x] 语言偏差补偿
- [x] CLI 导出工具（`scripts/export_skillbook.py`）
- [x] 3 本社区技能书（DE: Brodbeck / FR: Foucault / ZH: 大乘起信論）

#### 部署与工具
- [x] AstrBot 集成
- [x] `quickstart.py` 一键启动（自动检测环境）
- [x] 健康检查框架（`kl9_core/health.py`）
- [x] 中英双语 README
- [x] 版本常量系统（`kl9_core/version.py`）

#### 代码质量
- [x] 清理 63 个无关 AstrBot skill 目录
- [x] 删除 9 个重复核心文件
- [x] 修复所有硬编码路径
- [x] 文档重组（本文件所在的高集成度文档系统）

---

### 📋 9R-2.0 路线图 (当前)

#### 测试与 CI
- [ ] 完整测试套件（覆盖率 > 80%）
- [ ] CI (GitHub Actions)：lint + 单元测试 + 健康检查
- [ ] `pip install n9r20-core` PyPI 发布

#### 运行时优化
- [ ] TensionBus 异步事件循环（替代当前顺序编排）
- [ ] 模块热插拔（无需重启即可加载新 skill/reasoner）
- [ ] 分布式实例间 TensionBus 桥接

#### 技能书生态
- [ ] 技能书质量评测社区计划落地
- [ ] 首个社区贡献的技能书（非 kaile9 本人制作）
- [ ] 技能书导入冲突的 Web 确认界面
- [ ] 语义距离碰撞检测（接入嵌入模型）

#### 部署指南
- [ ] Claude Code 部署指南
- [ ] Cursor 部署指南
- [ ] Docker 化部署

---

### 🌊 9R-2.0 (未来 · Future)

#### 认知架构升级
- [ ] 动态张力类型生成（不再限于预定义 6 种）
- [ ] 跨实例概念图谱联邦（多个 KL9 实例共享部分图谱）
- [ ] 张力漂移检测——长期运行中检测 Constitutional DNA 是否被隐性侵蚀

#### 技能书 2.0
- [ ] 自动反视角生成（导入时自动生成对抗性解读）
- [ ] 技能书谱系追踪——追溯概念在不同实例间的传播路径
- [ ] 多语言技能书交叉验证

#### 社区与生态
- [ ] Web Demo（浏览器中试用 KL9）
- [ ] 社区贡献的视角类型注册表
- [ ] KL9 技能书质量独立榜单

---

### 🔒 不变 · Immutable

- **Constitutional DNA 五原则**（修改即身份断裂）
  - 二重性存在 · 张力悬置 · 概念对话 · 结构性情感 · 拒绝收束
- 拒绝缝合/综合/调和
- 技能书禁止 AI 摘要/二手文献产生

---

### 📐 版本策略 · Versioning

| 层级 | 含义 | 示例 |
|:---|:---|:---|
| 大版本 (9R-**X**.y) | 架构级变更，可能不向后兼容 | 9R-2.0 |
| 小版本 (9R-x.**Y**) | 功能增量，向后兼容 | 9R-2.1 |
| 语义版本 (x.y.z) | 标准 semver，用于 PyPI | 2.1.0 |

大版本升级时，上一大版本最新小版本归档到 `archive/v{X}/`。

---

## 5. 版本历史 · Release History

### [9R-2.0] (2.0.0) — 2026-05-06 — N9R20Framework 认知架构

#### 架构重构
- 升级至 N9R20Framework 认知架构
- 模块命名从 `kl9_*` 迁移至 `n9r20_*`
- 版本号升级：9R-1.5 → 9R-2.0（semver: 1.5.0 → 2.0.0）
- 旧架构完整归档至 `archive/9R-1.5/`
- 新架构核心模块：n9r20_core/（~12 模块）+ n9r20_skillbook/（~8 模块）

#### 新增
- n9r20_core/n9r20_structures.py：核心数据结构
- n9r20_core/n9r20_tension_bus.py：事件总线
- n9r20_core/n9r20_adaptive_router.py：自适应路由
- n9r20_core/n9r20_dual_reasoner.py：双视角推理
- n9r20_core/n9r20_compression_core.py：四模压缩引擎
- n9r20_core/n9r20_semantic_graph.py：概念图谱
- n9r20_core/n9r20_memory_learner.py：记忆学习
- n9r20_core/n9r20_llm_evaluator.py：LLM 评估器
- docs/FRAMEWORK.md, DEPLOY.md, TEST_REPORT.md 等

### [9R-1.5] (1.5.0) — 2026-05-05 — 技能书吸收协议

#### 架构重构
- 统一版本号命名：9R-1.5（9=开了玖, R=RHIZOME, 1.5=版本号）
- 清理旧 kailejiu-* 架构，保留 kl9_* 新架构
- 恢复核心模块到 kl9_core/（12 模块，~5236 行）
- 修复所有硬编码路径，确保跨环境可移植

#### 新增
- kl9_core/version.py：版本常量与解析
- quickstart.py：一键启动脚本
- kl9_core/health.py：健康检查框架

#### 修复
- 删除 63 个无关 AstrBot skill 目录
- 删除 9 个重复核心文件
- 修复 c8c807e 误提交导致的文件丢失/篡改

---

### [1.1.0] — 2026-05-06 — 双维度评分系统

#### Added
- **双维度评分引擎** (`skills/scorer.py`): 信任公式 `trust = quality × (1 - difficulty/200)`
- **难度评估** (`estimate_difficulty`): 四维度启发式评分（风格密度/信息密度/观点创新/引用密度）
- **质量评估** (`estimate_quality`): 基于 ProductionRecord 的客观评分（轮数+验证+反视角）
- **信任阈值**: 4 级吸收策略（完整/补充/选择性/拒绝）
- **数据模型** (`ProductionRecord`, `DifficultyBreakdown`): 制作记录与难度细分
- **v1.1 验证规则**: `difficulty` 和 `quality_score` 为 FATAL 必填，`production_record` 为 WARNING
- **导出增强**: `export_skillbook.py` 支持 `--rounds`, `--verify`, `--hours`, `--counter` 参数
- **导出自动评分**: `export_graph_to_skillbook()` 自动执行难度/质量评估
- **导入信任检查**: `import_skill_book()` 和 `import_skillbook_to_graph()` 在 import 前评估信任
- **向后兼容**: v1.0 的 `quality_tier` 自动映射为 `quality_score = quality_tier × 20`

#### Changed
- `SkillBookManifest`: 新增 `difficulty`, `quality_score`, `production_record`, `difficulty_breakdown`
- `validate_manifest`: 接受 v1.0 和 v1.1 双版本
- `import_skill_book`: 默认版本号升级为 "1.1"
- `export_graph_to_skillbook`: 输出 v1.1 格式，自动嵌入评分
- `import_skillbook_to_graph`: 返回结果包含 `trust` 和 `trust_level`
- 样本技能书更新为 v1.1 完整格式
- `SKILLBOOK_STANDARD.md` 更新为 v1.1 完整规范

---

### [1.5.0] — 2026-05-05 — 技能书吸收协议

#### Added
- **SQLite ↔ JSON 桥接** (`skills/bridge.py`): 双向导入/导出，含碰撞检测、影子分叉与张力局部重算
- **SQLite schema 扩展**: `nodes` 表新增 `perspective_a`, `perspective_b`, `tension_score`, `local_confidence`, `is_shadow`, `shadow_of` 六列
- **`store_concept()` 增强**: 支持所有新字段的持久化
- **CLI 导出工具** (`scripts/export_skillbook.py`): 一行命令将 SQLite 图谱导出为标准技能书 JSON
- **桥接测试套件** (`tests/test_bridge.py`): 11 个测试覆盖导出/导入/往返/边完整性/新字段
- **样本技能书** (`skills/de/Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md`): Brodbeck 货币现象学，螺旋递归论证结构，146 行
- **版本公告** (`docs/releases/RELEASE_v1.5.0.md`): v1.5.0 发布说明

#### Changed
- `graph_backend._get_conn()` 新增静默列迁移（try/except pass，兼容旧数据库）
- `graph_backend.store_concept()` 签名扩展：新增 6 个可选参数（向后兼容）
- README 更新：技能书吸收协议使用说明、核心原理图示、统计数字更新

---

### [1.0.0] — Initial Release

#### Core
- DualState 双视角加载
- TensionBus 事件总线
- dual_fold 递归折叠引擎
- 6 种张力类型 × 7 组推荐二重组合
- Constitutional DNA 五原则
- 9 层模块架构（core, reasoner, soul, graph, research, memory, learner, orchestrator, shared）
- SQLite 概念图谱（BM25 检索 + 子图遍历）
- SQLite 记忆后端（sessions, feedback, reading_list）
- 技能书 JSON 格式标准（validator, matcher, merger, tension, importer）

---

## 6. 行为准则 · Code of Conduct

- 尊重每个人的贡献
- 不修改 Constitutional DNA（五原则是不可变的）
- 保持建设性的对话

> *KL9-RHIZOME was born from a late-night exam prep session. It's not a company product. It's a labor of love. Be kind.*

---

*中英双语版由 DeepSeek V4 Pro 辅助创作 · Bilingual version co-created with DeepSeek V4 Pro*
