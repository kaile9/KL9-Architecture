# core/

9R-2.0 运行时引擎 — Python 源码目录。

| 文件 | 功能 |
|------|------|
| `n9r20_structures.py` | 数据结构：DualState、Tension、Perspective、RoutingDecision、CompressedOutput、FoldDepth |
| `n9r20_compression_core.py` | 四模式压缩引擎（construct → deconstruct → validate → interrupt） |
| `n9r20_dual_reasoner.py` | 双视角推理引擎：生成 A/B 视角 + 张力点 |
| `n9r20_tension_bus.py` | 去中心化事件总线：QueryEvent、CompressionCompleteEvent 等 |
| `n9r20_adaptive_router.py` | 自适应路由：学术关键词检测 → fold 深度分配 |
| `n9r20_llm_evaluator.py` | LLM 评估器：查询复杂度评估，动态 fold 深度 |
| `n9r20_llm_compressor.py` | LLM 压缩器：语义精修（依赖注入复用框架 LLM client） |
| `n9r20_semantic_graph.py` | 语义知识图谱：概念节点 + 上下文变体 + 赫布学习 |
| `n9r20_memory_learner.py` | 记忆学习器：SQLite 会话存储 |
| `n9r20_skillbook_compat.py` | v1.x 技能书兼容层：导入 + 冲突检测 + 迁移 |
| `n9r20_config.py` | 全局配置 |
| `n9r20_user_config.py` | 用户自定义配置 |
| `n9r20_utils.py` | 工具函数 |
| `n9r20_production_logger.py` | 生产日志 |
| `version.py` | 版本信息 |

详见根目录 README 架构章节。
