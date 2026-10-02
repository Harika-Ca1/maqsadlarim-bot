"""
handlers/stats.py
- 🔥 Streak ko'rsatish
- 📊 Haftalik va oylik hisobot (bajarilgan/bajarilmagan, foiz, maqsadlar progressi)
"""
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

import database as db
from keyboards import back_to_menu_keyboard
from utils import week_ago_str, month_ago_str, percent, progress_bar


async def streak_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)
    streak = await db.get_streak(user["id"])
    current = streak["current_streak"] or 0
    longest = streak["longest_streak"] or 0

    if current == 0:
        msg = "Hali streak boshlanmagan. Bugun check-in qiling va birinchi kunni boshlang! 🔥"
    else:
        msg = f"🔥 <b>{current} kunlik streak!</b>\n\nAjoyib davom etyapsiz, shu tezlikda ketaylik!"

    text = f"{msg}\n\n🏆 Eng uzun streak: {longest} kun"
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_to_menu_keyboard())


def _period_report(tasks, checkins):
    total = len(tasks)
    done = len([t for t in tasks if t["status"] == "done"])
    partial = len([t for t in tasks if t["status"] == "partial"])
    failed = len([t for t in tasks if t["status"] == "failed"])
    pct = percent(done, total)
    return total, done, partial, failed, pct


async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)

    week_tasks = await db.get_tasks_since(user["id"], week_ago_str())
    month_tasks = await db.get_tasks_since(user["id"], month_ago_str())
    streak = await db.get_streak(user["id"])
    goals = await db.get_goals(user["id"], status=None)

    w_total, w_done, w_partial, w_failed, w_pct = _period_report(week_tasks, None)
    m_total, m_done, m_partial, m_failed, m_pct = _period_report(month_tasks, None)

    lines = ["📊 <b>Natijalarim</b>\n"]
    lines.append("🗓 <b>Oxirgi 7 kun:</b>")
    lines.append(f"✅ Bajarildi: {w_done}  🟡 Qisman: {w_partial}  ❌ Bajarilmadi: {w_failed}")
    lines.append(f"Jami: {w_total} ta vazifa, muvaffaqiyat: {w_pct}%\n")

    lines.append("📆 <b>Oxirgi 30 kun:</b>")
    lines.append(f"✅ Bajarildi: {m_done}  🟡 Qisman: {m_partial}  ❌ Bajarilmadi: {m_failed}")
    lines.append(f"Jami: {m_total} ta vazifa, muvaffaqiyat: {m_pct}%\n")

    lines.append(f"🔥 Joriy streak: {streak['current_streak'] or 0} kun "
                  f"(rekord: {streak['longest_streak'] or 0} kun)\n")

    if goals:
        lines.append("🎯 <b>Maqsadlar progressi:</b>")
        for g in goals:
            status_mark = "🏁" if g["status"] == "completed" else "🟢"
            lines.append(f"{status_mark} {g['title']}: {progress_bar(g['progress'])}")
    else:
        lines.append("Hali maqsadlaringiz yo'q.")

    await query.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=back_to_menu_keyboard())


def register(app):
    app.add_handler(CallbackQueryHandler(streak_callback, pattern="^menu:streak$"))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^menu:stats$"))
