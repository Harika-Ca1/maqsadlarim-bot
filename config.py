"""
config.py
Muhit o'zgaruvchilarini (.env) yuklash va umumiy sozlamalarni saqlash.
"""
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi! Loyiha papkasida .env fayl yarating va "
        "unga BOT_TOKEN=... qatorini qo'shing (.env.example ga qarang)."
    )

# Vaqt mintaqasi (barcha eslatmalar shu bo'yicha hisoblanadi)
TIMEZONE_NAME = os.getenv("TIMEZONE", "Asia/Tashkent")
TIMEZONE = ZoneInfo(TIMEZONE_NAME)

# Ma'lumotlar bazasi fayli
DB_PATH = os.getenv("DB_PATH", "maqsadlarim.db")

# Faolsizlik nazorati necha kunda bir marta tekshiriladi (soat:daqiqa, local TZ)
INACTIVITY_CHECK_HOUR = int(os.getenv("INACTIVITY_CHECK_HOUR", "12"))
INACTIVITY_CHECK_MINUTE = int(os.getenv("INACTIVITY_CHECK_MINUTE", "0"))
