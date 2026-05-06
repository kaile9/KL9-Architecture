# skillbook/

9R-2.0 技能书系统。

- 持久化记忆存储（SQLite ↔ JSON 桥接）
- 技能书兼容层（9R-1.5 → 9R-2.0 迁移支持）
- `prebuilt/` — 预置技能书（考研、社会学、哲学等）

技能书定义 AI 的工作方式，每个 skill 包含：激活条件、执行流程、输出格式。

安装方式：
```bash
cp -r skills/kailejiu-core ~/.agents/skills/
```
