# 9R-2.0 文件夹整理与版本标记报告

> 初始整理: 2026-05-06 19:37 CST  
> 二次自检: 2026-05-06 19:48 CST  
> 操作: 对比v1.5结构，整理文件夹，统一版本号标记，位置修正

---

## ⚠️ 重要说明：9R-2.0 不是 Skill

9R-2.0 是一个 **Python 框架/库**（含 `core/`, `skills/`, `tests/`, `docs/`，无 `SKILL.md`），
**不应**放在 `/AstrBot/data/skills/` 目录中。正确的存放位置是 `/AstrBot/data/workspaces/9R-2.0/`。

判断依据：
- 9R-2.0 没有 `SKILL.md` 文件（skill 的必要标志）
- 它是一个完整的 Python 框架，包含独立的核心层、技能层、测试层
- 它的使用方式是 `import`，而非通过 skill 系统调度

---

## 📁 结构对比

### v1.5 (KL9-RHIZOME) 原结构

```
skills/archive/9R-1.5/
├── kailejiu-shared/lib/          # 核心库 (13文件)
│   ├── __init__.py
│   ├── core_structures.py
│   ├── dual_fold.py
│   ├── emergent_style.py
│   ├── fold_depth_policy.py
│   ├── graph_backend.py
│   ├── learner.py
│   ├── memory.py
│   ├── perspective_types.py
│   ├── routing.py
│   ├── suspension_evaluator.py
│   └── tension_bus.py
├── kailejiu-orchestrator/        # 协调器
├── kailejiu-reasoner/            # 推理器
├── kailejiu-graph/               # 图谱
├── kailejiu-learner/             # 学习器
├── kailejiu-memory/              # 记忆
├── kailejiu-soul/                # 灵魂
├── kailejiu-research/            # 研究
└── kailejiu-core/                # 核心
```

**v1.5特点:**
- 分散式结构，每个技能独立目录
- 命名不统一（kailejiu前缀）
- 核心库与技能分离
- 无统一入口

### v2.0 (9R-2.0) 新结构 ✅

```
workspaces/9R-2.0/                 # 统一主目录（框架，非skill）
├── __init__.py                    # 统一入口 N9R20Framework
├── requirements.txt               # 零运行时依赖
├── core/                          # 核心层
│   ├── __init__.py
│   ├── n9r20_structures.py        # 数据结构
│   ├── n9r20_tension_bus.py       # 事件总线
│   └── n9r20_llm_evaluator.py     # LLM评估接口 (N9R20LLMFoldEvaluator)
├── skills/                        # 技能层
│   ├── __init__.py
│   ├── n9r20_adaptive_router.py
│   ├── n9r20_compression_core.py
│   ├── n9r20_dual_reasoner.py
│   ├── n9r20_semantic_graph.py
│   └── n9r20_memory_learner.py
├── tests/                         # 测试层
│   ├── __init__.py
│   ├── n9r20_test_router.py       # 43 tests
│   ├── n9r20_test_tension_bus.py  # 34 tests
│   └── n9r20_test_compression.py  # 60 tests
└── docs/                          # 文档
    ├── README.md
    ├── FRAMEWORK.md
    ├── DEPLOY.md
    ├── TEST_REPORT.md
    └── STRUCTURE_REFACTOR_REPORT.md  ← 本文件
```

**v2.0特点:**
- 统一目录 `9R-2.0/`
- 统一前缀 `n9r20_` (文件) / `N9R20` (类)
- 统一入口 `N9R20Framework`
- 核心+技能+测试分层清晰
- 零外部依赖
- **存放在 workspaces/ 而非 skills/**（非skill框架）

---

## 🏷️ 标记统一化

| 层级 | v1.5标记 | v2.0标记 |
|------|---------|---------|
| 目录名 | `kailejiu-*`, `kl9_*` | `9R-2.0/` |
| 文件名 | 无统一前缀 | `n9r20_*.py` |
| 类名 | `DualState`, `TensionBus`... | `N9R20DualState`, `N9R20TensionBus`... |
| 全局变量 | `bus`, `router`... | `n9r20_bus`, `n9r20_router`... |
| 版本号 | `v1.5` | `9R-2.0` |
| 品牌名 | `KL9-RHIZOME` | `9R-2.0 RHIZOME` |

---

## 📦 归档处理

### v1.5 归档
```
skills/archive/9R-1.5/
├── kailejiu-baiyueguang-perspective.archived
├── kailejiu-core
├── kailejiu-graph
├── kailejiu-learner
├── kailejiu-memory
├── kailejiu-orchestrator
├── kailejiu-reasoner
├── kailejiu-research
├── kailejiu-shared
└── kailejiu-soul
```

### Legacy 归档
```
skills/archive/legacy/
├── kl9-v2.0/          # 原始v2.0副本
├── kl9_core/          # 旧核心位置
├── kl9_engines/       # 旧引擎
└── kl9_skills/     # 旧技能书
```

---

## ✅ 自检结果 (2026-05-06 19:48)

### 导入验证 (11/11 通过)

```
✓ __init__.py 导入成功 (N9R20Framework, compress)
✓ core.n9r20_structures 导入成功
✓ core.n9r20_tension_bus 导入成功
✓ core.n9r20_llm_evaluator 导入成功 (N9R20LLMFoldEvaluator)
✓ skills.n9r20_adaptive_router 导入成功
✓ skills.n9r20_compression_core 导入成功
✓ skills.n9r20_dual_reasoner 导入成功
✓ skills.n9r20_semantic_graph 导入成功
✓ skills.n9r20_memory_learner 导入成功
✓ N9R20Framework 实例化成功
✓ process() + compress() 调用成功
```

### 单元测试 (137/137 通过)

```
pytest tests/ --override-ini="testpaths=tests" --override-ini="python_files=n9r20_test_*.py"
─────────────────────────────────────────
n9r20_test_compression.py  → 60 passed
n9r20_test_router.py       → 43 passed
n9r20_test_tension_bus.py  → 34 passed
─────────────────────────────────────────
总计: 137/137 passed (1.24s)
```

### 结构完整性检查

```
9R-2.0/
  __init__.py              ✓
  requirements.txt          ✓
  core/                     ✓ (3 files)
  skills/                   ✓ (5 files)
  tests/                    ✓ (3 files)
  docs/                     ✓ (5 files)
  __pycache__/              ✗ 已清理
```

---

## 🚀 快速使用

```python
import sys
sys.path.insert(0, '/AstrBot/data/workspaces/9R-2.0')

from __init__ import N9R20Framework, compress

# 方式1: 框架实例
agent = N9R20Framework()
result = agent.process("何为空性？")
print(result.output)

# 方式2: 便捷函数
compressed = compress("你的查询")
```

---

## 📊 最终结构概览

```
/AstrBot/data/
├── workspaces/
│   └── 9R-2.0/                ← 当前主版本 (v2.0) · 框架，非skill
│       ├── core/              ← 核心基础设施
│       ├── skills/            ← 5大技能模块
│       ├── tests/             ← 137个测试
│       └── docs/              ← 文档
│
└── skills/
    └── archive/
        ├── 9R-1.5/            ← v1.5归档
        └── legacy/            ← 旧版本备份
```

---

*整理完成: 2026-05-06 19:39 CST*  
*自检通过: 2026-05-06 19:49 CST*  
*状态: ✅ 全部完成，137/137 测试通过，位置已修正*
