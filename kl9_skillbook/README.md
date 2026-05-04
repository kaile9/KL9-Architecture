# kl9_skillbook — 技能书吸收协议 v1.0

将 KL9 实例的学习成果导出为标准技能书，支持跨实例导入。碰撞分叉、张力局部重算、双轨信任。

| 模块 | 职责 |
|------|------|
| `models.py` | 数据模型：ConceptNode、SkillBookManifest、CollisionReport |
| `validator.py` | Manifest 校验：版本/质量等级/LLM来源 |
| `matcher.py` | 概念匹配：精确+Levenshtein模糊，三档分类 |
| `merger.py` | 核心合并：近似合并定义、精确碰撞分叉、无冲突新增 |
| `tension.py` | 2-hop子图张力重算 |
| `importer.py` | 9步导入流水线（JSON后端） |
| `bridge.py` | SQLite ↔ JSON 双向桥接 |

### 快速使用

```python
from kl9_skillbook.bridge import import_skillbook_to_graph
result = import_skillbook_to_graph("skillbooks/de/Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json")
```
