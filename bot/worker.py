import asyncio
import json
import logging
import signal
import sys

from config import BOT_TOKEN
from database import connect_db, close_db
from services import connect_redis, close_redis, dequeue_job, get_redis
from database import get_db, utcnow

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

QUEUES = [
    "jobs:forward",
    "jobs:dedupe",
    "jobs:download",
]

RUNNING = True


async def process_forward_job(job: dict) -> None:
    logger.info(f"[Worker] forward job for user {job.get('user_id')}: {job}")


async def process_dedupe_job(job: dict) -> None:
    logger.info(f"[Worker] dedupe job for user {job.get('user_id')}: {job}")


async def process_download_job(job: dict) -> None:
    logger.info(f"[Worker] download job for user {job.get('user_id')}: {job}")


HANDLERS = {
    "jobs:forward": process_forward_job,
    "jobs:dedupe": process_dedupe_job,
    "jobs:download": process_download_job,
}


async def run_worker() -> None:
    global RUNNING
    logger.info("[Worker] Starting job processor...")
    await connect_db()
    await connect_redis()

    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()

    def _signal_handler():
        logger.info("[Worker] Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    logger.info(f"[Worker] Listening on queues: {QUEUES}")

    while not stop_event.is_set():
        try:
            r = get_redis()
            result = await r.blpop(QUEUES, timeout=5)
            if result is None:
                continue

            queue_name, raw = result
            job = json.loads(raw)
            logger.info(f"[Worker] Dequeued job from {queue_name}: {job.get('job_id', '?')}")

            handler = HANDLERS.get(queue_name)
            if handler:
                try:
                    db = get_db()
                    await db.jobs.update_one(
                        {"_id": job.get("_id")},
                        {"$set": {"status": "running", "updated_at": utcnow()}},
                    )
                    await handler(job)
                    await db.jobs.update_one(
                        {"_id": job.get("_id")},
                        {"$set": {"status": "done", "updated_at": utcnow()}},
                    )
                except Exception as e:
                    logger.error(f"[Worker] Job failed: {e}", exc_info=True)
                    db = get_db()
                    await db.jobs.update_one(
                        {"_id": job.get("_id")},
                        {"$set": {"status": "failed", "error": str(e), "updated_at": utcnow()}},
                    )
            else:
                logger.warning(f"[Worker] No handler for queue: {queue_name}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[Worker] Unexpected error: {e}", exc_info=True)
            await asyncio.sleep(2)

    await close_redis()
    await close_db()
    logger.info("[Worker] Stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(run_worker())
