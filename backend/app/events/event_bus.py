import logging
from typing import Callable, List, Dict
from app.events.event_model import SecurityEvent, EventType

logger = logging.getLogger("event_bus")

class EventBus:
    """
    Lightweight in-process event bus for routing security and transaction events
    to risk evaluators, audit loggers, and alert dispatchers.
    """
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[SecurityEvent], None]]] = {}
        self._global_subscribers: List[Callable[[SecurityEvent], None]] = []

    def subscribe(self, event_type: EventType, handler: Callable[[SecurityEvent], None]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[SecurityEvent], None]):
        self._global_subscribers.append(handler)

    def publish(self, event: SecurityEvent):
        # Notify specific event handlers
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error executing event handler for {event.event_type}: {e}")

        # Notify global handlers
        for handler in self._global_subscribers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error executing global event handler: {e}")

event_bus = EventBus()
