# KL9-Architecture 目录层级说明 · Issue #3

> 明确 `core/`、`skillbook/`、`skills/` 三个目录的边界、当前问题与清理建议。

---

## 一、三层架构设计意图

| 目录 | 定位 | 内容类型 | 运行时角色 |
|------|------|----------|----------|
| **`core/`** | 9R-2.0 核心认知引擎 | Python 模块（数据结构、算法、事件总线、配置） | **运行时加载** |
| **`skillbook/`** | 技能书内容仓库 | Markdown 文档（SKILL.md）+ JSON 清单 | **内容定义** |
| **`skills/`** | ⚠️ 待清理 / 历史遗留 | 与 `skillbook/` 完全重复 | — |

---

## 二、各目录详细边界

### 2.1 `core/` — 运行时引擎

**职责**：提供 9R-2.0 的全部运行时代码。任何 import `core.xxx` 的地方都应指向这里。

**当前文件清单**（17 个 Python 文件 + 2 个 meta）：

```
core/
  __init__.py              — 公开 API：structures, tension_bus, llm_evaluator
  README.md                — 模块总览
  version.py               — 版本常量
  n9r20_structures.py      — DualState, Tension, Perspective 等数据结构
  n9r20_tension_bus.py     — 去中心化事件总线
  n9r20_dual_reasoner.py   — 双视角推理引擎
  n9r20_compression_core.py — 四模式压缩引擎
  n9r20_llm_compressor.py  — LLM 语义压缩器（Issue #2 修改后：依赖注入模式）
  n9r20_llm_evaluator.py   — LLM 评估器（fold 深度分配）
  n9r20_semantic_graph.py  — 语义知识图谱
  n9r20_memory_learner.py  — 记忆学习器
  n9r20_adaptive_router.py — 自适应路由器
  n9r20_skillbook_compat.py — 旧版 SkillBook 兼容层（9R-1.5 → 9R-2.0 迁移）
  n9r20_config.py          — 全局配置常量
  n9r20_user_config.py     — 用户可覆盖配置
  n9r20_production_logger.py — 制作记录日志
  n9r20_utils.py           — 工具函数
```

**边界规则**：
- 所有 Python 运行时模块**只能**放在 `core/`
- 其他目录不应出现 `.py` 文件（除了 `__init__.py` 作为包标记）

---

### 2.2 `skillbook/` — 技能书内容仓库

**职责**：存储**内容定义**——即 AI 处理特定领域/文本时的"工作手册"。不是代码，是 Markdown 格式的技能书文档。

**文件格式规范**（见 `skillbook/prebuilt/SKILLBOOK_STANDARD.md`）：

```
skillbook/
  README.md                    — 技能书系统说明
  SKILLBOOK_STANDARD.md        — 格式规范（预置在 prebuilt/ 下）
  __init__.py                  — 包标记（应极简，不导运行时类）
  prebuilt/
    zh/
      Asvaghosa-Dasheng-Qixin-Lun-554/SKILL.md
      ...（更多中文技能书）
    en/
      ...（英文技能书）
    de/
      ...（德文技能书）
    fr/
      ...（法文技能书）
    other/
      ...（其他语言）
```

**技能书内容示例**（`SKILL.md`）：
- 书目信息（作者、年份、语言、学科定位）
- 全书论证推进结构
- 核心概念定义 + 源语言引文
- 后续研究问题
- 制作记录（rounds_completed, verification_method, counter_perspectives）

**边界规则**：
- `skillbook/` 里**只能**有 SKILL.md、JSON 清单、规范文档
- **禁止**放入 Python 运行时模块（这是当前违反的规则）

---

### 2.3 `skills/` — 现状与问题

**当前状态**：与 `skillbook/` **完全重复**。

**对比证据**（通过 GitHub API 逐文件校验）：

| 文件 | `skillbook/` | `skills/` | 结论 |
|------|:----------:|:-------:|------|
| `README.md` | 存在 | 存在 | **内容逐字相同** |
| `__init__.py` | 存在 | 存在 | **内容逐字相同** |
| `n9r20_adaptive_router.py` | 存在 | 存在 | **文件名相同** |
| `n9r20_compression_core.py` | 存在 | 存在 | **文件名相同** |
| `n9r20_dual_reasoner.py` | 存在 | 存在 | **文件名相同** |
| `n9r20_memory_learner.py` | 存在 | 存在 | **文件名相同** |
| `n9r20_semantic_graph.py` | 存在 | 存在 | **文件名相同** |
| `prebuilt/` | 存在 | 存在 | **子目录结构相同**（zh, en, de, fr, other） |
| `prebuilt/SKILLBOOK_STANDARD.md` | 存在 | 存在 | 规范文档 |

