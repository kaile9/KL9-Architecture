# KL9-RHIZOME v1.5 部署说明

## 部署时间
2026-05-03 03:05 UTC

## 架构变更摘要

| 维度 | v5.0 (旧) | KL9-RHIZOME v1.5 (新) |
|:---|:---|:---|
| 入口 | `scripts/run.py` / `scripts/main.py` | `scripts/koordinator.py` |
| 架构 | 7 步串行流水线 O1-O7 | TensionBus 事件驱动 + dual_fold 递归 |
| 调度 | 中心调度器（唯一入口） | 去中心化协调器（多入口并行） |
| 资源 | 4 级手工预算 | fold_depth 动态调节 (1-5) |
| 推理 | 显式策略选择 (CoT/Debate/Counterfactual) | 张力类型 → emergent_style 自然涌现 |
| 收束 | self_reflect + fallback_disclaimer | 递归悬置或 forced 标记 |
| 对外接口 | `run(query)` | `coordinate(query)` — 语义保留 |

## 新增文件

### 运行时核心 (`kailejiu-shared/lib/`)
| 文件 | 行数 | 说明 |
|:---|:---|:---|
| `tension_bus.py` | ~110 | 去中心化事件总线，单例模式 |
| `core_structures.py` | ~125 | DualState / Tension / Perspective / FoldWeight / DifficultySpectrum / SuspensionAssessment |
| `perspective_types.py` | ~100 | 6 大视角类别 + 6 种张力类型 + 7 组推荐二重组合 + FAMILY_SIGNALS |
| `emergent_style.py` | ~20 | 张力类型 → 涌现风格映射 |
| `fold_depth_policy.py` | ~55 | 动态折叠深度策略 + token 预估 |
| `suspension_evaluator.py` | ~115 | 悬置评估 + TEMPORAL 压力放宽 |
| `constitutional_dna.py` | ~90 | 宪政五原则 + 硬约束审查 |
| `dual_fold.py` | ~165 | 递归二重折叠引擎 |

### 入口 (`kailejiu-orchestrator/scripts/`)
| 文件 | 说明 |
|:---|:---|
| `koordinator.py` | KL9-RHIZOME v1.5 协调器入口，替代 run.py |

### 重建的 Backend (`kailejiu-shared/lib/`)
| 文件 | 说明 |
|:---|:---|
| `graph_backend.py` | 概念图谱后端（从数据库 schema 重建） |
| `memory.py` | 持久记忆后端（从数据库 schema 重建） |

## 归档文件
| 文件 | 归档路径 |
|:---|:---|
| `scripts/main.py` | `logs/archived_v5/main_v5_20260503_024409.py` |
| `scripts/run.py` | `logs/archived_v5/run_v5_20260503_024409.py` |

## 已知问题
- `graph_backend.cpython-312.pyc` 和 `memory.cpython-312.pyc` 在迁移过程中被 wrapper 覆盖，已从数据库 schema 重建为 `.py` 源文件
- `learner.py` 仍使用原始 `.pyc`（通过 importlib 加载），`reasoner.py` 未受影响

## 验证结果
- ✅ detect_dual_nature: 6/6 查询正确分类（4 academic + 2 casual）
- ✅ coordinate(): DualState 构建 → dual_fold → 悬置成功
- ✅ Casual Mode: 简短应答，无理论
- ✅ TensionBus: 事件发射/收集/清理正常
- ✅ System Status: graph(40 concepts, 95 edges) / memory(28 sessions, 702 books) / learner(easy)
- ✅ 旧文件已归档至 logs/archived_v5/

## 回滚步骤
```bash
cp /AstrBot/data/skills/kailejiu-orchestrator/logs/archived_v5/main_v5_*.py \
   /AstrBot/data/skills/kailejiu-orchestrator/scripts/main.py
cp /AstrBot/data/skills/kailejiu-orchestrator/logs/archived_v5/run_v5_*.py \
   /AstrBot/data/skills/kailejiu-orchestrator/scripts/run.py
rm /AstrBot/data/skills/kailejiu-orchestrator/scripts/koordinator.py
```
