# KL9-RHIZOME 技能书库

结构化的 KL9 认知导出文件。每个技能书包含：概念图谱节点、DualState 记录、张力配置、阅读轮次摘要。

## 目录结构

```
skillbooks/
├── de/          ← 德语原著（Brodbeck, Simmel, Marx, Hegel...）
├── en/          ← 英语原著
├── fr/          ← 法语原著
├── zh/          ← 中文原著
├── other/       ← 其他语言
├── README.md
└── SKILLBOOK_STANDARD.md   ← 技能书格式规范
```

按原著写作语言分类，而非译者或中文译名语言。例如布德克《货币现象学》归入 `de/`。

## 使用

### 导入技能书

```python
from kl9_skillbook.bridge import import_skillbook_to_graph

result = import_skillbook_to_graph("skillbooks/de/brock_on_money.skillbook.json")
print(result)  # {success, nodes_imported, warnings}
```

### 导出技能书

```bash
python scripts/export_skillbook.py "Geld als Denkform" "deepseek-v4-pro" 4
```

### 格式

见 [SKILLBOOK_STANDARD.md](SKILLBOOK_STANDARD.md)。

## 现有藏书

| 文件 | 语言 | 作者 | 著作 | Quality |
|------|:--:|------|------|:--:|
| `de/brock_on_money.skillbook.json` | DE | Brodbeck | Phänomenologie des Geldes | 4 |
