from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


USER_SCHEMA = {
    "user_id": int,
    "username": str,
    "first_name": str,
    "last_name": str,
    "is_premium": bool,
    "is_admin": bool,
    "is_banned": bool,
    "subscribed_to_channel": bool,
    "joined_backup_bot": bool,
    "test_mode": str,
    "created_at": datetime,
    "updated_at": datetime,
}

SESSION_SCHEMA = {
    "user_id": int,
    "phone": str,
    "session_string": str,
    "is_active": bool,
    "created_at": datetime,
    "updated_at": datetime,
}

CHAT_SCHEMA = {
    "user_id": int,
    "chat_id": int,
    "chat_name": str,
    "chat_type": str,
    "access_hash": int,
    "topic_id": int,
    "is_source": bool,
    "is_destination": bool,
    "always_archive": bool,
    "created_at": datetime,
}

JOB_SCHEMA = {
    "user_id": int,
    "job_type": str,
    "status": str,
    "config": dict,
    "result": dict,
    "error": str,
    "created_at": datetime,
    "updated_at": datetime,
}

LOG_SCHEMA = {
    "user_id": int,
    "action": str,
    "details": dict,
    "timestamp": datetime,
}

PREMIUM_SCHEMA = {
    "user_id": int,
    "granted_by": int,
    "granted_at": datetime,
    "expires_at": datetime,
    "is_active": bool,
    "restricted_count": int,
}


def new_user(user_id: int, username: str, first_name: str, last_name: str = "", is_admin: bool = False) -> dict:
    now = utcnow()
    return {
        "user_id": user_id,
        "username": username or "",
        "first_name": first_name or "",
        "last_name": last_name or "",
        "is_premium": False,
        "is_admin": is_admin,
        "is_banned": False,
        "subscribed_to_channel": False,
        "joined_backup_bot": False,
        "test_mode": None,
        "created_at": now,
        "updated_at": now,
    }


def new_job(user_id: int, job_type: str, config: dict) -> dict:
    now = utcnow()
    return {
        "user_id": user_id,
        "job_type": job_type,
        "status": "pending",
        "config": config,
        "result": {},
        "error": None,
        "created_at": now,
        "updated_at": now,
    }


def new_log(user_id: int, action: str, details: dict | None = None) -> dict:
    return {
        "user_id": user_id,
        "action": action,
        "details": details or {},
        "timestamp": utcnow(),
    }


def new_premium_record(user_id: int, granted_by: int, expires_at: datetime | None = None) -> dict:
    now = utcnow()
    return {
        "user_id": user_id,
        "granted_by": granted_by,
        "granted_at": now,
        "expires_at": expires_at,
        "is_active": True,
        "restricted_count": 0,
    }
