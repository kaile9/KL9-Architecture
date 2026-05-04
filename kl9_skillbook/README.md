# kl9_skillbook — 技能书吸收协议 v1.1 (Skillbook Absorption Protocol)

将 KL9 实例的学习成果导出为标准技能书，支持跨实例导入。碰撞分叉、张力局部重算、双轨信任。

*Export KL9 learning outcomes as standardized skillbooks with cross-instance import. Collision bifurcation, local tension recalculation, dual-track trust.*

## 评分体系 · Scoring System

双维度评分 + 语言补偿:
- **难度分 (Difficulty)**: 0-100, LLM评估4项标准（风格/信息/创新/引用密度）
- **质量分 (Quality)**: 0-100, 基于制作记录的客观算法（轮数+验证+反视角）
- **语言补偿 (Language Bias)**: ±3% based on LLM model family and book language match
- **信任公式 (Trust)**: `trust = quality × (1 − difficulty/200)`, with language bias applied to quality

*Dual-dimension scoring + language bias: difficulty (LLM-evaluated 4-dim), quality (production-record based), ±3% language bias, trust formula with bias applied.*

| 模块 | 职责 |
|------|------|
| `models.py` | 数据模型：ConceptNode、SkillBookManifest、CollisionReport |
| `validator.py` | Manifest 校验：版本/质量等级/LLM来源/语言 |
| `matcher.py` | 概念匹配：精确+Levenshtein模糊，三档分类 |
| `merger.py` | 核心合并：近似合并定义、精确碰撞分叉、无冲突新增 |
| `tension.py` | 2-hop子图张力重算 |
| `scorer.py` | 评分引擎：难度/质量/语言偏差/信任计算 |
| `importer.py` | 9步导入流水线（JSON后端） |
| `bridge.py` | SQLite ↔ JSON 双向桥接 |

### 快速使用

```python
from kl9_skillbook.bridge import import_skillbook_to_graph
result = import_skillbook_to_graph("skillbooks/de/Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json")
```
