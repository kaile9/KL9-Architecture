"""Tests for AstrBotLLM adapter — esp. embed() probe semantics (Bug-3)."""
import pytest

from adapter import AstrBotLLM


class _ChatOnlyProvider:
    """Mimics an AstrBot chat-only provider (no embed method)."""
    model_name = "chat-only-mock"

    async def text_chat(self, **kwargs):
        return {"content": "ok"}


class _EmbedCapableProvider:
    model_name = "embed-mock"

    async def text_chat(self, **kwargs):
        return {"content": "ok"}

    async def embed_text(self, texts):
        return [[0.1] * 8 for _ in texts]


class _BrokenEmbedProvider:
    model_name = "broken-mock"

    async def embed_text(self, texts):
        raise RuntimeError("auth failed")


@pytest.mark.asyncio
async def test_embed_raises_when_unsupported():
    """Bug-3: chat-only provider must raise NotImplementedError, not silently
    return [] (which made startup probe always succeed)."""
    llm = AstrBotLLM(_ChatOnlyProvider())
    with pytest.raises(NotImplementedError):
        await llm.embed(["hello"])


@pytest.mark.asyncio
async def test_embed_works_when_supported():
    llm = AstrBotLLM(_EmbedCapableProvider())
    result = await llm.embed(["a", "b"])
    assert len(result) == 2
    assert len(result[0]) == 8


@pytest.mark.asyncio
async def test_embed_propagates_real_errors():
    """Real failures (auth, network, etc.) should propagate so probes can log
    the actual cause — not be swallowed as 'unsupported'."""
    llm = AstrBotLLM(_BrokenEmbedProvider())
    with pytest.raises(RuntimeError, match="auth failed"):
        await llm.embed(["x"])
