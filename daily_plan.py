"""
handlers/daily_plan.py
- Bugungi rejani ko'rsatish
- Har bir vazifa uchun status belgilash (✅/🟡/❌)
- Bajarilmagan vazifa uchun sabab so'rash
- "Vazifa juda katta edi" bo'lsa, uni kichik vazifalarga bo'lishni taklif qilish
"""
import datetime

from telegram import Update
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler,
    MessageHandler, filters, CommandHandler,
)

import database as db
from keyboards import (
    daily_tasks_keyboard, task_status_keyboard, fail_reason_keyboard,
    split_task_keyboard, back_to_menu_keyboard,
)
from utils import today_str, status_emoji, FAIL_REASONS

SPLIT_INPUT = 100


async def show_today_plan(update: Update, context: ContextTypes.DEFAULT_TYPE, send_new=False):
    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)
    tasks = await db.get_tasks_by_date(user["id"], today_str())
    if not tasks:
        text = (
            "📅 Bugun uchun vazifalaringiz yo'q.\n\n"
            "\"🎯 Maqsadlarim\" bo'limiga kirib, biror maqsadga bugungi vazifa qo'shishingiz "
            "mumkin."
        )
    else:
        done = len([t for t in tasks if t["status"] == "done"])
        text = f"📅 <b>Bugungi reja</b> ({done}/{len(tasks)} bajarildi)\n\nVazifani tanlang:"
    markup = daily_tasks_keyboard(tasks)
    if send_new:
        await context.bot.send_message(update.effective_chat.id, text, parse_mode="HTML",
                                        reply_markup=markup)
    else:
        query = update.callback_query
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)


async def today_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_today_plan(update, context, send_new=False)


async def task_open_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[2])
    task = await db.get_task(task_id)
    text = (
        f"📌 <b>{task['title']}</b>\n"
        f"Hozirgi holat: {status_emoji(task['status'])}\n\n"
        f"Ushbu vazifa bo'yicha natijani belgilang:"
    )
    await query.edit_message_text(text, parse_mode="HTML",
                                   reply_markup=task_status_keyboard(task_id))


async def task_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, _, task_id, status = query.data.split(":")
    task_id = int(task_id)

    if status in ("done", "partial"):
        await db.set_task_status(task_id, status)
        task = await db.get_task(task_id)
        await db.compute_and_update_goal_progress(task["goal_id"])
        await query.edit_message_text(
            f"{status_emoji(status)} Belgilandi: {task['title']}",
            reply_markup=back_to_menu_keyboard(),
        )
        await show_today_plan(update, context, send_new=True)
        return ConversationHandler.END

    # status == failed -> sabab so'raymiz
    task = await db.get_task(task_id)
    await query.edit_message_text(
        f"❌ \"{task['title']}\" bajarilmadi.\n\nNega bajarilmadi?",
        reply_markup=fail_reason_keyboard(task_id),
    )
    return ConversationHandler.END


async def fail_reason_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, task_id, code = query.data.split(":")
    task_id = int(task_id)
    reason_label = FAIL_REASONS.get(code, code)
    await db.set_task_status(task_id, "failed", fail_reason=reason_label)
    task = await db.get_task(task_id)
    await db.compute_and_update_goal_progress(task["goal_id"])

    if code == "too_big":
        await query.edit_message_text(
            f"❓ Tushunarli, \"{task['title']}\" juda katta ekan.\n\n"
            f"Uni kichikroq, bajarish osonroq vazifalarga bo'lib beraylikmi?",
            reply_markup=split_task_keyboard(task_id),
        )
        return SPLIT_INPUT
    else:
        await query.edit_message_text(
            f"Qabul qilindi: {reason_label}\n\nErtaga bu vazifani qayta rejalashtirishingiz "
            f"mumkin. Davom etamiz!",
            reply_markup=back_to_menu_keyboard(),
        )
        return ConversationHandler.END


async def split_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[2])
    context.user_data["split_task_id"] = task_id
    await query.edit_message_text(
        "✂️ Yangi, kichikroq vazifalarni har birini alohida qatorda yozing.\n\n"
        "Masalan:\n<code>Mavzuni izlab topish\nBirinchi bo'limni yozish\nTahrirlash</code>",
        parse_mode="HTML",
    )
    return SPLIT_INPUT + 1


async def split_no_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Xo'p, keyinroq o'zingiz bo'lib olasiz.",
                                   reply_markup=back_to_menu_keyboard())
    return ConversationHandler.END


async def split_input_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_id = context.user_data.pop("split_task_id")
    task = await db.get_task(task_id)
    lines = [line.strip() for line in update.message.text.split("\n") if line.strip()]
    tomorrow = (datetime.date.fromisoformat(today_str()) + datetime.timedelta(days=1)).isoformat()

    for line in lines:
        await db.create_task(task["goal_id"], task["user_id"], line, tomorrow,
                              stage_id=task["stage_id"])

    await update.message.reply_text(
        f"✅ {len(lines)} ta kichik vazifa ertangi ({tomorrow}) rejaga qo'shildi!",
        reply_markup=back_to_menu_keyboard(),
    )
    return ConversationHandler.END


async def split_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("split_task_id", None)
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=back_to_menu_keyboard())
    return ConversationHandler.END


split_task_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(split_yes_callback, pattern="^split:yes:")],
    states={
        SPLIT_INPUT + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, split_input_received)],
    },
    fallbacks=[CommandHandler("cancel", split_cancel)],
    name="split_task_conversation",
    persistent=False,
)


def register(app):
    app.add_handler(CallbackQueryHandler(today_menu_callback, pattern="^menu:today$"))
    app.add_handler(CallbackQueryHandler(task_open_callback, pattern="^task:open:"))
    app.add_handler(CallbackQueryHandler(task_status_callback, pattern="^task:status:"))
    app.add_handler(CallbackQueryHandler(fail_reason_callback, pattern="^reason:"))
    app.add_handler(split_task_conversation)
    app.add_handler(CallbackQueryHandler(split_no_callback, pattern="^split:no:"))
