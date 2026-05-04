# KL9-RHIZOME 技能书库

每个技能书 = **一个 `.skillbook.json` 文件**，包含 manifest + 概念图谱。按原著写作语言分类。

## 目录结构

```
skillbooks/
├── de/          ← 德语原著
├── en/          ← 英语原著
├── fr/          ← 法语原著
├── zh/          ← 中文原著
├── other/       ← 其他语言
├── README.md
└── SKILLBOOK_STANDARD.md   ← 技能书格式规范
```

## 文件命名规则

```
作者-书名-年份.skillbook.json
```

例如：`Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json`

## 使用

### 导入

```python
from kl9_skillbook.bridge import import_skillbook_to_graph
result = import_skillbook_to_graph("skillbooks/de/Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json")
```

### 导出

```bash
python scripts/export_skillbook.py "Phänomenologie des Geldes" "deepseek-v4-pro" 4
```

## 评分体系 v1.2

### 难度分 (0-100)
LLM 评估四项取均值：风格密度、信息密度、观点创新、引用密度

### 质量分 (0-100)
基于制作记录：rounds×20(≤60) + verify(0/10/20) + counter×5(≤20)

### 模型能力上限 (动态)
基于 HLE×0.5 + Arena Overall×0.25 + Arena Creative Writing×0.25 实时计算，非固定层级

### 语言补偿
中文模型读中文书 +3%，英文模型读中文书 −3%，依此类推

详见 [SKILLBOOK_STANDARD.md](SKILLBOOK_STANDARD.md)

## 现有藏书

| 文件 | 语言 | 作者 | 著作 | 年份 | Quality |
|------|:--:|------|------|:--:|:--:|
| `de/Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json` | DE | Brodbeck | Phänomenologie des Geldes | 2023 | 4 |
