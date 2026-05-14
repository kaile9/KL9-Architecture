"""
9R-2.1 — AstrBot LLM Adapter

Wraps AstrBot's native LLM provider into kl9's LLMProvider interface.
Multi-provider: route/decompose/fold/validate each can use different LLMs.
Supports both OpenAI-compatible and Anthropic-native API through AstrBot.

v2.2: Exposes embed() for SourceRetriever (semantic dedup + local search).
"""
from __future__ import annotations

import asyncio
import logging

from kl9.models import LLMProvider, LLMResponse, Message, Usage, RetryConfig
from kl9.utils.exceptions import ProviderError

logger = logging.getLogger("kl9.adapter")


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
                       timeout: float = 300.0) -> LLMResponse:
        import time
        t0 = time.perf_counter()
        # Retry up to 3 times with exponential backoff for rate limit / transient errors
        last_exc = None
        for attempt in range(4):
            try:
                raw = await self._p.text_chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
                # Extract *actual text content* — never str() the whole object
                if isinstance(raw, dict):
                    text = raw.get("content", "")
                elif hasattr(raw, "completion_text"):
                    text = raw.completion_text
                elif hasattr(raw, "content"):
                    text = raw.content
                else:
                    text = str(raw)
                return LLMResponse(
                    content=text if isinstance(text, str) else str(text),
                    usage=Usage(),
                    provider=self.NAME,
                    model=self.model,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            except Exception as e:
                last_exc = e
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "rate_limit" in err_str or "overloaded" in err_str
                is_timeout = "timeout" in err_str or "timed out" in err_str
                if attempt < 3 and (is_rate_limit or is_timeout):
                    delay = 5 * (attempt + 1)  # 5s, 10s, 15s
                    logger.warning("[KL9][Retry] %s, attempt %d/3, waiting %ds: %s",
                                   "rate limit" if is_rate_limit else "timeout",
                                   attempt + 1, delay, e)
                    await asyncio.sleep(delay)
                else:
                    break
        raise ProviderError(str(last_exc), code="AST-000") from last_exc

    async def chat(self, messages: list[Message], *,
                   temperature: float = 0.3, max_tokens: int = 8192,
                   timeout: float = 300.0) -> LLMResponse:
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

        Resolution order:
          1. Native embed_text() / embed()
          2. AstrBot EmbeddingProvider.get_embeddings()
          3. OpenAI-compatible client.embeddings.create()

        Raises:
            NotImplementedError: when none of the above are available.
        """
        # 1) Native methods (legacy / custom providers)
        embed_fn = getattr(self._p, "embed_text", None) or getattr(self._p, "embed", None)
        if embed_fn and callable(embed_fn):
            result = await embed_fn(texts)
            if result is not None:
                return result

        # 2) AstrBot EmbeddingProvider interface
        get_embeddings_fn = getattr(self._p, "get_embeddings", None)
        if get_embeddings_fn and callable(get_embeddings_fn):
            result = await get_embeddings_fn(texts)
            if result is not None:
                return result

        # 3) OpenAI-compatible client (most cloud providers: SiliconFlow, etc.)
        client = getattr(self._p, "client", None)
        if client is not None and hasattr(client, "embeddings"):
            try:
                model = getattr(self._p, "model_name", None) or getattr(self._p, "model", None) or ""
                resp = await client.embeddings.create(model=model, input=texts)
                if resp and resp.data:
                    return [d.embedding for d in resp.data]
            except Exception:
                pass

        raise NotImplementedError(
            f"provider {getattr(self._p, 'meta_id', type(self._p).__name__)!r} "
            f"does not expose embed_text(), embed(), get_embeddings() or an OpenAI client; "
            f"select an embedding-capable provider (e.g. BAAI/bge-m3) instead"
        )

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)
