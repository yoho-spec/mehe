from telegram import Update
from telegram.ext import ContextTypes
from config import MANDATORY_CHANNEL_USERNAME, BACKUP_BOT_USERNAME, ADMIN_USER_IDS
from services.subscription_service import check_mandatory_subscription, check_backup_bot
from database import get_db, new_user, new_log, utcnow


async def subscription_gate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.effective_user:
        return False

    user = update.effective_user
    user_id = user.id

    if user_id in ADMIN_USER_IDS:
        return True

    db = get_db()
    db_user = await db.users.find_one({"user_id": user_id})

    if not db_user:
        doc = new_user(
            user_id=user_id,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            is_admin=(user_id in ADMIN_USER_IDS),
        )
        await db.users.insert_one(doc)
        db_user = doc

    if db_user.get("is_banned"):
        if update.effective_message:
            await update.effective_message.reply_text(
                "You have been banned from using this bot."
            )
        return False

    if db_user.get("test_mode") == "free":
        pass
    elif db_user.get("test_mode") == "premium":
        pass

    subscribed = await check_mandatory_subscription(context.bot, user_id)
    if not subscribed:
        lines = ["You must subscribe to our channel before using this bot."]
        if MANDATORY_CHANNEL_USERNAME:
            lines.append(f"\n👉 Subscribe here: @{MANDATORY_CHANNEL_USERNAME}")
        if BACKUP_BOT_USERNAME:
            lines.append(f"👉 Also start the backup bot: @{BACKUP_BOT_USERNAME}")
        lines.append("\nOnce done, send /start again.")

        if update.effective_message:
            await update.effective_message.reply_text("\n".join(lines))
        return False

    return True


async def ensure_user_exists(update: Update) -> dict | None:
    if not update.effective_user:
        return None

    user = update.effective_user
    db = get_db()
    db_user = await db.users.find_one({"user_id": user.id})

    if not db_user:
        doc = new_user(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            is_admin=(user.id in ADMIN_USER_IDS),
        )
        await db.users.insert_one(doc)
        return doc

    return db_user
