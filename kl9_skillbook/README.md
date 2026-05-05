# kl9_skillbook — 技能书吸收协议 v1.2 (Skill Book Absorption Protocol)

KL9 实例学习成果的导入/导出/评分引擎。碰撞分叉、张力局部重算、三源动态评分。

## 模块 · Modules

| 模块 | 职责 |
|------|------|
| `models.py` | ConceptNode, SkillBookManifest, ProductionRecord, DifficultyBreakdown |
| `validator.py` | Manifest 校验 (FATAL/WARNING) + v1.0/v1.1 向后兼容 |
| `matcher.py` | Levenshtein 相似度 + 三档碰撞分类 (exact ≥95% / nearby 70-95%) |
| `merger.py` | 核心合并：近似合并定义、碰撞分叉影子节点、无冲突新增 |
| `tension.py` | 2-hop 子图张力局部重算 |
| `scorer.py` | HLE+Arena 三源聚合 + 语言偏差 ±3% + 信任公式 |
| `importer.py` | 9步导入流水线 (JSON 后端) |
| `bridge.py` | SQLite ↔ JSON 双向桥接 |

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

```python
from kl9_skillbook.bridge import export_graph_to_skillbook, import_skillbook_to_graph

# 导出
export_graph_to_skillbook("书名", "deepseek-v4-pro", rounds=2, verify="spot-check")

# 导入
result = import_skillbook_to_graph("skillbooks/de/Brodbeck-xxx-2023/SKILL.md")
# → {success, trust, trust_level, nodes_added, ...}
```

详见 [skillbooks/README.md](../skillbooks/README.md) 和 [SKILLBOOK_STANDARD.md](../skillbooks/SKILLBOOK_STANDARD.md)。
