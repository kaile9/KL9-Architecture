# KL9-RHIZOME 技能书库 · Skill Book Library

> 技能书不是摘要。技能书是精读后的认知残留。
> *A skill book is not a summary. It is the cognitive residue of deep reading.*

---

## 格式规范 · Format

每个技能书 = 一个目录，包含一份 `SKILL.md`，按 `Author-Title-Year` 命名：

```
skillbooks/{语言}/{Author-Title-Year}/SKILL.md
```

| 部分 | 规范 | 示例 |
|------|------|------|
| 语言 | ISO 639-1 双字母 | `de` `en` `zh` `fr` |
| Author | 原著语言名 | `Brodbeck` `~Aśvaghoṣa`（`~`=不可查） |
| Title | 原著书名（空格用 `_`） | `Phaenomenologie_des_Geldes` |
| Year | 出版/译经年份 | `2023` `~554`（`~`=争议） |

完整规范见 **[SKILLBOOK_STANDARD.md](SKILLBOOK_STANDARD.md)**。

---

## 输出与学习流程 · Workflow

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

### 导入技能书 · Importing a Skill Book

```
检测到 @skillbook: 引用
    ↓
加载 SKILL.md → kailejiu-research 征用
    ↓
dialogical_activation → DualState 构建
    ↓
概念图谱自动融合（碰撞分叉 / 近似合并 / 张力重算）
    ↓
信任评估 → full(≥90%) / supplementary(60-90%) / selective(30-60%) / reject(<30%)
```

---

## 评分体系 · Scoring System

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

---

## 可能的影响因素 · Factors Affecting Quality

| 因素 | 影响 | 缓解措施 |
|------|------|---------|
| **LLM 认知偏差** | 模型的语言/文化偏好影响概念提取 | 语言补偿 ±3% + 跨模型 ceiling 保护 |
| **阅读深度不足** | 跳读/速读导致概念表面化 | 强制 rounds≥1 + quality_notes 校验 |
| **AI 摘要污染** | 基于二手文献产生伪技能书 | 禁止项（Prohibitions）+ PR review |
| **翻译失真** | 非原文阅读导致术语偏移 | `book_language` 标注原文语言 |
| **原文失传** | 古籍原本不可查（如大乘起信論） | `~` 不可查标记 + 现存最早版本作为源文本 |
| **基准榜单漂移** | HLE/Arena 分数随时间变化 | 定期更新 BENCHMARK_DATA（社区协作） |
| **同质化** | 同一本书被多人数次提交 | 冲突分叉（影子节点），保留多视角 |

---

## 现有藏书 · Catalog

| 语言 | 著作 | 作者 | 年份 | 格式 |
|:--:|------|------|:--:|------|
| DE | [Phänomenologie des Geldes](de/Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md) | Brodbeck | 2023 | 螺旋递归，货币现象学 |
| ZH | [大乘起信論](zh/Asvaghosa-Dasheng-Qixin-Lun-554/SKILL.md) | ~Aśvaghoṣa | ~554 | 一心二門，如來藏框架 |

---

## 贡献 · Contribute

1. 读完一整本书——逐页，非跳读
2. 在 KL9 实例中完成 ≥1 轮学习
3. 按 [SKILLBOOK_STANDARD.md](SKILLBOOK_STANDARD.md) 撰写 SKILL.md
4. 提交 PR 到对应语言目录

禁止：AI 摘要/二手文献产生、伪造制作记录、多书合并。
