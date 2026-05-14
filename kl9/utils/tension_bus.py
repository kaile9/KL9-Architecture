"""
9R-2.1 — TensionBus

Async event bus. Rhizome communication fabric. Pub/Sub only.
Subscribers receive fold events, degradation signals, etc.
No central dispatcher — decoupled subscribers.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from ..models import KL9Event


class TensionBus:
    """Simplified Pub/Sub event bus for 9R-2.1."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[KL9Event], Awaitable[None]]]] = defaultdict(list)
        self._event_counts: dict[str, int] = defaultdict(int)
        self._running = False

    def subscribe(self, event_type: str, handler: Callable[[KL9Event], Awaitable[None]]) -> Callable[[], None]:
        self._subscribers[event_type].append(handler)
        def unsubscribe():
            if handler in self._subscribers.get(event_type, []):
                self._subscribers[event_type].remove(handler)
        return unsubscribe

    async def emit(self, event: KL9Event) -> None:
        self._event_counts[event.event_type] = self._event_counts.get(event.event_type, 0) + 1
        handlers = self._subscribers.get(event.event_type, []) + self._subscribers.get("*", [])
        if not handlers:
            return
        results = await asyncio.gather(*[self._safe(h, event) for h in handlers], return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                # Log but don't fail the event chain
                pass

    async def _safe(self, handler, event):
        try:
            await handler(event)
        except Exception:
            pass

    def event_count(self, event_type: str) -> int:
        return self._event_counts.get(event_type, 0)

    def reset(self):
        self._subscribers.clear()
        self._event_counts.clear()


# Global singleton for AstrBot integration
bus = TensionBus()
