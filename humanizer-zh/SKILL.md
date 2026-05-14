---
name: humanizer-zh
description: |
  开了玖文本抛光器。对中文文本进行后置扫描，检测 AI 生成痕迹、保护区侵蚀、
  强化区可优化点，输出极简检测报告。支持命令行调用与脚本集成。
---

# humanizer-zh · 中文文本抛光器

## 用途

检测并优化中文文本中的 AI 生成痕迹，减少机械感，保留风格锐度。

## 使用方式

直接调用脚本：

```bash
python scripts/kailejiu_linter.py --text "待检测文本"
python scripts/kailejiu_linter.py --file input.txt
echo "文本" | python scripts/kailejiu_linter.py --stdin
```

脚本输出结构化 markdown 检测报告，含行号定位、问题引用、简易评分。

## 检测维度

| 类别 | 说明 |
|------|------|
| 清除区 | AI 高频连接词、人称呼告、套话等 |
| 保护区 | 风格核心表达，误伤告警 |
| 强化区 | 可进一步锐化或精简之处 |

## 依赖

Python 3.8+，无第三方依赖。

## 注意

本 skill 为辅助检测工具，不提供自动改写功能。改写决策由使用者自行裁定。
