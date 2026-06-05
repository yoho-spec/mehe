import traceback
import html
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_USER_IDS
from database import get_db, new_log

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    if isinstance(update, Update) and update.effective_user:
        try:
            db = get_db()
            await db.logs.insert_one(
                new_log(
                    update.effective_user.id,
                    "error",
                    {"error": str(context.error), "traceback": tb_string[:1000]},
                )
            )
        except Exception:
            pass

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "⚠️ <b>An exception was raised while handling an update</b>\n\n"
        f"<pre>update = {html.escape(str(update_str)[:500])}</pre>\n\n"
        f"<pre>{html.escape(tb_string[-1500:])}</pre>"
    )

    for admin_id in ADMIN_USER_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode="HTML",
            )
        except Exception:
            pass

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An error occurred. The admin has been notified."
            )
        except Exception:
            pass
