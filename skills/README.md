# skills — KL9 认知技能模块 · Cognitive Skill Modules

每个子目录是一个独立的认知技能，由 orchestrator 通过 TensionBus 动态激活。

*Each subdirectory is an independent cognitive skill, dynamically activated by the orchestrator via TensionBus.*

### 技能架构

```
skills/
├── kailejiu-core/         ← 二重认知初始化层
├── kailejiu-orchestrator/ ← TensionBus 协调器
├── kailejiu-graph/        ← 概念知识图谱层
├── kailejiu-memory/       ← 持久记忆层
├── kailejiu-reasoner/     ← 理论视角认知运算（Perspective A）
├── kailejiu-soul/         ← 具身视角成长引擎（Perspective B）
├── kailejiu-research/     ← 对话式理论激活层
├── kailejiu-learner/      ← 二重学习迭代
└── kailejiu-shared/       ← 共享库
```

每个技能通过 `SKILL.md` 声明能力，通过 `scripts/` 实现逻辑。
