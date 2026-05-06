# 📖 KL9 技能书系统 · Skill Book System

> **最后更新**: 2026-05-06 · 当前版本: **9R-1.5** · 规范版本: **v1.2**

---

## 目录 · Table of Contents

1. [概览 · Overview](#1-概览--overview)
2. [技能书库 · Skill Book Library](#2-技能书库--skill-book-library)
3. [格式规范 · Format Standard](#3-格式规范--format-standard)
4. [吸收协议 · Absorption Protocol](#4-吸收协议--absorption-protocol)
5. [评分体系 · Scoring System](#5-评分体系--scoring-system)
6. [社区评测 · Community Evaluation](#6-社区评测--community-evaluation)
7. [贡献指南 · Contribution Guide](#7-贡献指南--contribution-guide)

---

## 1. 概览 · Overview

技能书是 KL9-RHIZOME 的去中心化知识传播机制：读完一本书 → 完成学习循环 → 导出 → 其他实例导入。

*Skill books are KL9-RHIZOME's decentralized knowledge propagation mechanism: read a book → complete learning cycles → export → other instances import.*

支持双维度评分（难度+质量）、语言偏差补偿、信任分级吸收。

---

## 2. 技能书库 · Skill Book Library

### 核心理念 · Core Philosophy

> 技能书不是摘要。技能书是精读后的认知残留。
> *A skill book is not a summary. It is the cognitive residue of deep reading.*

### 目录结构 · Directory Structure

```
skillbooks/{语言}/{Author-Title-Year}/SKILL.md
```

**命名规则**: `Author-Title-Year`，书名空格用 `_` 替代。

示例: `Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md`

### 语言目录 · Language Directories

| 目录 | 状态 | 说明 |
|------|:--:|------|
| `skillbooks/zh/` | ✅ 1 本 | 中文原著 |
| `skillbooks/fr/` | ✅ 1 本 | 法语原著 |
| `skillbooks/de/` | ✅ 1 本 | 德语原著 |
| `skillbooks/en/` | ⬜ 预留 | 英语原著（待贡献） |
| `skillbooks/other/` | ⬜ 预留 | 其他语言（待贡献） |

### 不可查标记 · Unverifiable Markers

| 标记 | 含义 | 示例 |
|:--:|------|------|
| `~` | 传统归因，学界有争议 | `~Aśvaghoṣa`（传为马鸣造）、`~554`（译经年） |
| `?` | 无可靠记载，推测值 | `?200_BCE`（约公元前200年） |

### 原文失传 · Lost Originals

古籍梵文原典不存时，以现存最早完整版本的语言作为 `book_language`，并在书目中注明。

### 现有藏书 · Catalog

| 语言 | 著作 | 作者 | 年份 | 格式 |
|:--:|------|------|:--:|------|
| DE | [Phänomenologie des Geldes](de/Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md) | Brodbeck | 2023 | 螺旋递归，货币现象学 |
| FR | [Les mots et les choses](fr/Foucault-Les-Mots-et-les-Choses-1966/SKILL.md) | Foucault | 1966 | épistémè 考古学，人之死 |
| ZH | [大乘起信論](zh/Asvaghosa-Dasheng-Qixin-Lun-554/SKILL.md) | ~Aśvaghoṣa | ~554 | 一心二門，如來藏框架 |

---

## 3. 格式规范 · Format Standard

### SKILL.md 结构 · Structure

```yaml
---
name: Author-Title-Year
description: 一句话 + 一段话描述，标注可被 kl9_research 征用
generating_model: 生成时使用的 LLM 模型 ID
---

# 书名 — 作者

## 书目信息
| 字段 | 内容 |
|:---|:---|
| **作者** | 原著语言名 |
| **年份** | 出版/译经年份 |
| **语言** | 原文语言（注明译本情况） |
| **定位** | 学科领域 + 学术地位 |

## 全书论证推进结构
> 此描述纳入质量分考评。引用时必须包含本部分。

**推进类型**: 线性演绎 / 螺旋递归 / 立破并行 / 现象学展开 / ...

**关键转折点**:
1. **第 N 节 → 转折描述**: 论证翻转型描述...
2. ...

## 核心概念
（概念定义 + 引文，引文必须使用源语言）

## 后续研究问题
（开放问题列表，供 dialogical_activation 触发用）

## 五分段結構一覽（如适用）
（古籍五分段：因缘分/立义分/解释分/修行信心分/劝修利益分）

---

激活方式说明（末尾）:
激活方式: `kl9_research` 通过 `dialogical_activation` 征用。
```

### 双维度评分 · Scoring

#### 难度分 (difficulty) — 0-100

LLM 评估原著四项取均值：

| 维度 | 评估内容 |
|------|---------|
| 风格密度 | 句子复杂度、术语密度、修辞层次 |
| 信息密度 | 概念密度、论证步骤数、隐含预设量 |
| 观点创新 | 与传统叙事的偏离度、原创概念比例 |
| 引用密度 | 跨文本对话频率、引用广度与深度 |

#### 质量分 (quality_score) — 0-100

```
quality = min(rounds × 20, 60) + verify_score(0/10/20) + min(counter × 5, 20)
```

| 制作记录字段 | 贡献 |
|-------------|------|
| `rounds_completed` | ×20，最多 60 分 |
| `verification_method` | none:0, spot-check:10, full-reread/external:20 |
| `counter_perspectives` | 每个反视角 ×5，最多 20 分 |

#### 模型能力上限 — 动态

```
ceiling = min(100, (HLE×0.5 + Arena_norm×0.25 + CW_norm×0.25) × 1.15 + 15)
arena_norm = min(100, (arena_elo − 1200) / 3.0)
```

#### 语言补偿

| LLM族 | 中文书 | 英文书 | 其他 |
|--------|:--:|:--:|:--:|
| zh | +3% | 0% | −3% |
| en | −3% | +3% | 0% |

补偿后 ≤ ceiling（同层不反超）。

### 制作记录 · Production Record

| 字段 | 必需 | 类型 | 描述 |
|------|:--:|------|------|
| `rounds_completed` | ✅ | int | 学习轮数，≥1 |
| `verification_method` | ✅ | string | `none` / `spot-check` / `full-reread` / `external` |
| `counter_perspectives` | ✅ | list[str] | 反视角列表 |
| `total_hours` | ✅ | float | 投入小时数 |
| `generating_model` | ✅ | string | 生成时使用的 LLM 模型 ID |

### 上传检查清单 · Pre-Upload Checklist

- [ ] 原著通读完成——逐页，非跳读，非摘要
- [ ] ≥1 轮完整学习循环
- [ ] SKILL.md 包含全部必填段（书目 + 论证结构 + 核心概念）
- [ ] 引文使用源语言（非译本）
- [ ] 文件命名符合 `Author-Title-Year/SKILL.md`
- [ ] 放入正确语言目录
- [ ] 不可查字段已标记 `~` 或 `?`
- [ ] 已标注 `generating_model`

### 禁止项 · Prohibitions

- ❌ AI 摘要/二手文献产生
- ❌ 伪造 rounds_completed 或 verification_method
- ❌ 多书合并（一书一谱）
- ❌ 引文不标注源语言

---

## 4. 吸收协议 · Absorption Protocol

### 模块概览 · Modules

KL9-RHIZOME 9R-1.5 实例学习成果的导入/导出/评分引擎。碰撞分叉、张力局部重算、三源动态评分。

| 模块 | 职责 | 代码行数 |
|------|------|:---:|
| `models.py` | ConceptNode, SkillBookManifest, ProductionRecord, DifficultyBreakdown | 95 |
| `validator.py` | Manifest 校验 (FATAL/WARNING) + v1.0/v1.1 向后兼容 | 189 |
| `matcher.py` | Levenshtein 相似度 + 三档碰撞分类 (exact ≥95% / nearby 70-95%) | 65 |
| `merger.py` | 核心合并：近似合并定义、碰撞分叉影子节点、无冲突新增 | 96 |
| `tension.py` | 2-hop 子图张力局部重算 | 43 |
| `scorer.py` | HLE+Arena 三源聚合 + 语言偏差 ±3% + 信任公式 | 501 |
| `importer.py` | 9步导入流水线 (JSON 后端) | 208 |
| `bridge.py` | SQLite ↔ JSON 双向桥接 | 488 |

### 导入流水线 · Import Pipeline

```
加载 JSON → 校验 manifest → 加载本地图谱 → 沙盒命名空间
→ 碰撞检测 → 合并 (近似/分叉/新增) → 2-hop 张力重算
→ 全局 stale 标记 → 持久化
```

### 核心设计原则 · Design Principles

#### 原则 1: 碰撞分叉优于强行合并
*Bifurcation over forced merge.*

同名但定义不同的概念不合并——在两个节点间创建 `collision_tension` 边，标记为需要人类裁决的冲突。

#### 原则 2: 溯源高于权重
*Provenance over weight.*

每个导入的概念节点携带来源信息——从哪个技能书来、哪个 LLM 生成、哪个架构版本。

#### 原则 3: 暂存优于直接激活
*Staging over direct activation.*

导入分两阶段：先加载到隔离的暂存图谱，检测完冲突后再由用户选择性地激活节点。

#### 原则 4: 回滚优于覆盖
*Rollback over overwrite.*

每次导入前保存 snapshot。激活后如果检测到全局张力梯度异常波动（任何张力强度变化 > 0.3），触发回滚建议。

### 信任公式 · Trust Formula

```
trust = quality_adjusted × (1 − difficulty/200)    → [0, 100]
```

| 信任分 | 吸收策略 |
|:--:|------|
| ≥90 | **完整吸收** — 全部概念直接导入 |
| 60-90 | **补充学习** — 标注需交叉验证的概念 |
| 30-60 | **选择性提取** — 仅采纳高置信度概念 |
| <30 | **拒绝** — 导入终止 |

### 使用方式 · Usage

#### 参考技能书（SKILL.md）
`kailejiu-research` 通过 `dialogical_activation` 直接征用 `skillbooks/` 中的 SKILL.md。

#### 可导入技能书（.skillbook.json）
```python
from kl9_skillbook.bridge import import_skillbook_to_graph

result = import_skillbook_to_graph("skillbooks/de/Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json")
# → {success, trust, trust_level, nodes_added, ...}
```

> 当前藏书均为 SKILL.md 格式。`.skillbook.json` 用于概念级图谱导入。

---

## 5. 评分体系 · Scoring System

### 难度分（0-100）

LLM 评估原著四项取均值：

| 维度 | 评估内容 |
|------|---------|
| 风格密度 | 句子复杂度、术语密度、修辞层次 |
| 信息密度 | 概念密度、论证步骤数、隐含预设量 |
| 观点创新 | 与传统叙事的偏离度、原创概念比例 |
| 引用密度 | 跨文本对话频率、引用广度与深度 |

### 质量分（0-100）

基于制作记录的客观评分：

```
quality = min(rounds × 20, 60) + verify_score(0/10/20) + min(counter × 5, 20)
```

| 分 | 条件 |
|:--:|------|
| 0-20 | 单轮学习，未验证 |
| 20-40 | ≥2轮，有基本概念图谱 |
| 40-60 | ≥2轮，含反视角，张力清晰 |
| 60-80 | ≥3轮，交叉验证，定义精确 |
| 80-100 | ≥3轮 + 二手文献 + 反视角充分展开 |

### 模型能力上限 · Model Ceiling（动态）

```
arena_norm = min(100, (arena_elo − 1200) / 3.0)
cw_norm    = min(100, (cw_elo    − 1200) / 3.0)
combined   = HLE × 0.50 + arena_norm × 0.25 + cw_norm × 0.25
ceiling    = min(100, combined × 1.15 + 15)
```

| 来源 | 权重 | 说明 |
|------|:--:|------|
| HLE (Humanity's Last Exam) | 50% | 极限推理，区分度最高 |
| Arena Overall Elo | 25% | 人类偏好，综合对话质量 |
| Arena Creative Writing | 25% | 最接近哲学文本生成质量的代理 |

> 数据来源: llm-stats.com, openlm.ai。此为启发式代理，非直接质量度量。

### 语言补偿 · Language Bias

| LLM 族 | 中文书 | 英文书 | 其他 |
|--------|:--:|:--:|:--:|
| zh (DeepSeek / Qwen / Kimi) | **+3%** | 0% | −3% |
| en (GPT / Claude / Gemini) | −3% | **+3%** | 0% |

补偿后质量分不超过模型 ceiling（同层不反超）。

### 信任公式 · Trust Formula

```
trust = quality_adjusted × (1 − difficulty / 200)    → [0, 100]
```

| 信任分 | 吸收策略 |
|:--:|------|
| ≥90 | **完整吸收** — 全部概念直接导入 |
| 60-90 | **补充学习** — 标注需交叉验证的概念 |
| 30-60 | **选择性提取** — 仅采纳高置信度概念 |
| <30 | **拒绝** — 导入终止 |

### 可能的影响因素 · Factors Affecting Quality

| 因素 | 影响 | 缓解措施 |
|------|------|---------|
| **LLM 认知偏差** | 模型的语言/文化偏好影响概念提取 | 语言补偿 ±3% + 跨模型 ceiling 保护 |
| **阅读深度不足** | 跳读/速读导致概念表面化 | 强制 rounds≥1 + quality_notes 校验 |
| **AI 摘要污染** | 基于二手文献产生伪技能书 | 禁止项（Prohibitions）+ PR review |
| **翻译失真** | 非原文阅读导致术语偏移 | `book_language` 标注原文语言 |
| **原文失传** | 古籍原本不可查 | `~` 不可查标记 + 现存最早版本作为源文本 |
| **基准榜单漂移** | HLE/Arena 分数随时间变化 | 定期更新 BENCHMARK_DATA（社区协作） |
| **同质化** | 同一本书被多人数次提交 | 冲突分叉（影子节点），保留多视角 |

---

## 6. 社区评测 · Community Evaluation

### 问题 · Problem

当前评分系统使用 HLE + Arena Elo + Arena Creative Writing 作为代理指标。但没有任何基准能直接衡量"模型能不能把一本哲学/社科著作读懂并转化为高质量技能书"。我们承认：**这是路灯效应——我们测了能测的，没测该测的。**

### Designer 的方案 · The Plan

对每个模型生成 3 本技能书（统一 3 个 prompt），由人类评估三项：

| 维度 | 权重 | 说明 |
|------|:--:|------|
| 结构完整度 | 40% | 必填字段齐全、manifest 正确、概念嵌套合理 |
| 信息密度 | 30% | 每百 token 独有事实数（去重后） |
| 引用准确率 | 30% | 有明确源出处的声明比例 |

综合分 = (结构×0.4 + 密度×0.3 + 引用×0.3) × 1.5，封顶 100。

### 如何参与 · How to Participate

1. Fork [KL9-Architecture](https://github.com/kaile9/KL9-Architecture)
2. 选一个模型，用 `scripts/export_skillbook.py` 生成技能书
3. 填写评测记录到 `eval/records/` 目录
4. 提交 PR

### 评测模板 · Evaluation Template

```json
{
  "model": "deepseek-v4-pro",
  "book": "Phänomenologie des Geldes",
  "evaluator": "@github_username",
  "date": "2026-05-XX",
  "scores": {
    "structural_completeness": 85,
    "information_density": 72,
    "citation_accuracy": 68
  },
  "notes": "概念提取准确，但对Brodbeck的论证结构把握有偏差"
}
```

### 目标 · Goal

积累 100+ 条评测后，发布独立的 **KL9 技能书质量榜单**，替代当前代理评分。

当前代理公式(仅供参考): combined = HLE×0.50 + Arena_norm×0.25 + CW_norm×0.25

---

## 7. 贡献指南 · Contribution Guide

### 制作技能书 · Creating a Skill Book

```
通读原著（逐页，非跳读）
    ↓
完成 ≥1 轮完整学习循环（DualState + 概念图谱 + 张力结构）
    ↓
撰写 SKILL.md（含论证推进结构 + 核心概念 + 引文）
    ↓
放入 skills/ 目录 → kailejiu-research 即刻可用
    ↓
提交 PR 到 skillbooks/{语言}/ 目录
```

### 使用技能书 · Using a Skill Book

```
kailejiu-research 检测到 @skillbook: 引用
    ↓
加载 skillbooks/{语言}/{Author-Title-Year}/SKILL.md
    ↓
dialogical_activation → 理论框架注入 → DualState 构建
    ↓
概念图谱自动融合（碰撞分叉 / 近似合并 / 张力重算）
    ↓
信任评估 → full(≥90%) / supplementary(60-90%) / selective(30-60%) / reject(<30%)
```

### 贡献步骤 · Steps

1. 读完一整本书——逐页，非跳读
2. 在 KL9 实例中完成 ≥1 轮学习
3. 按本规范撰写 SKILL.md
4. 提交 PR 到对应语言目录

禁止: AI 摘要/二手文献产生、伪造制作记录、多书合并。

---

*"一场真实的阅读。一次真实的折叠。其他都是噪音。"*

*中英双语版由 DeepSeek V4 Pro 辅助创作 · Bilingual version co-created with DeepSeek V4 Pro*
