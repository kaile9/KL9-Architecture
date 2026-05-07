# 9R-1.5 → 9R-2.0 架构迁移指南

> 面向现有 9R-1.5 用户，说明如何迁移到 9R-2.0。

---

## 一、为什么要升级

9R-1.5 的核心是"张力悬置"（Suspension）——矛盾不下结论，无限悬停。这在哲学分析中有效，但有两个问题：

1. **不输出结论**：用户问完问题，系统只呈现张力，不给出洞察
2. **LLM token 消耗大**：每次递归折叠都要调用 LLM，成本高

9R-2.0 的核心是"压缩涌现"（Compression Emergence）：
- 四模式折叠引擎（construct → deconstruct → validate → interrupt）从对立中压缩出洞察
- LLM 只做评估（evaluate），压缩本身用规则引擎完成
- 输出有结论，但不是廉价综合，而是经过验证的压缩结果

---

## 二、核心变化速览

| 维度 | 9R-1.5 | 9R-2.0 |
|------|--------|--------|
| **核心理念** | 张力悬置（无限悬停） | 压缩涌现（四模式折叠出洞察） |
| **压缩方式** | 递归 fold，每次调 LLM | 规则引擎 + LLM 评估 |
| **输出** | 呈现张力，不下结论 | 压缩洞察，附带验证状态 |
| **目录结构** | 分散式（kailejiu-*/） | 统一式（core/ + skillbook/） |
| **命名** | kl9_* / kailejiu-* | n9r20_* / N9R20* |
| **入口** | 无统一入口 | `quickstart.py` / `from core import *` |

---

## 三、目录结构迁移

### 旧结构（9R-1.5）

```
kl9_core/              ← 核心代码
├── core_structures.py
├── dual_fold.py
├── routing.py
├── suspension_evaluator.py
├── tension_bus.py
├── learner.py
├── memory.py
├── graph_backend.py
├── perspective_types.py
└── fold_depth_policy.py

kl9_skillbook/         ← 技能书系统
├── importer.py
├── matcher.py
├── merger.py
├── models.py
├── scorer.py
├── validator.py
├── bridge.py
└── tension.py

skillbooks/            ← 技能书内容
├── zh/
├── en/
├── de/
├── fr/
└── other/
```

### 新结构（9R-2.0）

```
core/                  ← 运行时引擎（Python 源码）
├── n9r20_structures.py
├── n9r20_compression_core.py      ← dual_fold.py 的替代
├── n9r20_adaptive_router.py       ← routing.py 的替代
├── n9r20_tension_bus.py
├── n9r20_dual_reasoner.py
├── n9r20_memory_learner.py        ← learner.py + memory.py
├── n9r20_semantic_graph.py        ← graph_backend.py
├── n9r20_llm_evaluator.py         ← 新增：LLM 评估
├── n9r20_llm_compressor.py        ← 新增：语义压缩
├── n9r20_skillbook_compat.py    ← 新增：v1.x 兼容层
└── ...

skillbook/             ← 技能书内容仓库（Markdown）
├── __init__.py        ← 内容加载器
├── prebuilt/
│   ├── zh/
│   ├── en/
│   ├── de/
│   ├── fr/
│   └── other/

quickstart.py          ← 统一入口：交互式 Agent REPL
```

### 迁移操作

```bash
# 1. 备份旧版本
cp -r kl9_core archive/9R-1.5/
cp -r kl9_skillbook archive/9R-1.5/

# 2. 下载 9R-2.0
git clone https://github.com/kaile9/KL9-Architecture.git
cd KL9-Architecture

# 3. 你的技能书还在——skillbook/ 目录结构与 v1.x 兼容
#    prebuilt/zh/、en/ 等目录可以直接复用
```

---

## 四、代码迁移对照

### 4.1 数据结构

**旧版（9R-1.5）**
```python
from core_structures import DualState, Tension, Perspective

state = DualState(
    query="佛教心性论",
    perspective_A=Perspective(name="真如门", characteristics=["不生不灭"]),
    perspective_B=Perspective(name="生灭门", characteristics=["缘起生灭"]),
)

tension = Tension(
    perspective_A="真如门",
    perspective_B="生灭门",
    claim_A="心性本净",
    claim_B="心性随缘",
)
```

**新版（9R-2.0）**
```python
from core import N9R20DualState, N9R20Tension, N9R20Perspective

state = N9R20DualState(
    query="佛教心性论",
    perspective_A=N9R20Perspective(name="真如门", characteristics=["不生不灭"]),
    perspective_B=N9R20Perspective(name="生灭门", characteristics=["缘起生灭"]),
    # 新增字段自动生效
    target_fold_depth=4,
    target_compression_ratio=2.5,
)

tension = N9R20Tension(
    perspective_A="真如门",
    perspective_B="生灭门",
    claim_A="心性本净",
    claim_B="心性随缘",
    # 新增字段
    dual_state=state,
    max_fold_depth=4,
    fold_count=0,
)
```

**变化点：**
- 类名加前缀：`DualState` → `N9R20DualState`
- `N9R20Tension` 新增 `dual_state`、`max_fold_depth`、`fold_count`、`tension_points`
- 旧字段（`perspective_A`、`claim_A`、`irreconcilable_points` 等）保持不变

---

### 4.2 路由决策

**旧版（9R-1.5）**
```python
from routing import QueryDepth, DepthAssessment

assessment = DepthAssessment(
    depth=QueryDepth.DEEP,
    max_fold_depth=7,
    full_pipeline=True,
    activated_skills=["kailejiu-research", "kailejiu-reasoner"],
)
```

