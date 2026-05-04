# kl9_skillbook — 技能书吸收协议 v1.2

将 KL9 实例的学习成果导出为标准技能书 JSON，支持跨实例导入。碰撞分叉、张力局部重算、三源动态评分。

## 模块

| 模块 | 职责 |
|------|------|
| `models.py` | ConceptNode, SkillBookManifest, ProductionRecord, DifficultyBreakdown |
| `validator.py` | Manifest 校验 (FATAL/WARNING) + v1.1 向后兼容 |
| `matcher.py` | 概念匹配：精确 Levenshtein + 三档分类 (exact/near/nearby) |
| `merger.py` | 核心合并：近似合并定义、碰撞分叉影子节点、无冲突新增 |
| `tension.py` | 2-hop 子图张力局部重算 |
| `scorer.py` | 三源聚合评分 + 语言偏差补偿 + 信任公式 |
| `importer.py` | 9步导入流水线 (JSON 后端) |
| `bridge.py` | SQLite ↔ JSON 双向桥接 |

## 导入后发生什么

```
导入技能书 → 9步流水线:
  1. 加载 JSON    2. 校验 manifest    3. 加载本地图谱
  4. 沙盒命名空间    5. 碰撞检测 (精确/模糊)
  6. 合并 (近似合并 / 碰撞分叉 / 新增)
  7. 2-hop 张力重算    8. 全局 stale 标记    9. 持久化

导入后:
  - 同名不同义概念 → 创建 __shadow_ 影子节点，双版本共存
  - 近似概念 (sim≥0.95) → 合并定义，标注来源
  - 模糊匹配 (0.7-0.95) → 仅报告，不自动连边
  - 受影响 2-hop 邻域内的 tension_score 重算
```

## 评分体系 v1.2

### 动态模型评分 (三源聚合)

```
arena_norm = min(100, (arena_elo - 1200) / 3.0)
cw_norm = min(100, (cw_elo - 1200) / 3.0)
combined = HLE × 0.50 + Arena_norm × 0.25 + CW_norm × 0.25
ceiling = min(100, combined × 0.9 + 15)
```

数据来源: llm-stats.com, openlm.ai, benchlm.ai

### 语言补偿

| LLM族 | 中文书 | 英文书 | 其他语言 |
|--------|:--:|:--:|:--:|
| zh (DeepSeek/Qwen/Kimi) | +3% | 0% | −3% |
| en (GPT/Claude/Gemini) | −3% | +3% | 0% |

补偿后质量分不能超过模型 ceiling。

### 信任公式

```
trust = quality_adjusted × (1 − difficulty/200)
```

信任阈值: ≥90 full / 60-90 supplementary / 30-60 selective / <30 reject

## 快速使用

```python
from kl9_skillbook.bridge import import_skillbook_to_graph
result = import_skillbook_to_graph("skillbooks/de/Brodbeck-xxx-2023.skillbook.json")
# → {success, nodes_added, trust, trust_level, ...}
```
