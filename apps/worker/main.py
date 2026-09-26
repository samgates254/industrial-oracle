"""Background worker entrypoint for Industrial Oracle outbox event processing."""

import asyncio
import logging
import signal
import sys

from industrial_oracle.integrations.application.worker import OutboxWorker
from industrial_oracle.integrations.infrastructure.publisher import (
    DefaultWebhookAdapter,
    InternalEventPublisher,
)
from industrial_oracle.integrations.infrastructure.repository import (
    consumption_repository,
    outbox_repository,
    webhook_repository,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("industrial_oracle.worker")


def build_worker() -> OutboxWorker:
    """Instantiates an OutboxWorker wired with internal publisher and webhook adapter."""
    webhook_adapter = DefaultWebhookAdapter()
    publisher = InternalEventPublisher(
        consumption_repo=consumption_repository,
        webhook_repo=webhook_repository,
        webhook_adapter=webhook_adapter,
    )
    return OutboxWorker(
        outbox_repo=outbox_repository,
        publisher=publisher,
        batch_size=20,
        lease_seconds=30,
    )


async def main() -> None:
    """Worker process main loop."""
    worker = build_worker()
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: stop_event.set())
        except NotImplementedError:
            # On platforms where signal handlers aren't supported in asyncio
            pass

    logger.info("Initializing Industrial Oracle Outbox Worker...")
    try:
        await worker.run_forever(poll_interval=1.0, stop_event=stop_event)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker process terminating...")
    finally:
        worker.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
