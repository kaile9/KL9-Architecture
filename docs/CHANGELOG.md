# Changelog

All notable changes to KL9-RHIZOME will be documented in this file.

---

## [1.1.0] — 2026-05-06 — 双维度评分系统

### Added
- **双维度评分引擎** (`kl9_skillbook/scorer.py`): 信任公式 `trust = quality × (1 - difficulty/200)`
- **难度评估** (`estimate_difficulty`): 四维度启发式评分（风格密度/信息密度/观点创新/引用密度）
- **质量评估** (`estimate_quality`): 基于 ProductionRecord 的客观评分（轮数+验证+反视角）
- **信任阈值**: 4 级吸收策略（完整/补充/选择性/拒绝）
- **数据模型** (`ProductionRecord`, `DifficultyBreakdown`): 制作记录与难度细分
- **v1.1 验证规则**: `difficulty` 和 `quality_score` 为 FATAL 必填，`production_record` 为 WARNING
- **导出增强**: `export_skillbook.py` 支持 `--rounds`, `--verify`, `--hours`, `--counter` 参数
- **导出自动评分**: `export_graph_to_skillbook()` 自动执行难度/质量评估
- **导入信任检查**: `import_skill_book()` 和 `import_skillbook_to_graph()` 在 import 前评估信任
- **向后兼容**: v1.0 的 `quality_tier` 自动映射为 `quality_score = quality_tier × 20`

### Changed
- `SkillBookManifest`: 新增 `difficulty`, `quality_score`, `production_record`, `difficulty_breakdown`
- `validate_manifest`: 接受 v1.0 和 v1.1 双版本
- `import_skill_book`: 默认版本号升级为 "1.1"
- `export_graph_to_skillbook`: 输出 v1.1 格式，自动嵌入评分
- `import_skillbook_to_graph`: 返回结果包含 `trust` 和 `trust_level`
- 样本技能书更新为 v1.1 完整格式
- `SKILLBOOK_STANDARD.md` 更新为 v1.1 完整规范

### Technical Details
- 列表视图只显示 `difficulty` 分，`quality_score` 在 manifest 内
- 信任分 ≥90: full / 60-90: supplementary / 30-60: selective / <30: reject
- 难度启发式可用于无 LLM 环境（citation_density 暂返回中性值 50）

---

## [1.5.0] — 2026-05-05 — 技能书吸收协议

### Added
- **SQLite ↔ JSON 桥接** (`kl9_skillbook/bridge.py`): 双向导入/导出，含碰撞检测、影子分叉与张力局部重算
- **SQLite schema 扩展**: `nodes` 表新增 `perspective_a`, `perspective_b`, `tension_score`, `local_confidence`, `is_shadow`, `shadow_of` 六列
- **`store_concept()` 增强**: 支持所有新字段的持久化
- **CLI 导出工具** (`scripts/export_skillbook.py`): 一行命令将 SQLite 图谱导出为标准技能书 JSON
- **桥接测试套件** (`tests/test_bridge.py`): 11 个测试覆盖导出/导入/往返/边完整性/新字段
- **样本技能书** (`skillbooks/de/Brodbeck-Phaenomenologie_des_Geldes-2023/SKILL.md`): Brodbeck 货币现象学，螺旋递归论证结构，146 行
- **版本公告** (`docs/releases/RELEASE_v1.5.0.md`): v1.5.0 发布说明

### Changed
- `graph_backend._get_conn()` 新增静默列迁移（try/except pass，兼容旧数据库）
- `graph_backend.store_concept()` 签名扩展：新增 6 个可选参数（向后兼容）
- README 更新：技能书吸收协议使用说明、核心原理图示、统计数字更新

### Technical Details
- 碰撞检测复用 `kl9_skillbook/matcher.py` 的 Levenshtein 算法
- 合并逻辑复用 `kl9_skillbook/merger.py` 的影子分叉策略
- 张力重算复用 `kl9_skillbook/tension.py` 的 2-hop 局部更新

---

## [1.0.0] — Initial Release

### Core
- DualState 双视角加载
- TensionBus 事件总线
- dual_fold 递归折叠引擎
- 6 种张力类型 × 7 组推荐二重组合
- Constitutional DNA 五原则
- 9 层模块架构（core, reasoner, soul, graph, research, memory, learner, orchestrator, shared）
- SQLite 概念图谱（BM25 检索 + 子图遍历）
- SQLite 记忆后端（sessions, feedback, reading_list）
- 技能书 JSON 格式标准（validator, matcher, merger, tension, importer）
