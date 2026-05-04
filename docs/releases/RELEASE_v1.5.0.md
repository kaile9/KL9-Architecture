# KL9-RHIZOME v1.5.0 — 技能书吸收协议

**2026-05-05**

v1.5.0 实现了技能书 JSON 与 SQLite 概念图谱的双向桥接，标志着技能书系统从"格式标准"进入"可操作阶段"。

### 核心更新

- **SQLite ↔ JSON 桥接**：`kl9_skillbook/bridge.py` 实现导入/导出，包含 Levenshtein 碰撞检测、影子节点分叉和 2-hop 张力局部重算
- **数据库迁移**：`nodes` 表静默新增 6 列（perspective_a/b, tension_score 等），完全向后兼容
- **CLI 导出工具**：`python scripts/export_skillbook.py "书名" "llm源" 4` 一键导出

### 设计原则

碰撞概念**永不自动合并**——同名概念以 `__shadow_` 节点保留双方版本并标记张力；相似度 ≥ 95% 的概念合并定义但附加来源标注。导入不覆盖，只分叉。

### 参与方式

```bash
# 导入样本技能书
python -c "from kl9_skillbook.bridge import import_skillbook_to_graph; import_skillbook_to_graph('skillbooks/de/brock_on_money.skillbook.json')"

# 导出你的图谱
python scripts/export_skillbook.py "你的书名" "你用的LLM" 4
```

去中心化知识传播的第一步。读一本书，留下认知残留，让其他 KL9 实例继承你的思考。
