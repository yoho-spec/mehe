from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_USER_IDS
from database import get_db, new_log, new_premium_record, utcnow
from middleware import subscription_gate


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return
        if update.effective_user.id not in ADMIN_USER_IDS:
            if update.effective_message:
                await update.effective_message.reply_text("⛔ Admin only.")
            return
        return await func(update, context)
    wrapper.__name__ = func.__name__
    return wrapper


@admin_only
async def admintest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    args = context.args
    if not args or args[0] not in ("premium", "free", "off"):
        await update.effective_message.reply_text(
            "Usage: /admintest <premium|free|off>\n\n"
            "• premium — simulate premium user experience\n"
            "• free — simulate free user experience\n"
            "• off — return to admin mode"
        )
        return

    mode = args[0]
    user_id = update.effective_user.id
    db = get_db()

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"test_mode": None if mode == "off" else mode, "updated_at": utcnow()}},
    )
    await db.logs.insert_one(new_log(user_id, "admintest", {"mode": mode}))

    if mode == "off":
        await update.effective_message.reply_text("✅ Returned to full admin mode.")
    else:
        await update.effective_message.reply_text(
            f"🔬 Test mode: <b>{mode}</b>\n"
            "You are now simulating a <b>{mode}</b> user. "
            "All commands will behave as if you are that user type.\n"
            "Use /admintest off to exit.".replace("{mode}", mode),
            parse_mode="HTML",
        )


@admin_only
async def addpremium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    args = context.args
    if not args:
        await update.effective_message.reply_text(
            "Usage: /addpremium <user_id or @username>"
        )
        return

    db = get_db()
    target = args[0].lstrip("@")

    if target.isdigit():
        target_user = await db.users.find_one({"user_id": int(target)})
    else:
        target_user = await db.users.find_one({"username": target})

    if not target_user:
        await update.effective_message.reply_text(
            "❌ User not found. They must have used the bot at least once."
        )
        return

    target_id = target_user["user_id"]
    admin_id = update.effective_user.id

    existing = await db.premium.find_one({"user_id": target_id})
    if existing and existing.get("is_active"):
        await update.effective_message.reply_text(
            f"ℹ️ User {target_id} already has premium."
        )
        return

    record = new_premium_record(user_id=target_id, granted_by=admin_id)
    await db.premium.update_one(
        {"user_id": target_id},
        {"$set": record},
        upsert=True,
    )
    await db.users.update_one(
        {"user_id": target_id},
        {"$set": {"is_premium": True, "updated_at": utcnow()}},
    )
    await db.logs.insert_one(
        new_log(admin_id, "addpremium", {"target_user_id": target_id})
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                "🎉 <b>You've been granted Premium!</b>\n\n"
                "You now have access to:\n"
                "• Cryptographic hash duplicate detection\n"
                "• Unlimited restricted content forwarding\n"
                "• Priority job queue\n\n"
                "Thank you for being part of Archiver Bot! ✨"
            ),
            parse_mode="HTML",
        )
        notify_status = "User has been notified."
    except Exception:
        notify_status = "⚠️ Could not notify the user (they may not have started the bot)."

    await update.effective_message.reply_text(
        f"✅ Premium granted to user <code>{target_id}</code>.\n{notify_status}",
        parse_mode="HTML",
    )


@admin_only
async def removepremium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    args = context.args
    if not args:
        await update.effective_message.reply_text(
            "Usage: /removepremium <user_id or @username>"
        )
        return

    db = get_db()
    target = args[0].lstrip("@")

    if target.isdigit():
        target_user = await db.users.find_one({"user_id": int(target)})
    else:
        target_user = await db.users.find_one({"username": target})

    if not target_user:
        await update.effective_message.reply_text("❌ User not found.")
        return

    target_id = target_user["user_id"]
    admin_id = update.effective_user.id

    await db.premium.update_one(
        {"user_id": target_id},
        {"$set": {"is_active": False}},
    )
    await db.users.update_one(
        {"user_id": target_id},
        {"$set": {"is_premium": False, "updated_at": utcnow()}},
    )
    await db.logs.insert_one(
        new_log(admin_id, "removepremium", {"target_user_id": target_id})
    )
    await update.effective_message.reply_text(
        f"✅ Premium removed from user <code>{target_id}</code>.",
        parse_mode="HTML",
    )


@admin_only
async def banuser_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    args = context.args
    if not args:
        await update.effective_message.reply_text("Usage: /banuser <user_id>")
        return

    db = get_db()
    try:
        target_id = int(args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ Provide a numeric user ID.")
        return

    await db.users.update_one(
        {"user_id": target_id},
        {"$set": {"is_banned": True, "updated_at": utcnow()}},
    )
    await db.logs.insert_one(
        new_log(update.effective_user.id, "banuser", {"target_user_id": target_id})
    )
    await update.effective_message.reply_text(
        f"✅ User <code>{target_id}</code> has been banned.",
        parse_mode="HTML",
    )


@admin_only
async def unbanuser_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    args = context.args
    if not args:
        await update.effective_message.reply_text("Usage: /unbanuser <user_id>")
        return

    db = get_db()
    try:
        target_id = int(args[0])
    except ValueError:
        await update.effective_message.reply_text("❌ Provide a numeric user ID.")
        return

    await db.users.update_one(
        {"user_id": target_id},
        {"$set": {"is_banned": False, "updated_at": utcnow()}},
    )
    await db.logs.insert_one(
        new_log(update.effective_user.id, "unbanuser", {"target_user_id": target_id})
    )
    await update.effective_message.reply_text(
        f"✅ User <code>{target_id}</code> has been unbanned.",
        parse_mode="HTML",
    )


@admin_only
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    db = get_db()
    total_users = await db.users.count_documents({})
    premium_users = await db.users.count_documents({"is_premium": True})
    active_sessions = await db.sessions.count_documents({"is_active": True})
    banned_users = await db.users.count_documents({"is_banned": True})
    total_jobs = await db.jobs.count_documents({})

    text = (
        "<b>📈 Bot Statistics</b>\n\n"
        f"👤 Total users: <b>{total_users}</b>\n"
        f"💎 Premium users: <b>{premium_users}</b>\n"
        f"🔗 Active sessions: <b>{active_sessions}</b>\n"
        f"🚫 Banned users: <b>{banned_users}</b>\n"
        f"⚙️ Total jobs: <b>{total_jobs}</b>"
    )
    await update.effective_message.reply_text(text, parse_mode="HTML")


@admin_only
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    if not update.effective_message.reply_to_message:
        await update.effective_message.reply_text(
            "Reply to a message with /broadcast to send it to all users."
        )
        return

    msg = update.effective_message.reply_to_message
    db = get_db()
    users = db.users.find({"is_banned": {"$ne": True}}, {"user_id": 1})

    sent = 0
    failed = 0
    async for user in users:
        try:
            await context.bot.copy_message(
                chat_id=user["user_id"],
                from_chat_id=msg.chat_id,
                message_id=msg.message_id,
            )
            sent += 1
        except Exception:
            failed += 1

    await update.effective_message.reply_text(
        f"📢 Broadcast done.\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )
