# kl9_core — 核心运行时 · Core Runtime

KL9-RHIZOME 的认知引擎，包含二重折叠、张力总线、概念图谱后端和风格涌现。

*Cognitive engine of KL9-RHIZOME: dual-fold, tension bus, concept graph backend, and emergent style.*

| 模块 | 职责 |
|------|------|
| `constitutional_dna.py` | 五原则宪法：A/B平等、反调和、显式张力、渐进深度、可逆折叠 |
| `kl9_core/dual_fold.py` | 二重折叠原语：在 A/B 视角间递归折叠直到悬置 |
| `kl9_core/tension_bus.py` | 去中心化张力总线：6种张力类型的发布/订阅 |
| `kl9_core/graph_backend.py` | SQLite 概念图谱：存储、BM25检索、张力共振排序、谱系边 |
| `kl9_core/memory.py` | 持久记忆：会话记录、反馈、张力上下文检索 |
| `kl9_core/core_structures.py` | 核心数据结构：DualState、Tension、FoldWeight |
| `kl9_core/suspension_evaluator.py` | 悬置质量评估：genuine / forced / insufficient |
| `kl9_core/emergent_style.py` | 风格涌现：从张力配置生成认知风格轮廓 |
| `kl9_core/fold_depth_policy.py` | 折叠深度策略：根据难度谱动态调节 max_fold_depth |
| `kl9_core/learner.py` | 二重学习器：张力悬置评估驱动的迭代学习 |
| `kl9_core/perspective_types.py` | 视角类型注册表 |
| `kl9_core/routing.py` | 路由：查询→张力场→技能匹配 |

## 技能书接入 · Skillbook Integration

导入技能书时，kl9_core 参与以下流程：

| 模块 | 导入时的行为 |
|------|-------------|
| `kl9_core/graph_backend.py` | bridge.py 通过 store_concept() + create_edge() 将导入概念写入 SQLite；新增概念自动参与 BM25 检索和张力共振排序 |
| `kl9_core/memory.py` | 导入操作记录为 session；通过 retrieve_by_tension_context() 可查到导入历史 |
| `kl9_core/tension_bus.py` | 导入完成后发射 SkillbookImportEvent，订阅者可响应（如 learner 触发重评估） |
| `kl9_core/core_structures.py` | 导入的 DualState 数据直接映射到 Perspective + Tension 结构 |
