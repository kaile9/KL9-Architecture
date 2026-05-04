---
name: kailejiu-soul
description: |
  KL9-RHIZOME v1.5 · Perspective B — 具身视角的"慢性烫伤"式成长引擎。

  不替代人格提示词，而是为其提供动态风格偏好和体验记忆。
  使 emergent_style 从查表变为共振。可见成长，抗污染。

  订阅 FoldCompleteEvent，每次认知管道后做微量 EMA 更新。
  为 emergent_style 提供 style_guidance（理论亲和/张力感受/风格轮廓）。
---

# 开了玖 · 灵魂核心 · KL9-RHIZOME v1.5

## 角色

soul 不是"另一个认知管道"。它是小开这个角色的**成长层**：
- **Layer 1（不变）**: Constitutional DNA — 硬约束，气质声明
- **Layer 2（缓慢变化）**: Soul Core — 理论亲和度、张力敏感度、风格偏好
- **Layer 3（每次涌现）**: Emergent Style — 由 tension_type + soul 偏好共振生成

## 设计原则

### 慢性烫伤
每次交互只做 EMA(0.95) 更新 — 新数据权重 5%。单次恶意交互最多移动 5%，累积有机交互会自动恢复。

### 抗污染
- 每小时最多 20 次更新（防轰炸）
- EMA 衰减保证污染输入不可能永久改变灵魂
- 至少累积 MIN_INTERACTIONS=3 次交互后才开始影响 emergent

### 零 LLM 开销
- 纯本地 SQLite 运算
- `extract_stylistic_patterns()` — 规则引擎，无需 LLM
- `extract_theories_from_dialogues()` — 从已激活的对话中直接提取

### 为 emergent 铺路
`get_style_guidance(tension_type)` 输出：
```python
{
    "affinities": [("鲍德里亚", 0.72), ("福柯", 0.45)],
    "tension_feel": 0.65,          # 对该张力的处理自然度
    "stylistic_hints": ["并置而非缝合", "悬置保持"],
    "growth_phase": "forming",
    "ready": True,
}
```

emergent_style 消费这些数据，不再做硬编码字典查表，而是做加权共振。

## 可见成长

成长里程碑通过 `soul_visible_log` 表记录：
- `nascent` (0-10 交互): 初生，soul 不参与生成
- `forming` (10-50): 成形，理论亲和开始显现
- `mature` (50-200): 成熟，风格轮廓稳定
- `weathered` (200+): 风化，深度内化

阶段转换和显著的亲和度变化会在对话中自然流露。

## 实现文件

- `scripts/soul_core.py` — 灵魂核心（EMA 更新、风格引导、模式提取）
- 数据库: `kailejiu-shared/storage/memory.db`（与 memory.py 共用）
