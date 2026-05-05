# KL9-RHIZOME 技能书标准 · Skill Book Standard v1.1

## 核心原则 · Core Principle

**技能书不是摘要。技能书是精读后的认知残留。**

技能书只能由深入阅读原著后产生——不来自二手文献，不来自 AI 摘要，不来自学术速读。

---

## 文件格式 · File Format

每个技能书 = **一个 `.skillbook.json` 文件**，命名规则：

```
Author-Title-Year.skillbook.json
```

例如：`Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json`

放入对应的语言目录：`de/` `en/` `fr/` `zh/` `other/`

---

## 文件结构 · File Structure

```jsonc
{
  "manifest": {
    // ═══ 基础标识 ═══
    "skill_book_id":     "brodbeck_phaenomenologie_des_geldes",
    "version":           "1.1",
    "kl9_version":       "1.5.0",
    "created_timestamp": 1746403200,
    "book_title":        "Phänomenologie des Geldes — K.-H. Brodbeck (2023)",
    "book_author":       "Karl-Heinz Brodbeck",
    "book_year":         2023,
    "book_language":     "de",

    // ═══ 双维度评分 (v1.1) ═══
    "difficulty":         68,        // 0-100, 原著阅读难度
    "quality_score":      75,        // 0-100, 技能书制作质量
    "difficulty_breakdown": {        // 难度四维度细分
      "style_density":      72,
      "info_density":       65,
      "viewpoint_novelty":  78,
      "citation_density":   57,
      "overall":            68
    },

    // ═══ 制作记录 (v1.1 必填) ═══
    "production_record": {
      "rounds_completed":      2,                  // ≥1
      "verification_method":   "spot-check",      // none|spot-check|full-reread|external
      "counter_perspectives":  ["马克思货币理论", "Simmel货币哲学"],
      "total_hours":           20.0
    },

    // ═══ 向后兼容 ═══
    "quality_tier":        4,           // deprecated v1.1, 保留用于向后兼容
    "llm_source":          "deepseek-v4-pro",
    "concept_count":       7,
    "extra": {
      "original_author":   "Karl-Heinz Brodbeck",
      "original_year":     2023,
      "language":          "de",
      "field":             "经济哲学",
      "pages":             110
    }
  },
  "concepts": {
    "concept_id": {
      "name":              "Geld als Denkform",
      "definition":        "概念定义...",
      "perspective_a":     "视角A简述",
      "perspective_b":     "视角B简述",
      "tension_score":     0.65,
      "edges":             ["other_concept_id"],
      "provenance": {
        "source_skill_book": "brodbeck_phaenomenologie_des_geldes",
        "quality_tier":      4,
        "llm_source":        "deepseek-v4-pro",
        "import_timestamp":  1714876800
      },
      "local_confidence":  1.0,
      "is_shadow":         false,
      "shadow_of":         null
    }
  }
}
```

---

## manifest 字段 · Manifest Fields

| 字段 | 必需 | 类型 | 描述 |
|------|:--:|------|------|
| `skill_book_id` | ✅ | string | 唯一标识，snake_case |
| `version` | ✅ | string | 协议版本，当前 `"1.1"` |
| `difficulty` | ✅ | float | **v1.1 必填** — 0-100 原著难度 |
| `quality_score` | ✅ | float | **v1.1 必填** — 0-100 制作质量 |
| `llm_source` | ✅ | string | 学习使用的 LLM |
| `kl9_version` | ✅ | string | 兼容的最低 KL9 版本 |
| `book_title` | ✅ | string | 完整书名 |
| `book_author` | ✅ | string | 作者名（原著语言） |
| `book_year` | ✅ | int | 出版年份 |
| `book_language` | ✅ | string | 原文语言 (`de`/`en`/`fr`/`zh`/`other`) |
| `concept_count` | ✅ | int | 概念数量 |
| `created_timestamp` | ✅ | int | Unix 时间戳 |
| `production_record` | ⚠️ | object | **v1.1 强烈建议** — 制作记录 |
| `difficulty_breakdown` | — | object | 难度四维度细分 |
| `quality_tier` | — | int | deprecated v1.1, 保留向后兼容 |
| `extra` | — | object | 扩展字段（作者、年份、语言等） |

### production_record 子字段

| 字段 | 必需 | 描述 |
|------|:--:|------|
| `rounds_completed` | ✅ | 完成的学习轮数，≥1 |
| `verification_method` | ✅ | `"none"` / `"spot-check"` / `"full-reread"` / `"external"` |
| `counter_perspectives` | ✅ | 反视角列表 (string[]) |
| `total_hours` | ✅ | 投入小时数 |

---

## 双维度评分体系 · Dual-Dimension Scoring

### 难度分 (difficulty) — 0-100

反映原著的阅读难度。v1.1 由 LLM 评估四个维度取均值：

| 维度 | 评估内容 |
|------|---------|
| **风格密度** (style_density) | 句子复杂度、术语密度、修辞层次 |
| **信息密度** (info_density) | 概念密度、论证步骤数、隐含预设量 |
| **观点创新** (viewpoint_novelty) | 与传统叙事的偏离度、原创概念比例 |
| **引用密度** (citation_density) | 跨文本对话频率、引用广度与深度 |

参考映射（0-100 与传统 1-5 的对应）：

