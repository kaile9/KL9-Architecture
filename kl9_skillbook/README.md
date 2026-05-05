# kl9_skillbook — 技能书吸收协议 · 9R-1.5 (Skill Book Absorption Protocol)

KL9-RHIZOME 9R-1.5 实例学习成果的导入/导出/评分引擎。碰撞分叉、张力局部重算、三源动态评分。

**版本**：9R-1.5 (semver: 1.5.0)  
**命名**：9=开了玖, R=RHIZOME, 1.5=大版本.小版本

## 模块 · Modules（8）

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

## 导入流水线 · Import Pipeline

```
加载 JSON → 校验 manifest → 加载本地图谱 → 沙盒命名空间
→ 碰撞检测 → 合并 (近似/分叉/新增) → 2-hop 张力重算
→ 全局 stale 标记 → 持久化
```

## 评分引擎 · Scoring Engine

| 组件 | 公式 |
|------|------|
| 模型 ceiling | `HLE×0.5 + Arena_norm×0.25 + CW_norm×0.25 → ×1.15+15` |
| 语言补偿 | zh族+中文书 +3%, en族+英文书 +3%（不超ceiling） |
| 信任 | `trust = quality_adjusted × (1 − difficulty/200)` |
| 吸收策略 | ≥90 full / 60-90 supplementary / 30-60 selective / <30 reject |

## 使用 · Usage

### 参考技能书（SKILL.md）
`kailejiu-research` 通过 `dialogical_activation` 直接征用 `skillbooks/` 中的 SKILL.md。

### 可导入技能书（.skillbook.json）
```python
from kl9_skillbook.bridge import import_skillbook_to_graph

result = import_skillbook_to_graph("skillbooks/de/Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json")
# → {success, trust, trust_level, nodes_added, ...}
```

> 当前藏书均为 SKILL.md 格式。`.skillbook.json` 用于概念级图谱导入。

详见 [skillbooks/README.md](../skillbooks/README.md)。
