import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
TELEGRAM_API_ID = int(os.environ["TELEGRAM_API_ID"])
TELEGRAM_API_HASH = os.environ["TELEGRAM_API_HASH"]

MONGODB_URI = os.environ["MONGODB_URI"]
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "archiver_bot")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

ADMIN_USER_IDS = [
    int(uid.strip())
    for uid in os.environ.get("ADMIN_USER_IDS", "").split(",")
    if uid.strip()
]

MANDATORY_CHANNEL_ID = os.environ.get("MANDATORY_CHANNEL_ID", "")
MANDATORY_CHANNEL_USERNAME = os.environ.get("MANDATORY_CHANNEL_USERNAME", "")
BACKUP_BOT_USERNAME = os.environ.get("BACKUP_BOT_USERNAME", "")

HEALTH_CHECK_PORT = int(os.environ.get("PORT", "8080"))

ADMIN_TEST_MAGIC_COMMAND = os.environ.get("ADMIN_MAGIC_CMD", "/xadminx")

SUBSCRIPTION_CACHE_TTL = 300

FREE_RESTRICTED_LIMIT = 7
