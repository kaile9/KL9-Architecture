# core/

9R-2.0 核心认知引擎。

- `structures.py` — DualState、Tension、Perspective 数据结构
- `dual_reasoner.py` — 双视角推理引擎
- `compression_core.py` — 四模式压缩引擎（construct/deconstruct/validate/interrupt）
- `tension_bus.py` — 去中心化事件总线
- `adaptive_router.py` — 自适应路由（关键词检测 → fold 深度分配）
- `llm_compressor.py` — LLM 压缩器接口
- `llm_evaluator.py` — LLM 评估器接口
- `semantic_graph.py` — 语义知识图谱
- `memory_learner.py` — 记忆学习器
- `config.py` — 全局配置

详见根目录 README 架构章节。
