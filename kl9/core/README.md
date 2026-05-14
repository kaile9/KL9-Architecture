# kl9/core — 认知协议引擎

> 9R-2.1 核心运行时 · 递归折叠认知协议层

---

## 模块一览

| 文件 | 职责 | 对应架构层 |
|---|---|---|
| `router.py` | LLM-only 路由 · 复杂度分级 | Router |
| `decomposer.py` | A/B 双视角拆解 | Decomposer |
| `fold.py` | 递归折叠引擎 | Fold Engine |
| `gate.py` | 规则引擎中间审查 | Gate |
| `validator.py` | LLM-as-Judge 五维评分 | Validator |
| `aggregator.py` | 张力保持输出组装 | Aggregator |
| `dna.py` | 宪法 DNA · 九条原则 | Constitutional DNA |
| `graph.py` | 语义知识图谱 | Semantic Graph |

---

## 数据流向

```
Query → Router → Decomposer → Fold 0→N → Gate → Validator → Aggregator → Output
         ↑           ↑            ↑        ↑         ↑
    LLM-as-Router  LLM拆A/B   递归折叠  [TENSION:]  LLM-as-Judge
    (~250 tokens)  视角初始化  深度优先  [UMKEHR:]   5维评分 A/B/C/D
                             增量停止
```

---

## 各模块详解

### router.py — LLM-only 路由

**设计目标**: 单次轻量 LLM 调用，判断查询复杂度。

**三级路由**:

| 级别 | 触发条件 | fold 深度 | 成本 |
|---|---|---|---|
| **QUICK** | 问候/简单事实查询 | 0 | ~$0 |
| **STANDARD** | 一般分析/总结 | 1-2 层 | ~$0.001 |
| **DEEP** | 学术分析/哲学辩证 | 3-9 层 | ~$0.003-0.01 |

**技术细节**:
- 提示词完全可缓存（~250 tokens）
- 缓存命中延迟 ~200ms
- 成本 <$0.0005/次

### decomposer.py — 双视角拆解

将用户查询拆为两个**不可调和的理论视角** A/B，标注初始张力。

**输出结构**:
```python
class Perspective:
    name: str
    content: str
    theorists_cited: list[str]
    tension_points: list[str]
```

### fold.py — 递归折叠引擎

**核心算法**: 深度优先，增量停止。

```
每步循环:
  1. A 视角深化 → 生成新论证
  2. B 视角深化 → 生成反驳
  3. 碰撞检测 → 提取新[硬张力]
  4. 增量检查 → 新产出 == 0 ? 停止 : 继续
  5. 预算检查 → 到达上限 ? 停止 : 继续
```

**停止条件**（满足任一）:
- 增量为零（新 fold 未产生新张力点）
- 到达 fold 深度预算上限
- 用户手动中断

### gate.py — 规则引擎审查

纯正则，零成本。

**审查维度**:
- **禁止模式检测**: 鸡汤、AI套话、"你应当"
- **概括率检查**: 引用 vs 概括比例 ≤ 5%
- **结尾形态验证**: 句号结尾 → 省略号

### validator.py — LLM-as-Judge 五维评分

| 维度 | 说明 | 权重 |
|---|---|---|
| 理论框架 | 是否有明确坐标 | 0.25 |
| 引用标准 | 引用密度与准确性 | 0.25 |
| 论证深度 | 是否触及结构性矛盾 | 0.20 |
| 文体质量 | 是否符合宪法 DNA | 0.15 |
| 原创性 | 是否产生新洞察 | 0.15 |

**评分等级**: A(≥0.85) / B(≥0.70) / C(≥0.55) / D(<0.55)

---

## 与其他层的关系

```
kl9/core/          ← 本层：认知协议引擎
kl9/llm/           ← 下游：LLM API 调用（被 core 各模块注入使用）
kl9/skillbook/     ← 上游：技能书内容注入（影响分解/折叠）
kl9/utils/         ← 工具：事件总线 + 异常 + 迁移辅助
```

---

*认知协议层的职责不是"回答问题"，而是"展开张力后从对立中压缩出洞察。"*
