# KL9 Skillbook Specification v2.0

> 9R-2.0 版本 | 从"张力悬置"到"压缩涌现" | 向下兼容 v1.x

---

## 版本演进

| 版本 | 核心哲学 | 关键变化 |
|------|----------|----------|
| v1.x (9R-1.5) | 张力悬置（拒绝输出） | A ↔ B → 悬置 |
| **v2.0 (9R-2.0)** | **压缩涌现（必须输出）** | A ↔ B → 压缩折叠 → 涌现决断 |

v2.0 不是否定 v1.x，而是**在悬置之后增加了压缩涌现层**——张力不再是终点，而是燃料。

---

## 核心概念变化

### v1.x：张力悬置
```
视角 A → 张力检测 → 悬置（不输出）
视角 B →
```

### v2.0：压缩涌现
```
视角 A → 张力检测 → 压缩折叠 → 涌现决断（输出）
视角 B →         ↑
              四模式：
              construct → deconstruct → validate → interrupt
```

**关键区别**：v2.0 不再拒绝输出，而是通过压缩折叠让两个视角的结构精华涌现为一个决断。

---

## 目录结构（v2.0）

```
skills/
├── {lang}/                     # 语言代码：ZH, EN, FR, DE, JP, OTHER
│   └── {Author-Title-Year}/
│       ├── SKILL.md            # 技能书本体
│       ├── META.yaml           # 元数据
│       ├── ATTRIBUTION.md      # 引用来源
│       └── compressed/         # v2.0 新增：压缩后的认知残留
│           └── v{version}/
│               └── fold-{depth}.md
└── prebuilt/                   # v2.0 新增：预置技能书
    ├── kailejiu-core/          # 核心技能
    ├── sociology/              # 社会学
    ├── philosophy/             # 哲学
    └── exam-prep/              # 考研
```

**v1.x → v2.0 迁移**：
- `skillbooks/` → `skills/`（目录改名）
- 新增 `compressed/` 子目录（存储压缩后的认知残留）
- 新增 `prebuilt/` 目录（预置技能书集合）
- `SKILL.md` 格式保持兼容，新增 `compressed/` 字段

---

## SKILL.md 格式（兼容 v1.x，扩展 v2.0）

```yaml
---
meta:
  version: "2.0"              # 升级版本号
  lang: "ZH"
  title: "弱者致死是孩子"
  author: "开了玖"
  year: 2026
  tags: ["社会批判", "精神分析", "规培制度"]
  difficulty: 0.8            # 0-1，阅读难度
  quality: 0.9                # 0-1，内容质量

  # v2.0 新增
  compression:
    version: "2.0"
    fold_depth: 6             # 压缩折叠深度
    compression_ratio: 2.5     # 压缩率
    retained_concepts: 12      # 保留概念数
    tension_points: 3          # 张力悬置点数

  # v2.0 新增：兼容性标记
  compatibility:
    min_core_version: "2.0"
    backward_compatible: true  # 是否兼容 v1.x 运行时

# v1.x 保持不变的认知核心
core_concepts:
  - "主体性危机"
  - "规训权力"
  - "倦怠社会"

tension_field:
  - perspective_a: "制度理性"
    perspective_b: "个体情感"
    tension_type: "结构性对立"

# v2.0 新增：压缩残留
compressed_core:
  fold_depth: 6
  mode_sequence: ["construct", "deconstruct", "validate", "interrupt"]
  output: |
    [压缩后的认知残留文本]
    保留核心论证结构
    张力点标记为 {tension}
    涌现决断标记为 {emergence}

# v1.x 保持不变的贡献信息
attribution:
  sources: [...]
  confidence: 0.9
---
```

---

## 吸收协议（v2.0 扩展）

### v1.x 原版（保持不变）
1. 碰撞分叉优于强行合并
2. 溯源高于权重
3. 概念节点 > 具体案例
4. 张力保持 > 廉价和解
5. 迭代吸收 > 一次成型

### v2.0 新增
6. **压缩涌现优于单纯悬置** — 不拒绝输出，而是通过压缩让精华涌现
7. **四模式验证** — construct → deconstruct → validate → interrupt，每步可追踪
8. **语义保留率 ≥ 0.85** — 压缩后核心概念保留率不低于 85%

---

## 评分体系（兼容 v1.x）

### 双维度评分（不变）
- 难度（D）：0-1
- 质量（Q）：0-1

### 信任公式（不变）
```
TrustScore = (D × 0.3) + (Q × 0.7)
```

### v2.0 新增维度
- 压缩深度（F）：fold_depth / max_fold_depth
- 涌现质量（E）：基于 LLM 评估器的 fold 质量评分
- **综合评分**：
```
v2_Score = (D × 0.2) + (Q × 0.5) + (F × 0.2) + (E × 0.1)
```

---

## 贡献指南

### 新增技能书（v2.0 流程）

1. 选择语言目录 `skills/{lang}/`
2. 创建 `{Author-Title-Year}/`
3. 编写 `SKILL.md`（使用 v2.0 格式，兼容 v1.x）
4. 运行压缩验证：
   ```bash
   python -m kl9_v20.compress SKILL.md --fold-depth=6
   ```
5. 检查保留率 ≥ 0.85
6. 提交 PR

### 从 v1.x 迁移技能书

```bash
# 自动迁移工具
python -m kl9_v20.migrate skillbooks/ skills/
```

迁移规则：
- 保留所有 v1.x 字段
- 自动添加 v2.0 压缩字段（运行一次压缩生成）
- `backward_compatible: true` 自动标记

---

## 向下兼容承诺

**v2.0 完全兼容 v1.x 技能书**：
- v1.x 的 SKILL.md 无需修改即可在 v2.0 运行时使用
- v2.0 新增字段为可选，不影响 v1.x 解析
- v1.x 运行时遇到 v2.0 字段自动忽略

**兼容性矩阵**：

| 技能书版本 | 运行时版本 | 兼容性 |
|-----------|-----------|--------|
| v1.x | v1.x | ✅ 原生 |
| v1.x | v2.0 | ✅ 兼容（忽略新字段） |
| v2.0 | v1.x | ⚠️ 降级（压缩字段失效，但核心可用） |
| v2.0 | v2.0 | ✅ 原生 |

---

## 藏书目录（v2.0）

### 已归档（v1.x → archive/v1/）
- DE(1): 布尔迪厄《区分》
- FR(1): 韩炳哲《倦怠社会》
- ZH(1): 预留

### 预置技能书（v2.0 → skills/prebuilt/）
- kailejiu-core: 核心认知协议
- sociology: 社会学概念集
- philosophy: 哲学概念集
- exam-prep: 考研知识库

### 自定义技能书（v2.0 → skills/{lang}/）
- 等待社区贡献

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2025-08 | 初代技能书规范 |
| v1.2 | 2026-01 | 9R-1.5 稳定版 |
| **v2.0** | **2026-05** | **9R-2.0 压缩涌现版** |

---

*基于 SKILLBOOK.md v1.2 迭代，保留所有 v1.x 规范，新增压缩涌现层。*
*向下兼容承诺：v1.x 技能书无需修改即可在 v2.0 使用。*
