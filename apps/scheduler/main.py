"""Industrial Oracle Scheduler Process."""

import asyncio
import logging
import signal
from industrial_oracle.core.config import settings
from industrial_oracle.core.logging import setup_logging, logger

setup_logging(log_level=settings.LOG_LEVEL, json_format=(settings.LOG_FORMAT == "json"))


class JobScheduler:
    """Schedules and triggers recurring cron-style jobs."""

    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        self.running = True
        logger.info("Scheduler started.")
        while self.running:
            try:
                await asyncio.sleep(10.0)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Scheduler error: %s", exc, exc_info=True)

    async def stop(self) -> None:
        logger.info("Stopping scheduler...")
        self.running = False
        logger.info("Scheduler stopped.")


scheduler = JobScheduler()


def handle_exit_signal(sig, frame):
    logger.info("Scheduler received signal %s, initiating shutdown...", sig)
    asyncio.create_task(scheduler.stop())


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)
    try:
        asyncio.run(scheduler.start())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler process exited.")
