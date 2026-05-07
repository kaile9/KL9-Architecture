# tests/

测试套件。

| 文件 | 说明 |
|------|------|
| `n9r20_test_compression.py` | 四模式压缩引擎测试 |
| `n9r20_test_router.py` | 自适应路由测试 |
| `n9r20_test_tension_bus.py` | 事件总线测试 |
| `n9r20_test_config.py` | 配置模块测试 |
| `n9r20_test_utils.py` | 工具函数测试 |
| `test_basic.py` | 基础功能测试 |
| `test_bridge.py` | 兼容层测试 |

运行全部测试：
```bash
python -m pytest tests/
```

运行单个模块：
```bash
python -m pytest tests/n9r20_test_router.py
```
