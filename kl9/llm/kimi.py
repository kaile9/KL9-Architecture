"""
9R-2.1 — Kimi K2.6 Optimized Provider

Key optimizations based on official docs:
- 262K context window (not 256K)
- Thinking mode: temperature 1.0 (official recommendation)
- Instant mode: temperature 0.6
- MLA (Multi-head Latent Attention): auto KV cache optimization
- Prefix caching: 75% cost savings, automatic
- max_output_tokens: 98,304 (not 8192!)
- Parallel tools NOT supported — tools sequential
- Cached tokens: $0.15/1M vs $0.60/1M standard
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

import aiohttp

from ..models import LLMProvider, LLMResponse, Message, Usage, RetryConfig
from ..utils.exceptions import (
    ProviderAuthError,
    ProviderBadRequestError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
)

KIMI_API_BASE = "https://api.moonshot.cn/v1"


class KimiProvider(LLMProvider):
    """Kimi K2.6 optimized adapter.

    Supports Thinking mode (deep chain-of-thought) and Instant mode (fast).
    Prefix caching is automatic — no configuration needed.
    """

    NAME = "kimi"
    BASE_URL = KIMI_API_BASE
    MODEL = "kimi-k2-6"
    MAX_TOKENS = 262_144       # Official: 262K context
    MAX_OUTPUT_TOKENS = 98_304  # Official: 98K max output
    EMBED_DIM = 1024

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        model: str | None = None,
        retry_config: RetryConfig | None = None,
        session: Any | None = None,
        thinking_mode: bool = True,  # Default: Thinking mode
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model or self.MODEL,
            retry_config=retry_config,
            session=session,
        )
        self.thinking_mode = thinking_mode

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int = 4096,
        timeout: float = 180.0,
    ) -> LLMResponse:
        messages = self._make_messages(system_prompt, user_prompt)
        temp = temperature if temperature is not None else (1.0 if self.thinking_mode else 0.6)
        return await self._call(messages, temp, max_tokens, timeout)

    async def chat(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int = 4096,
        timeout: float = 180.0,
    ) -> LLMResponse:
        temp = temperature if temperature is not None else (1.0 if self.thinking_mode else 0.6)
        return await self._call(
            [{"role": m.role, "content": m.content} for m in messages],
            temp,
            max_tokens,
            timeout,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json={"model": self.model, "input": texts},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                data = await resp.json()
                if "data" not in data:
                    raise ProviderServerError("embedding failed", provider=self.NAME)
                return [item["embedding"] for item in data["data"]]

    def count_tokens(self, text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            return max(1, len(text) // 4)

    # ── Internal ──

    async def _call(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": min(max_tokens, self.MAX_OUTPUT_TOKENS),
        }

        # Kimi-specific: Thinking mode configuration
        if self.thinking_mode:
            payload["temperature"] = 1.0
            # Kimi's thinking is automatic — no extra config needed
            # Just set temperature 1.0 and let model decide

        t0 = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                data = await resp.json()
                latency = (time.perf_counter() - t0) * 1000

                if resp.status == 401:
                    raise ProviderAuthError(str(data), provider=self.NAME)
                elif resp.status == 429:
                    raise ProviderRateLimitError(str(data), provider=self.NAME, retry_after=60)
                elif resp.status == 400:
                    raise ProviderBadRequestError(str(data), provider=self.NAME)
                elif resp.status >= 500:
                    raise ProviderServerError(str(data), provider=self.NAME)

                choice = data["choices"][0]
                usage_raw = data.get("usage", {})
                return LLMResponse(
                    content=choice["message"]["content"],
                    usage=Usage(
                        prompt_tokens=usage_raw.get("prompt_tokens", 0),
                        completion_tokens=usage_raw.get("completion_tokens", 0),
                        total_tokens=usage_raw.get("total_tokens", 0),
                        cached_tokens=usage_raw.get("prompt_tokens_details", {}).get("cached_tokens", 0),
                    ),
                    provider=self.NAME,
                    model=self.model,
                    finish_reason=choice.get("finish_reason", "stop"),
                    latency_ms=round(latency, 2),
                )

    @staticmethod
    def _make_messages(system: str, user: str) -> list[dict]:
        msgs: list[dict] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": user})
        return msgs


# ── Kimi-Specific System Prompt Optimizations ──

KIMI_OPTIMIZED_SYSTEM_APPENDIX = """
你是Kimi k2.6认知协议执行者。利用你的长上下文能力(262K)进行深度分析。
思考模式已激活：在回应前充分展开推理链。

Kimi专属约束:
- 充分利用262K上下文窗口进行多源引用
- 利用prefix caching: 系统提示会在多轮对话中自动缓存(75%成本节省)
- 输出长度可达98K tokens——不要过早截断深度分析
- 工具调用是顺序的——如果需要多步工具调用，分解为串行步骤
"""
