from telegram import Bot
from telegram.error import TelegramError
from config import MANDATORY_CHANNEL_ID, SUBSCRIPTION_CACHE_TTL
from services.redis_service import cache_get, cache_set
from database import get_db, new_log


async def check_mandatory_subscription(bot: Bot, user_id: int) -> bool:
    if not MANDATORY_CHANNEL_ID:
        return True

    cache_key = f"sub:{user_id}:{MANDATORY_CHANNEL_ID}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached == "1"

    try:
        member = await bot.get_chat_member(
            chat_id=MANDATORY_CHANNEL_ID,
            user_id=user_id,
        )
        is_member = member.status not in ("left", "kicked", "banned")
        await cache_set(cache_key, "1" if is_member else "0", ttl=SUBSCRIPTION_CACHE_TTL)

        db = get_db()
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"subscribed_to_channel": is_member}},
        )
        return is_member
    except TelegramError:
        return False


async def check_backup_bot(user_id: int) -> bool:
    db = get_db()
    user = await db.users.find_one({"user_id": user_id}, {"joined_backup_bot": 1})
    if not user:
        return False
    return user.get("joined_backup_bot", False)


async def invalidate_subscription_cache(user_id: int) -> None:
    from services.redis_service import cache_delete
    cache_key = f"sub:{user_id}:{MANDATORY_CHANNEL_ID}"
    await cache_delete(cache_key)
