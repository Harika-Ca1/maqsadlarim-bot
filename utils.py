"""
utils.py
Umumiy yordamchi funksiyalar: sanalar, progress-bar, matn formatlash.
"""
import datetime
from config import TIMEZONE


def today_str() -> str:
    return datetime.datetime.now(TIMEZONE).date().isoformat()


def now_local() -> datetime.datetime:
    return datetime.datetime.now(TIMEZONE)


def days_since(date_str: str) -> int:
    if not date_str:
        return 9999
    d = datetime.date.fromisoformat(date_str)
    today = datetime.datetime.now(TIMEZONE).date()
    return (today - d).days


def progress_bar(percent: int, length: int = 10) -> str:
    filled = round(length * percent / 100)
    return "█" * filled + "░" * (length - filled) + f"  {percent}%"


def status_emoji(status: str) -> str:
    return {
        "done": "✅",
        "partial": "🟡",
        "failed": "❌",
        "pending": "⬜",
    }.get(status, "⬜")


FAIL_REASONS = {
    "time": "⏰ Vaqt yetmadi",
    "tired": "😴 Charchadim",
    "distracted": "📱 Chalg'idim",
    "too_big": "❓ Vazifa juda katta edi",
    "other": "🔄 Boshqa sabab",
}


def validate_time_format(text: str) -> bool:
    try:
        parts = text.strip().split(":")
        if len(parts) != 2:
            return False
        h, m = int(parts[0]), int(parts[1])
        return 0 <= h <= 23 and 0 <= m <= 59
    except ValueError:
        return False


def week_ago_str() -> str:
    d = datetime.datetime.now(TIMEZONE).date() - datetime.timedelta(days=7)
    return d.isoformat()


def month_ago_str() -> str:
    d = datetime.datetime.now(TIMEZONE).date() - datetime.timedelta(days=30)
    return d.isoformat()


def percent(part: int, total: int) -> int:
    if total == 0:
        return 0
    return round(part / total * 100)
