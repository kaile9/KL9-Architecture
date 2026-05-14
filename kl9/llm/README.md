# kl9/llm — LLM 提供商适配层

> 统一接口 · 多后端切换 · 成本透明

---

## 推荐的后端LLM

| 提供商 | 文件 | 适用场景 | 成本特征 |
|---|---|---|---|
| **Kimi k2.6** | `kimi.py` | 中文长文本 / 推理 / 压缩涌现 | 输入缓存命中 ~95%，低成本 |
| **DeepSeek V4** | `deepseek.py` | 代码 / 数学 / 英文分析，1M 上下文 | 输出快，价格极低 |
| **Claude Opus 4.7** | `opus.py` | 创意写作 / 复杂推理，200K 上下文 | 高成本，按需启用 |

> **环境配置**: 在 AstrBot WebUI 中选择 `router/decomposer/fold/validator` 各自使用的 LLM。
> **推荐**: 路由选择 DeepSeek V4 Flash（快速便宜），递归折叠选择 Kimi K2.6 或 Opus 4.7。

---

## 统一接口

所有后端实现相同的 `LLMProvider` 抽象基类：

```python
class LLMProvider(ABC):
    async def complete(self, system_prompt, user_prompt, **kwargs) -> LLMResponse: ...
    async def chat(self, messages, **kwargs) -> LLMResponse: ...
    def count_tokens(self, text: str) -> int: ...
```

---

## 快速开始

### Kimi K2.6

```python
from kl9.llm.kimi import KimiProvider

provider = KimiProvider(api_key="sk-xxx", thinking_mode=True)
result = await provider.complete(
    system_prompt="你是认知协议执行者。",
    user_prompt="分析福柯规训社会与韩炳哲倦怠社会的辩证关系",
    temperature=1.0,  # Thinking mode 推荐温度
)
```

### DeepSeek V4

```python
from kl9.llm.deepseek import DeepSeekV4Provider

provider = DeepSeekV4Provider(api_key="sk-xxx")
result = await provider.complete(
    system_prompt="...",
    user_prompt="分析...",
    temperature=0.3,
)
```

### Claude Opus 4.7

```python
from kl9.llm.opus import Opus47Provider

provider = Opus47Provider(api_key="sk-ant-xxx", thinking_budget=16384)
result = await provider.complete(
    system_prompt="(不要给出一步步思考指令——模型有内部推理scratchpad)",
    user_prompt="分析...",
    max_tokens=16000,
)
```

---

## 多后端切换

```python
from kl9.llm import get_provider

# 根据环境自动选择
provider = get_provider(
    preferred="kimi",      # 优先使用
    fallback="deepseek",   # 备选
)

# 或在系统层统一注入
from kl9.system import KL9System

kl9 = KL9System(provider)
```

---

## Provider 规格对照

| 提供商 | MAX_TOKENS | MAX_OUTPUT_TOKENS | 推荐温度 |
|---|---|---|---|
| DeepSeek V4 | 1,048,576 | 32,768 | 0.3 |
| Kimi K2.6 | 262,144 | 98,304 | 1.0 (thinking) / 0.6 (instant) |
| Claude Opus 4.7 | 200,000 | 32,000 | adaptive (不设显式 CoT) |

---

## Token 缓存策略

Kimi 后端支持 **Prefix Caching**（自动，无配置）：

- 系统提示词 + 宪法 DNA → 自动缓存
- 缓存命中率 ~95%
- 成本降低 ~75%（缓存输入 $0.15/1M vs 标准 $0.60/1M）

---

## 环境变量

| 变量 | 说明 |
|---|---|
| `KL9_PROVIDER` | 默认后端 (`kimi` / `deepseek` / `opus`) |
| `KIMI_API_KEY` | Kimi API 密钥 |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `ANTHROPIC_API_KEY` | Claude/Anthropic API 密钥 |

---

*"LLM 不是大脑，是肌肉。认知协议层才是神经系统。"*
