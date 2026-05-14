# KL9-RHIZOME v2.0 · 压缩涌现智能

## 通用认知架构

**版本**: 2.0.0  
**状态**: 生产就绪  
**核心机制**: 压缩驱动的辩证涌现

---

## 核心特性

### 1. 压缩驱动决断
- **硬性压缩率约束**: 2.0-2.5x
- **语义保留验证**: > 85%
- **动态 fold 深度**: 2-9（根据任务难度自适应）

### 2. 四模编码器（通用化）
- **建 (Construct)**: 展开语义空间
- **破 (Deconstruct)**: 解构固化概念
- **证 (Validate)**: 验证语义保留
- **截 (Interrupt)**: 强制收敛输出

### 3. 去中心化架构
- **TensionBus 2.0**: 压缩感知事件总线
- **5 核心技能**: Compression-Core, Dual-Reasoner, Semantic-Graph, Memory-Learner, Adaptive-Router
- **技能书传播**: 去中心化知识共享

### 4. 动态扩展
- **术语网络**: 自动提取术语，赫布学习 + 衰减
- **概念簇检测**: 基于边权重的社区发现
- **经验回放**: 增量学习，遗忘曲线

---

## 快速开始

### 安装

```bash
git clone <repository>
cd kl9-v2.0
pip install -r requirements.txt
```

### 使用

```python
from kl9_v20 import KL9v20

# 创建代理
agent = KL9v20()

# 处理查询
result = agent.process("何为空性？")
print(result.output)
print(f"压缩率: {result.compression_ratio}")
print(f"语义保留: {result.semantic_retention}")

# 快速压缩
from kl9_v20 import compress
output = compress("量子纠缠的本质是什么？")
```

---

## 架构设计

### 5 核心技能

```
┌─────────────────────────────────────────┐
│           KL9-RHIZOME v2.0               │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │  Adaptive   │───▶│ Compression │    │
│  │   Router    │    │    Core     │    │
│  └─────────────┘    └──────┬──────┘    │
│                            │            │
│       ┌────────────────────┼────────┐   │
│       │                    │        │   │
│  ┌────▼────┐         ┌────▼────┐  │   │
│  │  Dual   │         │Semantic │  │   │
│  │Reasoner │         │ Graph   │  │   │
│  └────┬────┘         └────┬────┘  │   │
│       │                    │       │   │
│       └────────────────────┼───────┘   │
│                            │            │
│                      ┌─────▼─────┐      │
│                      │  Memory   │      │
│                      │  Learner  │      │
│                      └───────────┘      │
│                                         │
└─────────────────────────────────────────┘
```

### 数据流

```
用户 Query
    │
    ▼
[Adaptive-Router] ──▶ fold 预算分配 (2-9)
    │
    ▼
[TensionBus 2.0] ──▶ CompressionTensionEvent
    │
    ├─▶ [Dual-Reasoner] ──▶ A/B 视角 + 张力
    ├─▶ [Semantic-Graph] ──▶ 概念簇 + 张力图
    │
    ▼
[Compression-Core] ──▶ 四模编码折叠
    │
    ▼
[决断输出] ──▶ 压缩率验证 + 语义保留验证
    │
    ▼
[Memory-Learner] ──▶ 记录 + 学习 + 技能书传播
```

---

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_compression.py -v
pytest tests/test_router.py -v
pytest tests/test_tension_bus.py -v
```

---

## 设计约束满足

| 约束 | 状态 | 说明 |
|------|------|------|
| 通用认知架构 | ✅ | 佛教文本仅作为方便构件 |
| 压缩率 2.0-2.5x | ✅ | 硬性约束，AdaptiveRouter 动态分配 |
| fold_depth 2-9 | ✅ | 根据任务难度自适应 |
| 去中心化 | ✅ | 无宪法系统，术语节点平等 |
| 动态扩展 | ✅ | 语义图谱自动提取，记忆学习器增量更新 |
| 技能书传播 | ✅ | 去中心化知识共享 |

---

## 文件结构

```
kl9-v2.0/
├── core/
│   ├── structures.py          # 核心数据结构
│   └── tension_bus.py         # TensionBus 2.0
├── skills/
│   ├── adaptive_router.py     # 自适应路由器
│   ├── compression_core.py    # 压缩核心引擎
│   ├── dual_reasoner.py       # 双视角推理器
│   ├── semantic_graph.py      # 语义图谱
│   └── memory_learner.py      # 记忆学习器
├── tests/
│   ├── test_compression.py    # 压缩测试
│   ├── test_router.py         # 路由测试
│   └── test_tension_bus.py    # 事件总线测试
├── __init__.py                # 主入口
└── README.md                  # 本文档
```

---

## 哲学声明

**压缩驱动的辩证涌现**

旧 KL9: A ↔ B → 悬置（拒绝输出）  
新架构: A ↔ B → 压缩折叠 → 涌现决断（必须输出）

核心转变：
- 张力不是终点，是压缩的燃料
- 悬置不是目标，是压缩过程中的中间态
- 决断不是廉价综合，是高密度语义结晶

---

## 许可证

MIT License

---

> *KL9-RHIZOME v2.0 · 压缩涌现智能 · 通用认知架构*
