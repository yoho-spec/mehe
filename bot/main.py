import asyncio
import logging
import signal
import sys

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from config import BOT_TOKEN, HEALTH_CHECK_PORT
from database import connect_db, close_db
from services import connect_redis, close_redis
from health import start_health_server
from handlers import (
    start_handler,
    help_handler,
    status_handler,
    menu_callback_handler,
    admintest_handler,
    addpremium_handler,
    removepremium_handler,
    banuser_handler,
    unbanuser_handler,
    stats_handler,
    broadcast_handler,
    error_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("status", status_handler))

    app.add_handler(CommandHandler("admintest", admintest_handler))
    app.add_handler(CommandHandler("addpremium", addpremium_handler))
    app.add_handler(CommandHandler("removepremium", removepremium_handler))
    app.add_handler(CommandHandler("banuser", banuser_handler))
    app.add_handler(CommandHandler("unbanuser", unbanuser_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("broadcast", broadcast_handler))

    app.add_handler(CallbackQueryHandler(menu_callback_handler, pattern=r"^menu:"))

    app.add_error_handler(error_handler)

    return app


async def main() -> None:
    logger.info("Starting Archiver Bot...")

    await connect_db()
    await connect_redis()

    health_runner = await start_health_server(HEALTH_CHECK_PORT)

    app = build_application()

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    logger.info("Bot starting in polling mode...")
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await stop_event.wait()
        logger.info("Shutting down...")
        await app.updater.stop()
        await app.stop()

    await health_runner.cleanup()
    await close_redis()
    await close_db()
    logger.info("Bot stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
