"""
handlers/checkin.py
Kechki check-in: "Bugun rejangiz qanday o'tdi?"
Bajarilgan/bajarilmagan vazifalar avtomatik hisoblanadi, so'ng foydalanuvchidan
erkin izoh va ertangi kun uchun o'zgarish so'raladi.
"""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, filters, CommandHandler,
)

import database as db
from keyboards import back_to_menu_keyboard, cancel_keyboard
from utils import today_str, status_emoji

CHECKIN_NOTES, CHECKIN_TOMORROW = range(200, 202)


async def checkin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)
    tasks = await db.get_tasks_by_date(user["id"], today_str())

    if not tasks:
        await query.edit_message_text(
            "Bugun uchun rejalashtirilgan vazifalaringiz yo'q edi, shuning uchun "
            "check-in ham kerak emas. Ertaga \"➕ Yangi maqsad\" yoki mavjud maqsadga "
            "vazifa qo'shib ko'ring!",
            reply_markup=back_to_menu_keyboard(),
        )
        return ConversationHandler.END

    done = [t for t in tasks if t["status"] == "done"]
    partial = [t for t in tasks if t["status"] == "partial"]
    failed = [t for t in tasks if t["status"] == "failed"]
    pending = [t for t in tasks if t["status"] == "pending"]

    lines = [f"🌙 <b>Bugungi Check-in</b>", "Bugun rejangiz qanday o'tdi?\n"]
    lines.append(f"✅ Bajarildi: {len(done)}")
    lines.append(f"🟡 Qisman bajarildi: {len(partial)}")
    lines.append(f"❌ Bajarilmadi: {len(failed)}")
    if pending:
        lines.append(f"⬜ Hali belgilanmagan: {len(pending)}")
        lines.append("\n<i>Eslatma: belgilanmagan vazifalarni \"📅 Bugungi reja\" bo'limidan "
                      "belgilashingiz mumkin.</i>")
    if failed:
        lines.append("\nBajarilmagan vazifalar:")
        for t in failed:
            reason = f" ({t['fail_reason']})" if t["fail_reason"] else ""
            lines.append(f"• {t['title']}{reason}")

    context.user_data["checkin"] = {
        "tasks_done": len(done),
        "tasks_total": len(tasks),
    }

    lines.append("\n✍️ Umumiy holat haqida qisqacha izoh yozing (nima bajarilmadi / sabab):")
    await query.edit_message_text("\n".join(lines), parse_mode="HTML",
                                   reply_markup=cancel_keyboard())
    return CHECKIN_NOTES


async def checkin_notes_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["checkin"]["notes"] = update.message.text.strip()
    await update.message.reply_text(
        "👍 Va nihoyat: ertaga nimani o'zgartirish kerak deb o'ylaysiz?",
        reply_markup=cancel_keyboard(),
    )
    return CHECKIN_TOMORROW


async def checkin_tomorrow_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data.pop("checkin")
    data["tomorrow_change"] = update.message.text.strip()

    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)
    today = today_str()
    await db.create_checkin(user["id"], today, data["tasks_done"], data["tasks_total"],
                             data["notes"], data["tomorrow_change"])
    current, longest = await db.update_streak_on_checkin(user["id"], today)

    text = (
        f"✅ Check-in saqlandi! Rahmat, halol o'z-o'zini tahlil qilish — bu o'sishning "
        f"eng muhim qismi.\n\n"
        f"🔥 Joriy streak: {current} kun"
        + (f" (rekord: {longest} kun)" if longest > current else "")
        + f"\n\n📌 Ertangi fokus: {data['tomorrow_change']}"
    )
    await update.message.reply_text(text, reply_markup=back_to_menu_keyboard())
    return ConversationHandler.END


async def conv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("checkin", None)
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Bekor qilindi.", reply_markup=back_to_menu_keyboard())
    else:
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=back_to_menu_keyboard())
    return ConversationHandler.END


checkin_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(checkin_entry, pattern="^menu:checkin$")],
    states={
        CHECKIN_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, checkin_notes_received)],
        CHECKIN_TOMORROW: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           checkin_tomorrow_received)],
    },
    fallbacks=[
        CallbackQueryHandler(conv_cancel, pattern="^conv:cancel$"),
        CommandHandler("cancel", conv_cancel),
    ],
    name="checkin_conversation",
    persistent=False,
)


def register(app):
    app.add_handler(checkin_conversation)
