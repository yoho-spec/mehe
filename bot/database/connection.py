import motor.motor_asyncio
from config import MONGODB_URI, MONGODB_DB_NAME

_client: motor.motor_asyncio.AsyncIOMotorClient | None = None
_db: motor.motor_asyncio.AsyncIOMotorDatabase | None = None


async def connect_db():
    global _client, _db
    _client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    _db = _client[MONGODB_DB_NAME]
    await _create_indexes()
    print(f"[DB] Connected to MongoDB: {MONGODB_DB_NAME}")


async def close_db():
    global _client
    if _client:
        _client.close()
        print("[DB] MongoDB connection closed")


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _db


async def _create_indexes():
    db = get_db()
    await db.users.create_index("user_id", unique=True)
    await db.sessions.create_index("user_id", unique=True)
    await db.chats.create_index([("user_id", 1), ("chat_id", 1)])
    await db.jobs.create_index([("user_id", 1), ("status", 1)])
    await db.logs.create_index([("user_id", 1), ("timestamp", -1)])
    await db.premium.create_index("user_id", unique=True)
    print("[DB] Indexes ensured")