**额外问题**：
1. `README.md` 中的安装指令写的是 `cp -r skills/kailejiu-core ~/.agents/skills/`，但 `skills/` 下**没有 `kailejiu-core` 子目录**
2. `skills/` 和 `skillbook/` 都混入了 `n9r20_*.py` 运行时模块——这打破了 `core/` 作为唯一运行时源码目录的边界

---

## 三、问题诊断

### 问题 1：重复目录（`skills/` vs `skillbook/`）

**影响**：
- 维护成本翻倍：改一处需要同步改两处
- 引入困惑：新贡献者不知道该往哪放
- Git 历史混乱：同一个概念可能在两个目录有独立修改记录

**根因推测**：
- `skills/` 可能是 9R-1.x 时期的旧目录名
- 重构为 `skillbook/` 时未清理旧目录
- 或者 `skills/` 是面向用户的"安装源"，`skillbook/` 是内部开发仓库——但两者内容完全相同，说明这层区分没有实现

### 问题 2：运行时模块越界

**影响**：
- `core/` 不再是唯一源码目录，模块加载顺序不确定
- 如果 `skills/` 和 `skillbook/` 的 `.py` 文件与 `core/` 不同步，会产生运行时歧义

**当前越界文件**（需从 `skills/` 和 `skillbook/` 移除）：
```
n9r20_adaptive_router.py
n9r20_compression_core.py
n9r20_dual_reasoner.py
n9r20_memory_learner.py
n9r20_semantic_graph.py
```

### 问题 3：README 安装指令失效

`cp -r skills/kailejiu-core ~/.agents/skills/` 中的 `kailejiu-core` 路径不存在，说明文档和实际结构已脱节。

---

## 四、清理方案

### 方案 A：彻底合并（推荐）

1. **删除 `skills/` 目录**（确认 `skillbook/` 已包含全部内容后）
2. **清理 `skillbook/` 中的 `.py` 文件**：
   - 删除 `skillbook/n9r20_*.py`（5 个运行时模块）
   - 重写 `skillbook/__init__.py` 为极简包标记（不导运行时类）
3. **重写 `skillbook/README.md`**：
   - 明确技能书是"内容仓库"而非"代码仓库"
   - 修正安装路径（指向 `prebuilt/{lang}/...`）
4. **验证**：确保 `from core import xxx` 仍能正常工作

### 方案 B：保留区分（如果确实需要两层）

如果 `skills/` 和 `skillbook/` 确实有不同定位：

| 目录 | 新定位 | 内容 |
|------|--------|------|
| `skillbook/` | **源仓库** | 原始 SKILL.md 源文件 + 制作工具 |
| `skills/` | **分发/安装包** | `skillbook/` 的构建产物（去重、去工具，只留用户需要的 SKILL.md） |

但这需要：
- 建立从 `skillbook/` → `skills/` 的构建/同步流程
- `skills/` 里不放 `.py` 文件（除了构建脚本）
- 两个 README 内容差异化

**当前状态不支持方案 B**：因为没有构建流程，内容也完全相同。

---

## 五、目录边界总览（清理后）

```
KL9-Architecture/
├── core/                          ← Python 运行时引擎（唯一源码目录）
│   ├── __init__.py
│   ├── n9r20_*.py                 ← 所有核心模块
│   └── README.md
│
├── skillbook/                     ← 技能书内容仓库（Markdown 文档）
│   ├── __init__.py                ← 极简包标记
│   ├── README.md                  ← 技能书系统说明 + 安装指南
│   ├── prebuilt/
│   │   ├── SKILLBOOK_STANDARD.md  ← 格式规范
│   │   ├── zh/
│   │   │   └── Author-Title-Year/
│   │   │       └── SKILL.md
│   │   ├── en/
│   │   ├── de/
│   │   ├── fr/
│   │   └── other/
│   └── ...                        ← 制作工具 / 批量导入脚本（如有）
│
├── archive/                       ← 历史版本归档
├── docs/                          ← 架构文档
├── examples/                      ← 使用示例
├── tests/                         ← 测试用例
├── scripts/                       ← 运维/部署脚本
├── assets/                        ← 静态资源
├── README.md                      ← 根目录总览
├── CHANGELOG.md
└── LICENSE
```

---

## 六、实施优先级

| 优先级 | 任务 | 操作 |
|:------:|------|------|
| P0 | 删除 `skills/` 目录 | `git rm -rf skills/` |
| P0 | 删除 `skillbook/*.py` | `git rm skillbook/n9r20_*.py` |
| P1 | 重写 `skillbook/__init__.py` | 极简包标记 |
| P1 | 重写 `skillbook/README.md` | 修正定位 + 安装路径 |
| P2 | 建立 CI 检查 | 禁止非 `core/` 目录出现 `n9r20_*.py` |

---

*文档生成时间：2026-05-07*
*基于仓库 commit HEAD 的实时文件扫描*
