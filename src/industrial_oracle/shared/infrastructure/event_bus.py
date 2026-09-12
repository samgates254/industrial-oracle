"""In-memory and async event bus for domain event dispatching."""

import asyncio
from collections import defaultdict
import logging
from typing import Callable, Coroutine, Dict, List

from industrial_oracle.shared.domain.events import DomainEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent], Coroutine[None, None, None]]


class EventBus:
    """Dispatches domain events to registered internal handlers."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribes an async handler to a specific event type."""
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed %s to event %s", handler.__name__, event_type)

    async def publish(self, event: DomainEvent) -> None:
        """Publishes an event to all matching subscribers."""
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            logger.debug("No handlers registered for event %s", event.event_type)
            return

        for handler in handlers:
            try:
                await handler(event)
            except Exception as exc:
                logger.error(
                    "Error executing handler %s for event %s: %s",
                    handler.__name__,
                    event.event_type,
                    exc,
                    exc_info=True,
                )

    async def publish_all(self, events: List[DomainEvent]) -> None:
        """Publishes a batch of events sequentially."""
        for ev in events:
            await self.publish(ev)


# Global event bus singleton for monolith internal coordination
event_bus = EventBus()
