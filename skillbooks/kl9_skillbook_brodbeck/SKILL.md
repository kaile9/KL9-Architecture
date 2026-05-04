---
name: brodbeck_phaenomenologie_des_geldes
version: "1.0.0"
description: |
  Karl-Heinz Brodbeck《Phänomenologie des Geldes》（货币现象学，2023）的
  KL9-RHIZOME 二重折叠学习记录。首次大规模学习的完整输出。
  
  适合人群：对货币本质有兴趣的理论学习者，已部署了 KL9-RHIZOME v1.5+
  的 AI agent。
  
  内容：
  - 12 个 DualState（逐章二重折叠）
  - 12 个核心概念节点
  - 6 条谱系边（Brodbeck ↔ Simmel/Hegel/Husserl/Aristoteles/Marx/MMT）
  - 3 组理论张力场边
  - 7 个后续待解决问题（follow-up queries）
  - 第二轮学习的三个线程输出（Simmel重读/Marx互补/经济学回应）

  导入后效果：
  - 你的 KL9 实例将理解 Brodbeck 的货币理论体系
  - 能够识别货币作为思维形式 vs 作为量/物/符号/功能之间的张力
  - 能够在对货币相关询问中调用 Brodbeck 的视角进行二重折叠
---

# Brodbeck 学谱 — 货币现象学

## 核心论点（一句话）

货币不是物，不是功能，不是符号，不是量。货币是一种思维形式（Denkform），其存在在于被思维，其实质是大众承担并每天实施的循环式承认幻象（zirkuläre Illusion der Geltung）。

## 导入方式

```python
# 假设 KL9-RHIZOME 框架提供了 import_skillbook 接口
from kl9.imports import import_skillbook

await import_skillbook(
    path="./brodbeck_phaenomenologie_des_geldes",
    merge_strategy="supplement"  # supplement | override | branch
)
```

## 冲突检测与合并

导入时检测同名概念冲突：
- 同名概念不同定义 → 保持双版本 + 标记为 tension
- 同名谱系边不同权重 → 取较高权重，标注 provenance
- 新概念直接加入图谱

## 生态协作

1. 你导入这个学谱 → 你的 KL9 学会 Brodbeck
2. 你补充 Simmel 重读的成果 → fork 出新版本
3. 其他人导入你的学谱 → 你的补充进入他们的图谱
4. 最终形成去中心化的知识根系

> Der Logos verbindet; die Ratio trennt. Das Rhizom verbindet beides.
