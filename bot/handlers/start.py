from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from middleware import subscription_gate, ensure_user_exists
from database import get_db, new_log
from config import MANDATORY_CHANNEL_USERNAME, BACKUP_BOT_USERNAME


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message or not update.effective_user:
        return

    user = update.effective_user
    db = get_db()

    db_user = await ensure_user_exists(update)

    allowed = await subscription_gate(update, context)
    if not allowed:
        return

    await db.logs.insert_one(new_log(user.id, "start"))

    name = user.first_name or "there"

    keyboard = [
        [
            InlineKeyboardButton("📦 My Chats", callback_data="menu:mychats"),
            InlineKeyboardButton("⚙️ Settings", callback_data="menu:settings"),
        ],
        [
            InlineKeyboardButton("🔗 Connect Account", callback_data="menu:connect"),
            InlineKeyboardButton("📊 Status", callback_data="menu:status"),
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="menu:premium"),
            InlineKeyboardButton("❓ Help", callback_data="menu:help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 Hey {name}! Welcome to <b>Archiver Bot</b>.\n\n"
        "I can help you:\n"
        "• 📁 Archive and forward messages from any chat\n"
        "• 🔍 Remove duplicate files across channels\n"
        "• 🛡 Manage group joins with Q&A gates\n"
        "• 🤖 Moderate groups with smart tools\n"
        "• 🔎 Search your Telegram history\n\n"
        "Use the menu below to get started.\n"
        "Type /help anytime for a command list."
    )

    await update.effective_message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return

    allowed = await subscription_gate(update, context)
    if not allowed:
        return

    help_text = (
        "<b>📖 Archiver Bot — Command Reference</b>\n\n"
        "<b>General</b>\n"
        "/start — Open the main menu\n"
        "/help — Show this help message\n"
        "/status — Your account status\n\n"
        "<b>Account</b>\n"
        "/connect — Log in with your Telegram account\n"
        "/disconnect — Log out your account\n"
        "/mychats — List all your chats (requires login)\n\n"
        "<b>Archiving</b>\n"
        "/setsource — Set a source chat to archive from\n"
        "/setdest — Set a destination chat/topic\n"
        "/forward — Start forwarding messages\n"
        "/forwardold — Forward historical messages\n"
        "/stop — Stop active forwarding\n\n"
        "<b>Duplicates</b>\n"
        "/dedupe — Run duplicate scan on a channel\n"
        "/dedupeall — Scan multiple chats at once\n\n"
        "<b>Group Tools</b>\n"
        "/joinsetup — Configure join request gating\n"
        "/setquestion — Set Q&A for new members\n"
        "/banlist — Manage the auto-ban list\n"
        "/welcome — Configure welcome messages\n\n"
        "<b>Logs</b>\n"
        "/logs — View recent activity logs\n\n"
        "Type /start to open the interactive menu."
    )

    await update.effective_message.reply_text(help_text, parse_mode="HTML")


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message or not update.effective_user:
        return

    allowed = await subscription_gate(update, context)
    if not allowed:
        return

    user_id = update.effective_user.id
    db = get_db()
    db_user = await db.users.find_one({"user_id": user_id})
    session = await db.sessions.find_one({"user_id": user_id, "is_active": True})
    premium = await db.premium.find_one({"user_id": user_id, "is_active": True})

    account_status = "✅ Connected" if session else "❌ Not connected"
    premium_status = "💎 Premium" if premium or (db_user and db_user.get("is_premium")) else "🆓 Free"
    sub_status = "✅ Subscribed" if db_user and db_user.get("subscribed_to_channel") else "❌ Not subscribed"

    restricted_used = premium.get("restricted_count", 0) if premium else 0
    restricted_left = "Unlimited" if premium else f"{max(0, 7 - restricted_used)} remaining"

    text = (
        "<b>📊 Your Account Status</b>\n\n"
        f"👤 <b>Account login:</b> {account_status}\n"
        f"💎 <b>Plan:</b> {premium_status}\n"
        f"📣 <b>Channel sub:</b> {sub_status}\n"
        f"🔒 <b>Restricted content:</b> {restricted_left}\n"
    )

    await update.effective_message.reply_text(text, parse_mode="HTML")


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    action = query.data.replace("menu:", "")

    if action == "help":
        help_text = (
            "<b>📖 Archiver Bot — Command Reference</b>\n\n"
            "Use /help for the full command list.\n"
            "Use /start to return to the main menu."
        )
        await query.edit_message_text(help_text, parse_mode="HTML")

    elif action == "status":
        fake_update = update
        await status_handler(fake_update, context)

    elif action == "premium":
        text = (
            "💎 <b>Premium Features</b>\n\n"
            "• Cryptographic hash duplicate detection\n"
            "• Unlimited restricted content forwarding\n"
            "• Priority job queue\n\n"
            "Contact an admin to get premium access."
        )
        await query.edit_message_text(text, parse_mode="HTML")

    elif action == "connect":
        await query.edit_message_text(
            "Use /connect to log in with your Telegram account.\n"
            "This unlocks forwarding, history search, and more."
        )

    elif action == "mychats":
        await query.edit_message_text(
            "Use /mychats to list all your Telegram chats.\n"
            "Requires /connect first."
        )

    elif action == "settings":
        await query.edit_message_text(
            "⚙️ Settings coming in Part 3.\n"
            "Use /start to go back."
        )
