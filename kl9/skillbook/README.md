# kl9/skillbook — 技能书加载器

> 去中心化知识传播 · 惰性加载 · 格式桥接

---

## 职责

`kl9/skillbook/loader.py` 是技能书系统的**唯一入口**。

```
skillbooks/ (文件)
    └── SkillbookLoader (内存统一模型)
            └── SkillBook dataclass
                    └── SemanticGraph.ingest()
```

**核心原则**: 惰性、单向、不回写。

---

## 支持的格式

| 格式 | 文件结构 | 状态 |
|---|---|---|
| v1.x SKILL.md | 单文件 Markdown + YAML frontmatter | 兼容 |
| v3.1 6-file | `meta.yaml` + `lens.json` + 4 个 YAML | 兼容 |

两种格式会被统一转换为内存 `SkillBook` dataclass，上层代码无感知差异。

---

## API 参考

### 加载技能书

```python
from kl9.skillbook.loader import SkillbookLoader

# 加载 v1.x 格式
book = SkillbookLoader.load_v1("skillbooks/zh/xxx/SKILL.md")

# 加载 v3.1 格式
book = SkillbookLoader.load_v31("skillbooks/zh/xxx/")
```

### SkillBook 数据结构

```python
@dataclass
class SkillBook:
    name: str
    domain: list[str]
    school: str
    period: str
    language: str
    description: str
    concepts: list[SkillBookConcept]
    tensions: list[SkillBookTension]
    quotes: list[dict]
    references: list[dict]
    tags: list[str]
```

---

## 格式桥接细节

### v1.x → 内存模型

```python
loader = SkillbookLoader()
book = loader.load_v1(skill_md_path)
# 自动解析 YAML frontmatter + ## sections
```

### v3.1 → 内存模型

```python
book = loader.load_v31(six_file_dir)
# 自动解析 meta.yaml + lens.json + hooks.yaml + tensions.yaml + quotes.yaml + references.yaml
```

---

## 故障排查

| 症状 | 原因 | 解决 |
|---|---|---|
| 返回 None | 格式不匹配 | 检查是否存在 `SKILL.md` 或 6-file 结构 |
| YAML 解析失败 | frontmatter 语法错误 | 用 yaml linter 检查 |
| 概念为空 | sections 未按规范命名 | 检查是否使用 `## Concepts` |

---

## 与核心引擎的关系

```
kl9/skillbook/     ← 本层：知识加载 + 格式桥接
        ↓
kl9/core/graph.py  ← 注入语义图谱 + 词频统计
        ↓
kl9/core/fold.py   ← 折叠时调用概念/张力
```

---

*"知识不是储备，是弹药。技能书加载器是装填机构。"*