**新版（9R-2.0）**
```python
from core import N9R20AdaptiveRouter, N9R20RoutingDecision

router = N9R20AdaptiveRouter()
decision = router.detect("佛教心性论")
# decision.path == "deep"
# decision.target_fold_depth == 9
# decision.academic_markers == ["佛教"]
```

**变化点：**
- 从手动构建 `DepthAssessment` 变成 `router.detect()` 自动检测
- 返回 `N9R20RoutingDecision` 对象，字段为 `path`（不是 `depth`）
- 学术标记列表在 `academic_markers` 中

---

### 4.3 压缩流程（最大变化）

**旧版（9R-1.5）——每次 fold 都调 LLM**
```python
from dual_fold import structural_tension

# 构建张力
tension = structural_tension(perspective_A, perspective_B, claim_A, claim_B, "本体论")

# 递归折叠——每次都要调 LLM
# fold 1: A 视角
# fold 2: B 视角
# fold 3: 检查悬置
# ... 每一层都消耗 token
```

**新版（9R-2.0）——LLM 只做评估，压缩用规则**
```python
from core import N9R20CompressionCore, N9R20LLMFoldEvaluator

# 1. LLM 评估查询复杂度
evaluator = N9R20LLMFoldEvaluator(llm_client=your_llm)
evaluation = evaluator.evaluate("佛教心性论")
# evaluation.fold_depth == 7
# evaluation.compression_target == 2.5

# 2. 规则引擎执行四模式压缩
compressor = N9R20CompressionCore()
result = compressor.compress(tension, route="deep")
# result.content 包含 construct + deconstruct + validate + interrupt 四段
# result.constitutional_check == True/False
# result.fold_depth_used == 7
```

**核心变化：**
- 9R-1.5：压缩 = 递归 fold，每次调 LLM，token 消耗随深度线性增长
- 9R-2.0：压缩 = LLM 评估一次（定深度）→ 规则引擎四模式折叠（零 LLM token）

---

### 4.4 事件总线

**旧版（9R-1.5）**
```python
from tension_bus import TensionBus

bus = TensionBus()
bus.emit("query_received", {"query": "..."})
```

**新版（9R-2.0）**
```python
from core import n9r20_bus, N9R20QueryEvent

n9r20_bus.emit(N9R20QueryEvent(query="...", session_id="..."))
```

---

### 4.5 内存/学习器

**旧版（9R-1.5）**
```python
from learner import Learner
from memory import MemoryStore

learner = Learner()
store = MemoryStore(db_path="data/kl9.db")
```

**新版（9R-2.0）**
```python
from core import N9R20MemoryLearner

memory = N9R20MemoryLearner(db_path="data/n9r20.db")
# 合并了 Learner + MemoryStore 的功能
```

---

## 五、Breaking Changes

| 变更 | 影响 | 迁移操作 |
|------|------|---------|
| 类名加 `N9R20` 前缀 | 所有 import 语句 | `DualState` → `N9R20DualState` |
| `skillbook/*.py` 移除 | 如果 import 了 `skillbook/n9r20_*` | 改为 `from core import ...` |
| `FoldDepth` 从 `routing.py` 移到 `structures.py` | import 路径 | `from routing import FoldDepth` → `from core import FoldDepth` |
| `Tension` 字段新增 | 直接构建 `Tension` 的代码 | 添加 `dual_state`、`max_fold_depth`、`fold_count` 等字段 |
| `RoutingDecision` 字段名 | 使用旧字段名 | `route_type` → `path`，`fold_depth_budget` → `target_fold_depth` |
| 压缩流程 | 压缩逻辑 | 从递归 fold 改为 `CompressionCore.compress()` |

---

## 六、兼容层

9R-2.0 内置兼容层 `core/n9r20_skillbook_compat.py`：

```python
from core.n9r20_skillbook_compat import N9R20SkillBookImporter, N9R20SkillBookManifest

# 导入旧版 skillbook 格式
importer = N9R20SkillBookImporter()
manifest = importer.import_from_file("skillbook/prebuilt/zh/Asvaghosa-Dasheng-Qixin-Lun-554/SKILL.md")

# 转换为新版格式
book = manifest.sync_to_skill_book()  # → N9R20SkillBook
```

兼容层功能：
- 读取 v1.x 的 SKILL.md 格式
- 自动转换为 v2.0 的 `N9R20SkillBook` / `N9R20ConceptNode`
- 冲突检测（同名概念不同定义）
- 上下文变体支持（v2.0 新增）

---

## 七、FAQ

**Q: 我的 v1.x 技能书还能用吗？**
A: 能。`skillbook/prebuilt/` 的目录结构和 SKILL.md 格式保持不变，兼容层自动处理。

**Q: 需要改哪些代码？**
A: 主要是 import 路径和类名。压缩逻辑从递归 fold 改为 `CompressionCore.compress()`，但数据结构兼容。

**Q: quickstart.py 是什么？**
A: 9R-2.0 的统一入口。`python quickstart.py` 启动交互式 Agent，支持 `status`、`help`、`quit` 等命令。

**Q: 还走 AstrBot 吗？**
A: 可以。`quickstart.py` 内置环境检测（AstrBot/OpenClaw/Standalone），自动适配路径。

**Q: token 消耗有变化吗？**
A: 有。9R-2.0 LLM 只做一次评估（evaluate），压缩用规则引擎。token 消耗从 O(n) 降到 O(1)。

---

## 八、快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/kaile9/KL9-Architecture.git
cd KL9-Architecture

# 2. 启动 Agent
python quickstart.py

# 3. 交互模式
KL9> 佛教心性论是什么结构？
# Agent 走完整 9R-2.0 流程输出洞察

KL9> status
# 查看会话状态和子系统健康

KL9> quit
```

---

*迁移遇到问题，开 Issue 或参考 `docs/DIRECTORY_HIERARCHY_GUIDE.md`。*