| 难度分 | 传统 1-5 | 描述 |
|:--:|:--:|------|
| 0-20 | 1 | 科普/入门读物 |
| 20-40 | 2 | 本科教材级 |
| 40-60 | 3 | 研究生专著 |
| 60-80 | 4 | 高度抽象的理论 |
| 80-100 | 5 | 极端密集/晦涩 |

### 质量分 (quality_score) — 0-100

基于制作记录的客观评分算法：

```
quality = min(rounds_completed × 20, 60)          // 轮数最多贡献 60 分
        + (20 if verification in ("full-reread","external")
           else 10 if verification == "spot-check"
           else 0)                                 // 验证方法最多贡献 20 分
        + min(len(counter_perspectives) × 5, 20)  // 反视角最多贡献 20 分
```

裁剪到 [0, 100]。

参考映射（0-100 与传统 1-5）：

| 质量分 | 传统 1-5 | 条件 |
|:--:|:--:|------|
| 0-20 | 1 | 单轮学习，未交叉验证 |
| 20-40 | 2 | ≥2 轮，有基本概念图谱 |
| 40-60 | 3 | ≥2 轮，含反视角，张力清晰 |
| 60-80 | 4 | ≥3 轮，交叉验证，定义精确 |
| 80-100 | 5 | ≥3 轮 + 二手文献验证 + 反视角充分展开 |

---

## 模型能力评估 · Model Capability Assessment (v1.1)

KL9 使用**三源聚合**评估 LLM 模型的技能书生成能力上限（ceiling）：

```
arena_norm = min(100, (arena_elo − 1200) / 3.0)
cw_norm    = min(100, (cw_elo    − 1200) / 3.0)
combined   = HLE × 0.50 + arena_norm × 0.25 + cw_norm × 0.25
ceiling    = min(100, combined × 1.15 + 15)
```

| 来源 | 权重 | 说明 |
|------|:--:|------|
| **HLE** (Humanity's Last Exam) | 50% | 极限推理能力，前 50 模型跨度最广 |
| **Arena Overall Elo** (LMSYS Chatbot Arena) | 25% | 人类偏好投票，综合写作/对话质量 |
| **Arena Creative Writing Elo** | 25% | 子榜——最接近"哲学文本生成质量"的代理指标 |

语言补偿 ±3% 在 quality_score 上叠加后，以模型 ceiling 为上限（跨模型不反超）。

> ⚠️ **声明**: 此为启发式代理系统。基准分数不直接测量技能书质量。参见 `docs/design/` 中关于未来评测方案的讨论。

## 原文失传的处理 · Lost Originals

部分古籍梵文/巴利文原本已不可考，现存最早版本为中文译本。此时以**现存最早完整版本**的语言作为 `book_language`。

### 不可查字段标记

当作者归属、年份等信息存在争议或不可查时，使用以下标记：

| 标记 | 含义 | 示例 |
|:--:|------|------|
| `~` | 传统归因，学界有争议 | `~Aśvaghoṣa`（传为马鸣造）、`~554`（译经年份） |
| `?` | 无可靠记载，推测值 | `?200_BCE`（约公元前200年） |

这不是"向译入语言回译"，而是**承认既有事实**——现存最早的认知残留本就是中文。

---

## 信任模型 · Trust Model

### 信任公式

```
trust = quality × (1 — difficulty / 200)
```

两者均为 0-100，trust 也裁剪到 [0, 100]。

直觉：高质量提升信任，高难度降低信任。极端困难的书即使制作精良，信任也会被压低——需要更多同行验证。

### 信任阈值与吸收策略

| 信任分 | 策略 | 行为 |
|:--:|------|------|
| ≥90% | **完整吸收** (full) | 全部概念直接导入，无额外检查 |
| 60-90% | **补充学习** (supplementary) | 导入成功，标注需交叉验证的概念 |
| 30-60% | **选择性提取** (selective) | 导入成功，仅采纳高置信度概念 |
| <30% | **拒绝** (reject) | 导入终止，返回错误 |

---

## 向后兼容 · Backward Compatibility

v1.1 同时接受 v1.0 和 v1.1 格式的 manifest：

- 若 `version` 为 `"1.0"`，则 `difficulty` 和 `quality_score` 从 `quality_tier` 自动推导：
  - `quality_score = quality_tier × 20`
  - `difficulty = 50.0` (中性默认)
- 若 `version` 为 `"1.1"`，则 `difficulty` 和 `quality_score` 为必填 FATAL 字段

---

## 上传前检查清单 · Pre-Upload Checklist

- [ ] 原著通读完成——逐页，非跳读，非摘要
- [ ] 至少完成 1 轮完整学习
- [ ] manifest 所有必填字段完整（**v1.1: 含 difficulty 和 quality_score**）
- [ ] production_record 填写完整（rounds, verify, counter, hours）
- [ ] 文件命名符合 `Author-Title-Year.skillbook.json` 格式
- [ ] 放入正确的语言目录（`de/` `en/` `fr/` `zh/` `other/`）
- [ ] 已在本地验证导入不破坏现有图谱
- [ ] 信任分 ≥ 30%（否则无法被其他实例导入）

---

## 禁止项 · Prohibitions

- ❌ 基于 AI 摘要/二手文献产生
- ❌ 伪造 production_record
- ❌ 多本书合并为一个技能书（一书一谱）
- ❌ 手动篡改 difficulty_breakdown 以提高信任分

---

*"一场真实的阅读。一次真实的折叠。其他都是噪音。"*
