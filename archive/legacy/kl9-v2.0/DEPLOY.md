# KL9-RHIZOME v2.0 · 部署指南

## 环境要求

- Python 3.10+
- 内存: 2GB+（推荐 4GB）
- 磁盘: 1GB+

## 安装步骤

### 1. 克隆仓库

```bash
git clone <repository>
cd kl9-v2.0
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行测试

```bash
pytest tests/ -v
```

### 5. 验证安装

```python
from kl9_v20 import KL9v20

agent = KL9v20()
result = agent.process("测试查询")
print(f"输出: {result.output}")
print(f"压缩率: {result.compression_ratio}")
```

## 生产部署

### Docker 部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "-m", "kl9_v20"]
```

### 服务化部署

```python
# server.py
from fastapi import FastAPI
from kl9_v20 import KL9v20

app = FastAPI()
agent = KL9v20()

@app.post("/compress")
async def compress(query: str):
    result = agent.process(query)
    return {
        "output": result.output,
        "compression_ratio": result.compression_ratio,
        "semantic_retention": result.semantic_retention,
        "fold_depth": result.fold_depth
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
```

## 监控

### 关键指标

- **请求延迟**: p50, p95, p99
- **压缩率分布**: 2.0-2.5x 达标率
- **语义保留率**: > 85% 达标率
- **fold 深度分布**: 2-9 范围
- **技能书状态**: 成功率、平均保留率

### 日志

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('kl9_v20')
logger.info("系统启动")
```

## 配置

### 环境变量

```bash
# 压缩率目标
KL9_TARGET_RATIO=2.5

# 最大 fold 深度
KL9_MAX_FOLD_DEPTH=9

# 语义保留阈值
KL9_RETENTION_THRESHOLD=0.85

# 紧急度阈值
KL9_URGENCY_THRESHOLD=0.8
```

### 配置文件

```python
# config.py
class Config:
    TARGET_RATIO = 2.5
    MAX_FOLD_DEPTH = 9
    RETENTION_THRESHOLD = 0.85
    URGENCY_THRESHOLD = 0.8
    
    # TensionBus 配置
    BUS_TIMEOUT = 5.0
    BUS_MAX_EVENTS = 1000
```

## 性能优化

### 1. 缓存

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_compress(query: str):
    return agent.process(query)
```

### 2. 并发

```python
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

# 并发处理
results = list(executor.map(agent.process, queries))
```

### 3. 预热

```python
# 系统启动时预热
warmup_queries = [
    "测试查询1",
    "测试查询2",
    "测试查询3"
]

for query in warmup_queries:
    agent.process(query)
```

## 故障排除

### 常见问题

1. **压缩率不达标**
   - 检查输入文本长度
   - 调整目标压缩率
   - 增加 fold 深度

2. **语义保留率过低**
   - 检查验证器配置
   - 调整保留阈值
   - 优化压缩策略

3. **性能问题**
   - 启用缓存
   - 增加并发
   - 优化术语网络

### 调试

```python
# 启用调试模式
import logging
logging.getLogger('kl9_v20').setLevel(logging.DEBUG)

# 查看内部状态
stats = agent.get_stats()
print(stats)
```

## 更新

### 版本升级

```bash
# 备份数据
cp -r data/ data_backup/

# 拉取更新
git pull origin main

# 重新安装
pip install -r requirements.txt

# 运行测试
pytest tests/ -v
```

### 回滚

```bash
# 恢复备份
cp -r data_backup/ data/

# 重启服务
systemctl restart kl9_v20
```

---

> *KL9-RHIZOME v2.0 · 压缩涌现智能 · 通用认知架构*
