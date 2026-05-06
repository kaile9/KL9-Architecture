# scripts — 命令行工具 · CLI Tools

| 脚本 | 用途 |
|------|------|
| `export_skillbook.py` | 将当前 SQLite 图谱导出为技能书 JSON · Export SQLite graph to skillbook JSON |

### 使用

```bash
# 导出技能书（书名 / LLM来源 / 质量等级 1-5）
python scripts/export_skillbook.py "Phänomenologie des Geldes" "deepseek-v4-pro" 4
```
