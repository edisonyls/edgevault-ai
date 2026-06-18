"""
In-process pub/sub for pushing upload status changes to SSE subscribers.

This is a single-process event bus: the background extraction task publishes 
status changes and the SSE endpoint forwards them to connected clients. It 
works only while the backend runs as a single worker.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

SUBSCRIBER_QUEUE_MAXSIZE = 100


@dataclass(frozen=True, slots=True)
class UploadStatusEvent:
    upload_id: UUID
    status: str


class UploadEventBus:
    def __init__(self) -> None:
        self._subscribers: dict[UUID, set[asyncio.Queue[UploadStatusEvent]]] = defaultdict(
            set
        )

    # Subscribe to upload status changes for a workspace.
    def subscribe(self, workspace_id: UUID) -> asyncio.Queue[UploadStatusEvent]:
        queue: asyncio.Queue[UploadStatusEvent] = asyncio.Queue(
            maxsize=SUBSCRIBER_QUEUE_MAXSIZE
        )
        self._subscribers[workspace_id].add(queue)
        return queue

    # Unsubscribe from upload status changes for a workspace.
    def unsubscribe(self, workspace_id: UUID, queue: asyncio.Queue[UploadStatusEvent]) -> None:
        subscribers = self._subscribers.get(workspace_id)
        if subscribers is None:
            return
        subscribers.discard(queue)
        if not subscribers:
            self._subscribers.pop(workspace_id, None)

    # Publish an upload status event for a workspace.
    def publish(self, workspace_id: UUID, event: UploadStatusEvent) -> None:
        for queue in tuple(self._subscribers.get(workspace_id, ())):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                continue


_event_bus = UploadEventBus()


def get_upload_event_bus() -> UploadEventBus:
    return _event_bus
