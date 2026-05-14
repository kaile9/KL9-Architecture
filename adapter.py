"""
9R-2.1 — AstrBot LLM Adapter

Wraps AstrBot's native LLM provider into kl9's LLMProvider interface.
Multi-provider: route/decompose/fold/validate each can use different LLMs.
Supports both OpenAI-compatible and Anthropic-native API through AstrBot.

v2.2: Exposes embed() for SourceRetriever (semantic dedup + local search).
"""
from __future__ import annotations

from kl9.models import LLMProvider, LLMResponse, Message, Usage, RetryConfig
from kl9.utils.exceptions import ProviderError


class AstrBotLLM(LLMProvider):
    """Wrap AstrBot provider into kl9 interface."""

    NAME = "astrbot_wrapped"
    MAX_OUTPUT_TOKENS = 32_768

    def __init__(self, astrbot_provider):
        self._p = astrbot_provider
        name = getattr(astrbot_provider, 'model_name', 'unknown')
        super().__init__(api_key="", model=name)

    async def complete(self, system_prompt: str, user_prompt: str, *,
                       temperature: float = 0.3, max_tokens: int = 8192,
                       timeout: float = 120.0) -> LLMResponse:
        import time
        t0 = time.perf_counter()
        try:
            raw = await self._p.text_chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            return LLMResponse(
                content=raw.get("content", "") if isinstance(raw, dict) else str(raw),
                usage=Usage(),
                provider=self.NAME,
                model=self.model,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        except Exception as e:
            raise ProviderError(str(e), code="AST-000") from e

    async def chat(self, messages: list[Message], *,
                   temperature: float = 0.3, max_tokens: int = 8192,
                   timeout: float = 120.0) -> LLMResponse:
        system = ""
        user = ""
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                user = m.content
        return await self.complete(system_prompt=system, user_prompt=user,
                                   temperature=temperature, max_tokens=max_tokens, timeout=timeout)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts via the wrapped provider.

        Raises:
            NotImplementedError: when the underlying AstrBot provider does not
                expose an embedding method (e.g. wrapping a chat-only LLM).
                The plugin's startup probe relies on this to detect mis-config
                rather than silently falling back to URL-only dedup.

        Other exceptions are re-raised so probes can show the real reason
        (auth error, network, etc.).
        """
        embed_fn = getattr(self._p, "embed_text", None) or getattr(self._p, "embed", None)
        if not (embed_fn and callable(embed_fn)):
            raise NotImplementedError(
                f"provider {getattr(self._p, 'meta_id', type(self._p).__name__)!r} "
                f"does not expose embed_text() or embed(); "
                f"select an embedding-capable provider (e.g. BAAI/bge-m3) instead"
            )
        result = await embed_fn(texts)
        if result is None:
            raise NotImplementedError(
                f"provider returned None from embed; treating as unsupported"
            )
        return result

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)
