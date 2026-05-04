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

## 现有藏书

| 文件 | 语言 | 作者 | 著作 | 年份 | Quality |
|------|:--:|------|------|:--:|:--:|
| `de/Brodbeck-Phaenomenologie_des_Geldes-2023.skillbook.json` | DE | Brodbeck | Phänomenologie des Geldes | 2023 | 4 |
