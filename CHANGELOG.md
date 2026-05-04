# Changelog

All notable changes to KL9-RHIZOME will be documented in this file.

---

## [1.5.0] — 2026-05-05 — 技能书吸收协议

### Added
- **SQLite ↔ JSON 桥接** (`kl9_skillbook/bridge.py`): 双向导入/导出，含碰撞检测、影子分叉与张力局部重算
- **SQLite schema 扩展**: `nodes` 表新增 `perspective_a`, `perspective_b`, `tension_score`, `local_confidence`, `is_shadow`, `shadow_of` 六列
- **`store_concept()` 增强**: 支持所有新字段的持久化
- **CLI 导出工具** (`scripts/export_skillbook.py`): 一行命令将 SQLite 图谱导出为标准技能书 JSON
- **桥接测试套件** (`tests/test_bridge.py`): 11 个测试覆盖导出/导入/往返/边完整性/新字段
- **样本技能书** (`skillbooks/de/Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json`): 7 个布德克货币哲学概念，quality_tier=4
- **版本公告** (`docs/RELEASE_v1.5.0.md`): v1.5.0 发布说明

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
