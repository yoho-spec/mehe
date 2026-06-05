import re
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def format_chat_id(chat_id: int | str) -> str:
    s = str(chat_id)
    if not s.startswith("-100") and s.lstrip("-").isdigit():
        if s.startswith("-"):
            return f"-100{s[1:]}"
    return s


def extract_chat_id(text: str) -> int | None:
    text = text.strip()
    if text.lstrip("-").isdigit():
        return int(text)
    match = re.search(r"t\.me/c/(\d+)", text)
    if match:
        return int(f"-100{match.group(1)}")
    return None


def chunk_list(lst: list, size: int) -> list[list]:
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def is_admin(user_id: int) -> bool:
    from config import ADMIN_USER_IDS
    return user_id in ADMIN_USER_IDS


def truncate(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def human_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def mention_user(user_id: int, first_name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{first_name}</a>'
