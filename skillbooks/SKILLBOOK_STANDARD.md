# KL9-RHIZOME 技能书规范 · Skill Book Standard v1.2

> 纯规范文档。使用指南见 [skillbooks/README.md](README.md)。

---

## 文件格式 · File Format

```
skillbooks/{语言}/{Author-Title-Year}/SKILL.md
```

**命名规则**：`Author-Title-Year`，书名空格用 `_` 替代。

示例：`Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md`

### 不可查标记 · Unverifiable Markers

| 标记 | 含义 | 示例 |
|:--:|------|------|
| `~` | 传统归因，学界有争议 | `~Aśvaghoṣa`（传为马鸣造）、`~554`（译经年） |
| `?` | 无可靠记载，推测值 | `?200_BCE`（约公元前200年） |

### 原文失传 · Lost Originals

古籍梵文原典不存时，以现存最早完整版本的语言作为 `book_language`，并在书目中注明。见 [README.md § 可能的影响因素](README.md#可能的影响因素-factors-affecting-quality)。

---

## SKILL.md 结构 · Structure

```yaml
---
name: Author-Title-Year
description: 一句话 + 一段话描述，标注可被 kailejiu-research 征用
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

**推进类型**：线性演绎 / 螺旋递归 / 立破并行 / 现象学展开 / ...

**关键转折点**：
1. **第 N 节 → 转折描述**：论证翻转型描述...
2. ...

## 核心概念
（概念定义 + 引文，引文必须使用源语言）

## 后续研究问题
（开放问题列表，供 dialogical_activation 触发用）

## 五分段結構一覽（如适用）
（古籍五分段：因缘分/立义分/解释分/修行信心分/劝修利益分）

---

激活方式说明（末尾）：
激活方式：`kailejiu-research` 通过 `dialogical_activation` 征用。
```

---

## 双维度评分 · Scoring

### 难度分 (difficulty) — 0-100

LLM 评估四项取均值：

| 维度 | 评估内容 |
|------|---------|
| 风格密度 | 句子复杂度、术语密度、修辞层次 |
| 信息密度 | 概念密度、论证步骤数、隐含预设量 |
| 观点创新 | 与传统叙事的偏离度、原创概念比例 |
| 引用密度 | 跨文本对话频率、引用广度与深度 |

### 质量分 (quality_score) — 0-100

```
quality = min(rounds × 20, 60) + verify_score(0/10/20) + min(counter × 5, 20)
```

| 制作记录字段 | 贡献 |
|-------------|------|
| `rounds_completed` | ×20，最多 60 分 |
| `verification_method` | none:0, spot-check:10, full-reread/external:20 |
| `counter_perspectives` | 每个反视角 ×5，最多 20 分 |

### 模型能力上限 — 动态

```
ceiling = min(100, (HLE×0.5 + Arena_norm×0.25 + CW_norm×0.25) × 1.15 + 15)
arena_norm = min(100, (arena_elo − 1200) / 3.0)
```

### 语言补偿

| LLM族 | 中文书 | 英文书 | 其他 |
|--------|:--:|:--:|:--:|
| zh | +3% | 0% | −3% |
| en | −3% | +3% | 0% |

补偿后 ≤ ceiling（同层不反超）。

### 信任模型

```
trust = quality_adjusted × (1 − difficulty/200)    → [0,100]
≥90 full | 60-90 supplementary | 30-60 selective | <30 reject
```

---

## 制作记录 · Production Record

| 字段 | 必需 | 类型 | 描述 |
|------|:--:|------|------|
| `rounds_completed` | ✅ | int | 学习轮数，≥1 |
| `verification_method` | ✅ | string | `none` / `spot-check` / `full-reread` / `external` |
| `counter_perspectives` | ✅ | list[str] | 反视角列表 |
| `total_hours` | ✅ | float | 投入小时数 |
| `generating_model` | ✅ | string | 生成时使用的 LLM 模型 ID，如 `deepseek-v4-pro`、`kimi-2.6` |

---

## 上传检查清单 · Pre-Upload Checklist

- [ ] 原著通读完成——逐页，非跳读，非摘要
- [ ] ≥1 轮完整学习循环
- [ ] SKILL.md 包含全部必填段（书目 + 论证结构 + 核心概念）
- [ ] 引文使用源语言（非译本）
- [ ] 文件命名符合 `Author-Title-Year/SKILL.md`
- [ ] 放入正确语言目录
- [ ] 不可查字段已标记 `~` 或 `?`
- [ ] 已标注 `generating_model`（生成时使用的 LLM 模型 ID）

---

## 禁止项 · Prohibitions

- ❌ AI 摘要/二手文献产生
- ❌ 伪造 rounds_completed 或 verification_method
- ❌ 多书合并（一书一谱）
- ❌ 引文不标注源语言

---

*"一场真实的阅读。一次真实的折叠。其他都是噪音。"*
