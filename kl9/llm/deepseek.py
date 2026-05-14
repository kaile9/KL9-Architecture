"""
9R-2.1 — DeepSeek V4 Provider

1M context window. OpenAI-compatible API.
Primary provider for tonight's implementation.
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

DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"


class DeepSeekV4Provider(LLMProvider):
    NAME = "deepseek"
    BASE_URL = DEEPSEEK_API_BASE
    MODEL = "deepseek-chat"
    MAX_TOKENS = 1_048_576  # 1M context
    MAX_OUTPUT_TOKENS = 32768

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        model: str | None = None,
        retry_config: RetryConfig | None = None,
        session: Any | None = None,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model or self.MODEL,
            retry_config=retry_config,
            session=session,
        )

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        timeout: float = 120.0,
    ) -> LLMResponse:
        messages = self._make_messages(system_prompt, user_prompt)
        return await self._call(messages, temperature, max_tokens, timeout)

    async def chat(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        timeout: float = 120.0,
    ) -> LLMResponse:
        return await self._call(
            [{"role": m.role, "content": m.content} for m in messages],
            temperature,
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
                json={"model": "deepseek-chat", "input": texts},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                data = await resp.json()
                if "data" not in data:
                    raise ProviderServerError("embedding failed", provider=self.NAME)
                return [item["embedding"] for item in data["data"]]

    def count_tokens(self, text: str) -> int:
        # Heuristic: ~4 chars per token for CJK+EN mixed
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
                    raise ProviderRateLimitError(str(data), provider=self.NAME)
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
                    ),
                    provider=self.NAME,
                    model=self.model,
                    finish_reason=choice.get("finish_reason", "stop"),
                    latency_ms=round(latency, 2),
                )

    @staticmethod
    def _make_messages(system: str, user: str) -> list[dict]:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": user})
        return msgs
