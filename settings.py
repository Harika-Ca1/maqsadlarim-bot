"""
handlers/settings.py
Ertalabki reja va kechki check-in eslatma vaqtlarini sozlash, eslatmalarni
yoqish/o'chirish.
"""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, filters, CommandHandler,
)

import database as db
from keyboards import settings_keyboard, cancel_keyboard, back_to_menu_keyboard
from utils import validate_time_format

SET_TIME = 300


async def settings_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)
    await query.edit_message_text(
        "⚙️ <b>Sozlamalar</b>\n\nEslatma vaqtlarini o'zgartirish uchun tugmani bosing:",
        parse_mode="HTML", reply_markup=settings_keyboard(user),
    )


async def set_morning_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["settings_field"] = "morning_time"
    await query.edit_message_text(
        "🌅 Ertalabki reja eslatmasi uchun vaqtni kiriting (HH:MM formatida, masalan 08:00):",
        reply_markup=cancel_keyboard(),
    )
    return SET_TIME


async def set_evening_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["settings_field"] = "evening_time"
    await query.edit_message_text(
        "🌙 Kechki check-in eslatmasi uchun vaqtni kiriting (HH:MM formatida, masalan 21:00):",
        reply_markup=cancel_keyboard(),
    )
    return SET_TIME


async def time_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not validate_time_format(text):
        await update.message.reply_text(
            "❗️ Noto'g'ri format. Iltimos HH:MM ko'rinishida kiriting (masalan 07:30):",
            reply_markup=cancel_keyboard(),
        )
        return SET_TIME

    field = context.user_data.pop("settings_field")
    telegram_id = update.effective_user.id
    if field == "morning_time":
        await db.update_user_settings(telegram_id, morning_time=text)
    else:
        await db.update_user_settings(telegram_id, evening_time=text)

    # Job'larni qayta rejalashtirish
    from handlers.jobs import reschedule_user_jobs
    user = await db.get_user_by_telegram_id(telegram_id)
    reschedule_user_jobs(context.application, user)

    await update.message.reply_text(f"✅ Yangi vaqt saqlandi: {text}",
                                     reply_markup=back_to_menu_keyboard())
    return ConversationHandler.END


async def toggle_reminders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    user = await db.get_user_by_telegram_id(telegram_id)
    new_value = not bool(user["reminders_on"])
    await db.update_user_settings(telegram_id, reminders_on=new_value)
    user = await db.get_user_by_telegram_id(telegram_id)

    from handlers.jobs import reschedule_user_jobs
    reschedule_user_jobs(context.application, user)

    await query.answer("Eslatmalar " + ("yoqildi 🔔" if new_value else "o'chirildi 🔕"))
    await query.edit_message_text(
        "⚙️ <b>Sozlamalar</b>\n\nEslatma vaqtlarini o'zgartirish uchun tugmani bosing:",
        parse_mode="HTML", reply_markup=settings_keyboard(user),
    )


async def conv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("settings_field", None)
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Bekor qilindi.", reply_markup=back_to_menu_keyboard())
    else:
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=back_to_menu_keyboard())
    return ConversationHandler.END


settings_time_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(set_morning_entry, pattern="^settings:morning$"),
        CallbackQueryHandler(set_evening_entry, pattern="^settings:evening$"),
    ],
    states={SET_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_received)]},
    fallbacks=[
        CallbackQueryHandler(conv_cancel, pattern="^conv:cancel$"),
        CommandHandler("cancel", conv_cancel),
    ],
    name="settings_time_conversation",
    persistent=False,
)


def register(app):
    app.add_handler(CallbackQueryHandler(settings_entry, pattern="^menu:settings$"))
    app.add_handler(settings_time_conversation)
    app.add_handler(CallbackQueryHandler(toggle_reminders_callback, pattern="^settings:toggle$"))
