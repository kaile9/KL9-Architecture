# examples/

使用示例与参考。

| 文件 | 说明 |
|------|------|
| `quickstart.py` | ⚠️ 已迁移到根目录。现为主 Agent 入口，支持 REPL / API / OpenClaw 三种模式。 |
| `reference-prompt.md` | 参考提示词模板 |

根目录 `quickstart.py` 用法：
```bash
python quickstart.py                    # 交互式 REPL（默认）
python quickstart.py --mode api         # HTTP API 服务
python quickstart.py --mode openclaw   # 输出插件配置 JSON
python quickstart.py --eval "query"     # 单条评估
```

