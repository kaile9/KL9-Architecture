# 技能书质量评测 — 社区共建计划

## 问题

当前评分系统使用 HLE + Arena Elo + Arena Creative Writing 作为代理指标。但没有任何基准能直接衡量"模型能不能把一本哲学/社科著作读懂并转化为高质量技能书"。我们承认：**这是路灯效应——我们测了能测的，没测该测的。**

## Designer 的方案

对每个模型生成 3 本技能书（统一 3 个 prompt），由人类评估三项：

| 维度 | 权重 | 说明 |
|------|:--:|------|
| 结构完整度 | 40% | 必填字段齐全、manifest 正确、概念嵌套合理 |
| 信息密度 | 30% | 每百 token 独有事实数（去重后） |
| 引用准确率 | 30% | 有明确源出处的声明比例 |

综合分 = (结构×0.4 + 密度×0.3 + 引用×0.3) × 1.5，封顶 100。

## 如何参与

1. Fork [KL9-Architecture](https://github.com/kaile9/KL9-Architecture)
2. 选一个模型，用 `scripts/export_skillbook.py` 生成技能书
3. 填写评测记录到 `eval/records/` 目录
4. 提交 PR

## 评测模板

```json
{
  "model": "deepseek-v4-pro",
  "book": "Phänomenologie des Geldes",
  "evaluator": "@github_username",
  "date": "2026-05-XX",
  "scores": {
    "structural_completeness": 85,
    "information_density": 72,
    "citation_accuracy": 68
  },
  "notes": "概念提取准确，但对Brodbeck的论证结构把握有偏差"
}
```

## 目标

积累 100+ 条评测后，发布独立的 **KL9 技能书质量榜单**，替代当前代理评分。

当前代理公式(仅供参考): combined = HLE×0.50 + Arena_norm×0.25 + CW_norm×0.25
