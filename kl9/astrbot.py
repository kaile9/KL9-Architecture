"""
9R-2.1 — AstrBot Adapter

Connects the KL9 system to the AstrBot container.
Receives queries from AstrBot message pipeline, returns formatted responses.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from .models import AggregatedOutput, LLMProvider
from .system import KL9System


class AstrBotAdapter:
    """Adapter for AstrBot integration.

    Usage (from AstrBot skill):
        from .astrbot import AstrBotAdapter
        adapter = AstrBotAdapter(provider)
        await adapter.initialize()
        response = await adapter.handle_query(user_message, session_id)

    Formatting:
        - QUICK: plain text
        - STANDARD: markdown with constitutional markers
        - DEEP: markdown with fold metadata block
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.kl9: Optional[KL9System] = None
        self._ready = False

    async def initialize(self) -> None:
        """Initialize the KL9 system."""
        self.kl9 = KL9System(self.llm)
        self._ready = True

    async def handle_query(
        self,
        message: str,
        session_id: str = "",
        user_id: str = "",
    ) -> str:
        """Handle a user query through the full pipeline.

        Returns formatted string for AstrBot to send.
        """
        if not self._ready or self.kl9 is None:
            await self.initialize()

        assert self.kl9 is not None

        # Detect force prefix
        force_depth = None
        q = message.strip()
        if q.startswith("/deep "):
            force_depth = "deep"
            q = q[6:]
        elif q.startswith("/quick "):
            force_depth = "quick"
            q = q[7:]
        elif q.startswith("/standard "):
            force_depth = "standard"
            q = q[10:]

        result = await self.kl9.process(q, session_id=session_id, force_depth=force_depth)

        return self._format(result)

    def _format(self, result: AggregatedOutput) -> str:
        """Format output for AstrBot delivery."""
        parts = [result.content]

        # Append fold metadata
        if result.fold_depth > 1:
            parts.append(f"\n---\n*折叠深度: {result.fold_depth} | "
                         f"质量: {result.quality.grade if result.quality else 'N/A'}*")

            if result.quality and result.quality.constitutional_violations:
                parts.append("*⚠ 宪法违例: " + ", ".join(result.quality.constitutional_violations) + "*")

        if result.constitutional_warning:
            parts.append("*⚠ 质量警告: 含宪法违例*")

        return "\n".join(parts)


# Singleton for AstrBot skill use
adapter: Optional[AstrBotAdapter] = None


async def get_adapter(llm: LLMProvider) -> AstrBotAdapter:
    global adapter
    if adapter is None:
        adapter = AstrBotAdapter(llm)
        await adapter.initialize()
    return adapter
