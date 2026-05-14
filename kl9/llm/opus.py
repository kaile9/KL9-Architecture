"""
9R-2.1 — Claude Opus 4.7 Optimized Provider

Key findings from official docs and community benchmarks:
- DO NOT give explicit step-by-step chain-of-thought instructions
  → degrades performance (overrides RL-trained internal scratchpad)
- DO use adaptive thinking: thinking={type: "adaptive"}
- DO use verification slot in prompts: "verify before responding"
- DO be explicit and literal — Opus 4.7 won't infer unrequested content
- Price: $5 input / $25 output per 1M tokens
- Default thinking: 16K tokens, extendable to 64K
- Best for: long-document synthesis, code review, multi-source analysis
- Worse for: simple Q&A (use Sonnet), creative writing without structure
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

ANTHROPIC_API_BASE = "https://api.anthropic.com/v1"

OPUS_47_MODEL = "claude-opus-4-7"
OPUS_47_MAX_TOKENS = 200_000
OPUS_47_MAX_OUTPUT = 32_000
OPUS_47_DEFAULT_THINKING = 16_384  # Default thinking budget


class Opus47Provider(LLMProvider):
    """Claude Opus 4.7 optimized adapter.

    Uses adaptive thinking mode. Never injects explicit CoT instructions.
    Verification-first prompt structure for best results.
    """

    NAME = "claude-opus"
    BASE_URL = ANTHROPIC_API_BASE
    MODEL = OPUS_47_MODEL
    MAX_TOKENS = OPUS_47_MAX_TOKENS
    MAX_OUTPUT_TOKENS = OPUS_47_MAX_OUTPUT
    EMBED_DIM = 4096

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str | None = None,
        model: str | None = None,
        retry_config: RetryConfig | None = None,
        session: Any | None = None,
        thinking_budget: int = OPUS_47_DEFAULT_THINKING,
        anthropic_version: str = "2026-04-16",
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model or self.MODEL,
            retry_config=retry_config,
            session=session,
        )
        self.thinking_budget = thinking_budget
        self.anthropic_version = anthropic_version

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 16000,
        timeout: float = 180.0,
    ) -> LLMResponse:
        return await self._call(
            system_prompt,
            [{"role": "user", "content": user_prompt}],
            temperature,
            min(max_tokens, self.MAX_OUTPUT_TOKENS),
            timeout,
        )

    async def chat(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.3,
        max_tokens: int = 16000,
        timeout: float = 180.0,
    ) -> LLMResponse:
        system = ""
        user_messages: list[dict] = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                user_messages.append({"role": m.role, "content": m.content})

        return await self._call(system, user_messages, temperature, max_tokens, timeout)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Anthropic doesn't have a public embedding API — use heuristic fallback
        raise NotImplementedError("Anthropic embedding not available. Use DeepSeek or BGE-M3.")

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
        system: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        timeout: float,
    ) -> LLMResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
            "Content-Type": "application/json",
        }

        # Opus 4.7: adaptive thinking — do NOT inject explicit CoT
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "thinking": {
                "type": "adaptive",
                "budget_tokens": self.thinking_budget,
            },
        }
        if system:
            payload["system"] = system
        if temperature > 0:
            payload["temperature"] = temperature

        t0 = time.perf_counter()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                data = await resp.json()
                latency = (time.perf_counter() - t0) * 1000

                if resp.status == 401 or resp.status == 403:
                    raise ProviderAuthError(str(data), provider=self.NAME)
                elif resp.status == 429:
                    raise ProviderRateLimitError(str(data), provider=self.NAME, retry_after=60)
                elif resp.status == 400:
                    raise ProviderBadRequestError(str(data), provider=self.NAME)
                elif resp.status >= 500:
                    raise ProviderServerError(str(data), provider=self.NAME)

                # Parse Anthropic response format
                content_blocks = data.get("content", [])
                text_content = ""
                for block in content_blocks:
                    if block.get("type") == "text":
                        text_content += block.get("text", "")

                usage_raw = data.get("usage", {})
                return LLMResponse(
                    content=text_content,
                    usage=Usage(
                        prompt_tokens=usage_raw.get("input_tokens", 0),
                        completion_tokens=usage_raw.get("output_tokens", 0),
                        total_tokens=usage_raw.get("input_tokens", 0) + usage_raw.get("output_tokens", 0),
                        cached_tokens=usage_raw.get("cache_read_input_tokens", 0),
                    ),
                    provider=self.NAME,
                    model=self.model,
                    finish_reason=data.get("stop_reason", "end_turn"),
                    latency_ms=round(latency, 2),
                )


# ── Opus 4.7-Specific Prompt Rules ──

OPUS47_PROMPT_RULES = """
Opus 4.7 提示词铁律:
1. 不要给"一步步思考"类指令——模型有内部推理scratchpad，显式CoT指令会降性能
2. 用Verification slot: 每个任务末尾加上"验证你的回答，引用原文证据"
3. 更字面化: Opus 4.7不会推断你没要求的内容——把约束写清楚
4. 长文档分析是强项: 充分利用200K上下文窗口
5. 代码审查优先: Opus 4.7在multi-file diff审查上超越其他模型
6. 禁止注入已废弃参数: budget_tokens/temperature限制已变更
7. SKILL.md文件更关键: Opus 4.7更依赖skill files做声音匹配
"""
