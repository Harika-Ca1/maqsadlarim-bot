"""
handlers/jobs.py
JobQueue orqali ishlaydigan fon vazifalar:
- Har bir foydalanuvchi uchun ertalabki reja eslatmasi
- Har bir foydalanuvchi uchun kechki check-in eslatmasi
- Kunlik faolsizlik nazorati (3 kun / 7 kun)
"""
import datetime

from telegram.ext import Application, ContextTypes

import database as db
from keyboards import main_menu_keyboard
from utils import today_str
from config import TIMEZONE, INACTIVITY_CHECK_HOUR, INACTIVITY_CHECK_MINUTE

MORNING_JOB_PREFIX = "morning_"
EVENING_JOB_PREFIX = "evening_"
INACTIVITY_JOB_NAME = "inactivity_check"


def _parse_time(time_str: str) -> datetime.time:
    h, m = time_str.split(":")
    return datetime.time(hour=int(h), minute=int(m), tzinfo=TIMEZONE)


async def morning_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    telegram_id = context.job.data
    user = await db.get_user_by_telegram_id(telegram_id)
    if not user or not user["reminders_on"]:
        return
    tasks = await db.get_tasks_by_date(user["id"], today_str())
    if tasks:
        lines = [f"🌅 Xayrli tong! Bugungi rejangizda {len(tasks)} ta vazifa bor:\n"]
        for t in tasks:
            lines.append(f"• {t['title']}")
        text = "\n".join(lines)
    else:
        text = (
            "🌅 Xayrli tong! Bugun uchun hali vazifa belgilanmagan.\n\n"
            "\"🎯 Maqsadlarim\" bo'limiga kirib, bugungi kichik qadamni tanlang!"
        )
    try:
        await context.bot.send_message(telegram_id, text, reply_markup=main_menu_keyboard())
    except Exception:
        pass


async def evening_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    telegram_id = context.job.data
    user = await db.get_user_by_telegram_id(telegram_id)
    if not user or not user["reminders_on"]:
        return
    text = (
        "🌙 Kechki vaqt keldi. Bugun rejangiz qanday o'tdi?\n\n"
        "\"📝 Bugungi Check-in\" tugmasini bosib, kunni yakunlang."
    )
    try:
        await context.bot.send_message(telegram_id, text, reply_markup=main_menu_keyboard())
    except Exception:
        pass


def _remove_jobs(app: Application, name: str):
    if app.job_queue is None:
        return
    for job in app.job_queue.get_jobs_by_name(name):
        job.schedule_removal()


def reschedule_user_jobs(app: Application, user: dict):
    """Foydalanuvchining eslatma job'larini o'chirib, yangi vaqt bilan qayta qo'yadi."""
    if app.job_queue is None:
        return
    telegram_id = user["telegram_id"]
    morning_name = f"{MORNING_JOB_PREFIX}{telegram_id}"
    evening_name = f"{EVENING_JOB_PREFIX}{telegram_id}"
    _remove_jobs(app, morning_name)
    _remove_jobs(app, evening_name)

    if not user["reminders_on"]:
        return

    app.job_queue.run_daily(
        morning_reminder_job, _parse_time(user["morning_time"]),
        data=telegram_id, name=morning_name,
    )
    app.job_queue.run_daily(
        evening_reminder_job, _parse_time(user["evening_time"]),
        data=telegram_id, name=evening_name,
    )


async def schedule_all_users_jobs(app: Application):
    """Bot ishga tushganda barcha mavjud foydalanuvchilar uchun eslatmalarni qo'yish."""
    users = await db.get_all_users()
    for user in users:
        reschedule_user_jobs(app, user)


async def inactivity_check_job(context: ContextTypes.DEFAULT_TYPE):
    """Har kuni bir marta: 3 kun va 7 kun faolsizlikni tekshiradi."""
    users = await db.get_all_users()
    today = datetime.datetime.now(TIMEZONE).date()

    for user in users:
        last_active = user["last_active"]
        if not last_active:
            continue
        try:
            last_date = datetime.date.fromisoformat(last_active)
        except ValueError:
            continue
        diff = (today - last_date).days
        stage = user["inactivity_stage"] or 0

        if diff >= 7 and stage < 2:
            text = (
                "😔 Yo'qolib ketgan bo'lsangiz ham, hech qisi yo'q — qaytadan boshlash "
                "har doim mumkin.\n\n"
                "🔄 <b>Recovery rejimi</b>: kichik bir qadam bilan boshlang. Bugun uchun "
                "faqat 1 ta oddiy vazifa belgilang va uni bajaring. Streak'ingiz nolga "
                "tushgan bo'lishi mumkin, lekin har bir katta yo'l bitta qadamdan boshlanadi."
            )
            try:
                await context.bot.send_message(user["telegram_id"], text, parse_mode="HTML",
                                                 reply_markup=main_menu_keyboard())
            except Exception:
                pass
            await db.set_inactivity_stage(user["telegram_id"], 2)
        elif diff >= 3 and stage < 1:
            text = (
                f"👋 {diff} kundan beri ko'rinmadingiz. Hammasi joyidami?\n\n"
                "Maqsadlaringiz sizni kutmoqda. Xohlasangiz, bugun kichik bir vazifa bilan "
                "qaytishingiz mumkin."
            )
            try:
                await context.bot.send_message(user["telegram_id"], text,
                                                 reply_markup=main_menu_keyboard())
            except Exception:
                pass
            await db.set_inactivity_stage(user["telegram_id"], 1)


def register_jobs(app: Application):
    """Dastur ishga tushganda chaqiriladi: faolsizlik nazorati job'ini qo'yadi va barcha
    foydalanuvchilar uchun eslatmalarni rejalashtiradi."""
    if app.job_queue is None:
        return

    async def _startup_schedule(context: ContextTypes.DEFAULT_TYPE):
        await schedule_all_users_jobs(app)

    app.job_queue.run_daily(
        inactivity_check_job,
        datetime.time(hour=INACTIVITY_CHECK_HOUR, minute=INACTIVITY_CHECK_MINUTE,
                      tzinfo=TIMEZONE),
        name=INACTIVITY_JOB_NAME,
    )
    app.job_queue.run_once(_startup_schedule, when=1)
