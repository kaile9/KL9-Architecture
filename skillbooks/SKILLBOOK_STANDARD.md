# KL9-RHIZOME 技能书标准 · Skill Book Standard v1.1

## 核心原则 · Core Principle

**技能书不是摘要。技能书是精读后的认知残留。**

技能书只能由深入阅读原著后产生——不来自二手文献，不来自 AI 摘要，不来自学术速读。

## 文件格式 · File Format

每个技能书 = **一个 `.skillbook.json` 文件**，命名规则：

```
作者-书名-年份.skillbook.json
```

例如：`Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json`

## 文件结构 · File Structure

```jsonc
{
  "manifest": {
    "skill_book_id":     "作者_书名_snake_case",
    "version":           "1.1",
    "quality_tier":      4,                        // [待定] 制作质量 1-5
    "difficulty":        3,                        // [待定] 原著难度 1-5
    "llm_source":        "deepseek-v4-pro",
    "kl9_version":       "1.5",
    "created_timestamp": 1714876800,
    "book_title":        "完整书名",
    "book_author":       "作者名",
    "book_year":         2023,
    "book_language":     "de",
    "concept_count":     7,
    "rounds_completed":  2
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

## manifest 字段 · Manifest Fields

| 字段 | 必需 | 描述 |
|------|:--:|------|
| `skill_book_id` | ✅ | 唯一标识，snake_case |
| `version` | ✅ | 协议版本，当前 `"1.1"` |
| `quality_tier` | ✅ | 制作质量 1-5（见下方评分体系） |
| `difficulty` | ✅ | 原著难度 1-5（见下方评分体系） |
| `llm_source` | ✅ | 学习使用的 LLM |
| `kl9_version` | ✅ | 兼容的最低 KL9 版本 |
| `book_title` | ✅ | 完整书名 |
| `book_author` | ✅ | 作者名 |
| `book_year` | ✅ | 出版年份 |
| `book_language` | ✅ | 原文语言代码 (de/en/fr/zh/...) |
| `concept_count` | ✅ | 概念数量 |
| `rounds_completed` | ✅ | 完成的学习轮数，≥1 |
| `created_timestamp` | ✅ | Unix 时间戳 |
| `description` | — | 一句话描述 |
| `dependencies` | — | 依赖的其他技能书 ID 列表 |

## 评分体系 · Scoring System

双维度评分，各自独立：

### 难度分（1-5）：反映原著阅读难度

| 分 | 描述 | 示例 |
|:--:|------|------|
| 1 | 科普/入门读物 | 畅销经济学入门 |
| 2 | 本科教材级 | 标准学科教科书 |
| 3 | 研究生专著 | 中等抽象的理论著作 |
| 4 | 高度抽象的理论 | 现象学/批判理论 |
| 5 | 极端密集/晦涩 | 黑格尔、海德格尔级别 |

### 质量分（1-5）：反映技能书制作质量

| 分 | 条件 |
|:--:|------|
| 1 | 单轮学习，未交叉验证 |
| 2 | ≥2轮学习，有基本概念图谱 |
| 3 | ≥2轮，含反视角，张力结构清晰 |
| 4 | ≥3轮，交叉验证，概念定义精确 |
| 5 | ≥3轮 + 二手文献验证 + 反视角充分展开 |

## 上传前检查清单 · Pre-Upload Checklist

- [ ] 原著通读完成——逐页，非跳读，非摘要
- [ ] 至少完成 1 轮完整学习
- [ ] manifest 所有必填字段完整
- [ ] 文件命名符合 `作者-书名-年份.skillbook.json` 格式
- [ ] 放入正确的语言目录（`de/` `en/` `fr/` `zh/` `other/`）
- [ ] 已在本地验证导入不破坏现有图谱

## 禁止项 · Prohibitions

- ❌ 基于 AI 摘要/二手文献产生
- ❌ 伪造 quality_notes 或 rounds_completed
- ❌ 多本书合并为一个技能书（一书一谱）

---

*"一场真实的阅读。一次真实的折叠。其他都是噪音。"*
