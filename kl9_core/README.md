# kl9_core — 核心运行时 · Core Runtime

KL9-RHIZOME 的认知引擎，包含二重折叠、张力总线、概念图谱后端和风格涌现。

*Cognitive engine of KL9-RHIZOME: dual-fold, tension bus, concept graph backend, and emergent style.*

| 模块 | 职责 |
|------|------|
| `constitutional_dna.py` | 五原则宪法：A/B平等、反调和、显式张力、渐进深度、可逆折叠 |
| `dual_fold.py` | 二重折叠原语：在 A/B 视角间递归折叠直到悬置 |
| `tension_bus.py` | 去中心化张力总线：6种张力类型的发布/订阅 |
| `graph_backend.py` | SQLite 概念图谱：存储、BM25检索、张力共振排序、谱系边 |
| `memory.py` | 持久记忆：会话记录、反馈、张力上下文检索 |
| `core_structures.py` | 核心数据结构：DualState、Tension、FoldWeight |
| `suspension_evaluator.py` | 悬置质量评估：genuine / forced / insufficient |
| `emergent_style.py` | 风格涌现：从张力配置生成认知风格轮廓 |
| `fold_depth_policy.py` | 折叠深度策略：根据难度谱动态调节 max_fold_depth |
| `learner.py` | 二重学习器：张力悬置评估驱动的迭代学习 |
| `perspective_types.py` | 视角类型注册表 |
| `routing.py` | 路由：查询→张力场→技能匹配 |
