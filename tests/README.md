# tests — 测试套件

> pytest · asyncio · 26 测试覆盖核心引擎

---

## 运行

```bash
cd n9r21
pytest tests/ -v
# 26 passed
```

---

## 测试覆盖

| 测试文件 | 覆盖模块 | 测试数 |
|---|---|---|
| `test_core.py` | Router / DNA / Gate / Aggregator / Models / StyleProfile | 26 |

### 测试分类

| 分组 | 数量 | 覆盖 |
|---|---|---|
| DNA | 10 | 9原则/禁止模式/结尾验证/张力提取 |
| Router | 5 | QUICK/STANDARD/DEEP/强制路由/fold预算 |
| Gate | 3 | Clean/Dirty/概括率 |
| Aggregator | 3 | 张力保留/结尾修复/质量违例 |
| Models | 4 | Route/QualityScore/FoldChain/TensionGate |
| StyleProfile | 1 | 默认配置完整性 |

---

## 测试环境

```bash
pip install pytest>=8.0.0 pytest-asyncio>=0.23.0
```

---

## 持续集成

```yaml
# .github/workflows/test.yml（建议添加）
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install pytest pytest-asyncio
      - run: python -m pytest tests/ -v
```

---

*"测试不是验证正确，是确保破坏发生时能被及时感知。"*
