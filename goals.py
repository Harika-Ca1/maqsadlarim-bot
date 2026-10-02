"""
handlers/goals.py
- Yangi maqsad qo'shish (ConversationHandler)
- Maqsadni bosqichlarga bo'lish
- Maqsadlar ro'yxati va tafsilotlari
- Bosqichga / maqsadga bugungi vazifa qo'shish
"""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, filters, CommandHandler,
)

import database as db
from keyboards import (
    goals_list_keyboard, goal_detail_keyboard, stage_detail_keyboard,
    confirm_stages_keyboard, finish_stages_keyboard, cancel_keyboard,
    back_to_menu_keyboard,
)
from utils import today_str, progress_bar

# ConversationHandler holatlari
TITLE, WHY, DEADLINE, RESULT, STAGES_DECISION, STAGES_INPUT, ADD_STAGE, ADD_TASK = range(8)


# ---------------------------------------------------------------------------
# YANGI MAQSAD QO'SHISH OQIMI
# ---------------------------------------------------------------------------

async def new_goal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_goal"] = {}
    await query.edit_message_text(
        "➕ <b>Yangi maqsad</b>\n\n1️⃣ Maqsadingiz nomini yozing:",
        parse_mode="HTML", reply_markup=cancel_keyboard(),
    )
    return TITLE


async def goal_title_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_goal"]["title"] = update.message.text.strip()
    await update.message.reply_text(
        "2️⃣ Nega bu maqsad siz uchun muhim?", reply_markup=cancel_keyboard()
    )
    return WHY


async def goal_why_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_goal"]["why"] = update.message.text.strip()
    await update.message.reply_text(
        "3️⃣ Qachongacha bajarilishi kerak? (masalan: 2026-12-31 yoki \"3 oy ichida\")",
        reply_markup=cancel_keyboard(),
    )
    return DEADLINE


async def goal_deadline_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_goal"]["deadline"] = update.message.text.strip()
    await update.message.reply_text(
        "4️⃣ Taxminiy natija qanday bo'lishi kerak?", reply_markup=cancel_keyboard()
    )
    return RESULT


async def goal_result_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_goal"]["expected_result"] = update.message.text.strip()
    g = context.user_data["new_goal"]

    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)
    goal_id = await db.create_goal(user["id"], g["title"], g["why"], g["deadline"],
                                    g["expected_result"])
    context.user_data["new_goal"]["id"] = goal_id

    text = (
        f"✅ Maqsad saqlandi!\n\n"
        f"🎯 <b>{g['title']}</b>\n"
        f"💡 Sabab: {g['why']}\n"
        f"⏳ Muddat: {g['deadline']}\n"
        f"🏁 Natija: {g['expected_result']}\n\n"
        f"Endi katta maqsadni kichik bosqichlarga bo'lib olaylik.\n"
        f"Masalan: \"Uy qurish biznesini boshlash\" → 1) Bozorni o'rganish, "
        f"2) Moliyaviy model, 3) Mijoz topish...\n\n"
        f"Bosqichlarga bo'lamizmi?"
    )
    await update.message.reply_text(text, parse_mode="HTML",
                                     reply_markup=confirm_stages_keyboard())
    return STAGES_DECISION


async def stages_decision_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["stage_order"] = 1
    await query.edit_message_text(
        "📋 1-bosqich nomini yozing (masalan: \"Bozorni o'rganish\"):\n\n"
        "Barcha bosqichlarni kiritib bo'lgach, pastdagi \"✅ Bosqichlarni tugatish\" "
        "tugmasini bosing.",
    )
    await context.bot.send_message(update.effective_chat.id, "👇",
                                    reply_markup=finish_stages_keyboard())
    return STAGES_INPUT


async def stages_decision_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    goal_id = context.user_data["new_goal"]["id"]
    context.user_data.pop("new_goal", None)
    await query.edit_message_text(
        "Xo'p, bosqichlarni keyinroq \"🎯 Maqsadlarim\" bo'limidan qo'shishingiz mumkin.",
    )
    await show_goal_detail(update, context, goal_id, send_new=True)
    return ConversationHandler.END


async def stage_title_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal_id = context.user_data["new_goal"]["id"]
    order = context.user_data.get("stage_order", 1)
    title = update.message.text.strip()
    await db.create_stage(goal_id, title, order)
    context.user_data["stage_order"] = order + 1
    await update.message.reply_text(
        f"✅ {order}-bosqich qo'shildi: {title}\n\nKeyingi bosqichni yozing yoki tugating.",
        reply_markup=finish_stages_keyboard(),
    )
    return STAGES_INPUT


async def stages_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    goal_id = context.user_data["new_goal"]["id"]
    context.user_data.pop("new_goal", None)
    context.user_data.pop("stage_order", None)
    await query.edit_message_text("🎉 Bosqichlar saqlandi! Endi har bosqich uchun kunlik "
                                   "vazifalar qo'shishingiz mumkin.")
    await show_goal_detail(update, context, goal_id, send_new=True)
    return ConversationHandler.END


async def conv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Bekor qilindi.", reply_markup=back_to_menu_keyboard())
    else:
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=back_to_menu_keyboard())
    return ConversationHandler.END


new_goal_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(new_goal_entry, pattern="^menu:newgoal$")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_title_received)],
        WHY: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_why_received)],
        DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_deadline_received)],
        RESULT: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_result_received)],
        STAGES_DECISION: [
            CallbackQueryHandler(stages_decision_yes, pattern="^newgoal:stages_yes$"),
            CallbackQueryHandler(stages_decision_no, pattern="^newgoal:stages_no$"),
        ],
        STAGES_INPUT: [
            CallbackQueryHandler(stages_finish, pattern="^newgoal:stages_done$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, stage_title_received),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(conv_cancel, pattern="^conv:cancel$"),
        CommandHandler("cancel", conv_cancel),
    ],
    name="new_goal_conversation",
    persistent=False,
)


# ---------------------------------------------------------------------------
# BOSQICH QO'SHISH (mavjud maqsadga)
# ---------------------------------------------------------------------------

async def add_stage_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    goal_id = int(query.data.split(":")[2])
    context.user_data["add_stage_goal_id"] = goal_id
    await query.edit_message_text("📋 Yangi bosqich nomini yozing:", reply_markup=cancel_keyboard())
    return ADD_STAGE


async def add_stage_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal_id = context.user_data.pop("add_stage_goal_id")
    stages = await db.get_stages(goal_id)
    order = len(stages) + 1
    await db.create_stage(goal_id, update.message.text.strip(), order)
    await update.message.reply_text("✅ Bosqich qo'shildi!")
    await show_goal_detail(update, context, goal_id, send_new=True)
    return ConversationHandler.END


add_stage_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_stage_entry, pattern="^goal:addstage:")],
    states={ADD_STAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_stage_received)]},
    fallbacks=[
        CallbackQueryHandler(conv_cancel, pattern="^conv:cancel$"),
        CommandHandler("cancel", conv_cancel),
    ],
    name="add_stage_conversation",
    persistent=False,
)


# ---------------------------------------------------------------------------
# BUGUNGI VAZIFA QO'SHISH (maqsadga yoki bosqichga)
# ---------------------------------------------------------------------------

async def add_task_from_goal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    goal_id = int(query.data.split(":")[2])
    context.user_data["add_task"] = {"goal_id": goal_id, "stage_id": None}
    await query.edit_message_text("📅 Bugungi vazifa matnini yozing:", reply_markup=cancel_keyboard())
    return ADD_TASK


async def add_task_from_stage_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stage_id = int(query.data.split(":")[2])
    stage = await db.get_stage(stage_id)
    context.user_data["add_task"] = {"goal_id": stage["goal_id"], "stage_id": stage_id}
    await query.edit_message_text("📅 Bugungi vazifa matnini yozing:", reply_markup=cancel_keyboard())
    return ADD_TASK


async def add_task_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = context.user_data.pop("add_task")
    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)
    await db.create_task(info["goal_id"], user["id"], update.message.text.strip(),
                          today_str(), stage_id=info["stage_id"])
    await update.message.reply_text("✅ Vazifa bugungi rejaga qo'shildi!")
    await show_goal_detail(update, context, info["goal_id"], send_new=True)
    return ConversationHandler.END


add_task_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(add_task_from_goal_entry, pattern="^goal:addtask:"),
        CallbackQueryHandler(add_task_from_stage_entry, pattern="^stage:addtask:"),
    ],
    states={ADD_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_received)]},
    fallbacks=[
        CallbackQueryHandler(conv_cancel, pattern="^conv:cancel$"),
        CommandHandler("cancel", conv_cancel),
    ],
    name="add_task_conversation",
    persistent=False,
)


# ---------------------------------------------------------------------------
# MAQSADLAR RO'YXATI VA TAFSILOTLARI (oddiy callbacklar)
# ---------------------------------------------------------------------------

async def goals_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)
    goals = await db.get_goals(user["id"], status="active")
    if not goals:
        await query.edit_message_text(
            "Hozircha maqsadlaringiz yo'q. Keling, birinchisini qo'shamiz!",
            reply_markup=goals_list_keyboard([]),
        )
        return
    await query.edit_message_text("🎯 <b>Sizning maqsadlaringiz:</b>", parse_mode="HTML",
                                   reply_markup=goals_list_keyboard(goals))


async def show_goal_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, goal_id: int,
                            send_new: bool = False):
    goal = await db.get_goal(goal_id)
    if not goal:
        return
    stages = await db.get_stages(goal_id)
    text = (
        f"🎯 <b>{goal['title']}</b>\n\n"
        f"💡 Sabab: {goal['why']}\n"
        f"⏳ Muddat: {goal['deadline']}\n"
        f"🏁 Kutilayotgan natija: {goal['expected_result']}\n\n"
        f"📈 Progress: {progress_bar(goal['progress'])}\n\n"
        f"📋 Bosqichlar: {len(stages)} ta\n"
    )
    markup = goal_detail_keyboard(goal_id, stages)
    if send_new:
        await context.bot.send_message(update.effective_chat.id, text, parse_mode="HTML",
                                        reply_markup=markup)
    else:
        query = update.callback_query
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)


async def goal_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    goal_id = int(query.data.split(":")[2])
    await show_goal_detail(update, context, goal_id, send_new=False)


async def goal_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    goal_id = int(query.data.split(":")[2])
    progress = await db.compute_and_update_goal_progress(goal_id)
    await query.answer(f"Progress yangilandi: {progress}%")
    await show_goal_detail(update, context, goal_id, send_new=False)


async def goal_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    goal_id = int(query.data.split(":")[2])
    await db.delete_goal(goal_id)
    user = await db.get_or_create_user(update.effective_user.id,
                                        update.effective_user.username,
                                        update.effective_user.first_name)
    goals = await db.get_goals(user["id"], status="active")
    await query.edit_message_text("🗑 Maqsad o'chirildi.\n\n🎯 <b>Sizning maqsadlaringiz:</b>",
                                   parse_mode="HTML", reply_markup=goals_list_keyboard(goals))


async def stage_view_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stage_id = int(query.data.split(":")[2])
    stage = await db.get_stage(stage_id)
    goal = await db.get_goal(stage["goal_id"])
    tasks = await db.get_tasks_by_goal(stage["goal_id"])
    stage_tasks = [t for t in tasks if t["stage_id"] == stage_id]
    done = len([t for t in stage_tasks if t["status"] == "done"])
    text = (
        f"📋 <b>{stage['title']}</b>\n"
        f"🎯 Maqsad: {goal['title']}\n"
        f"Holati: {'✅ Yakunlangan' if stage['status'] == 'done' else '🟢 Faol'}\n\n"
        f"Vazifalar: {done}/{len(stage_tasks)} bajarilgan"
    )
    await query.edit_message_text(text, parse_mode="HTML",
                                   reply_markup=stage_detail_keyboard(stage_id, stage["goal_id"]))


async def stage_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    stage_id = int(query.data.split(":")[2])
    stage = await db.get_stage(stage_id)
    await db.set_stage_status(stage_id, "done")
    await db.compute_and_update_goal_progress(stage["goal_id"])
    await query.answer("Bosqich yakunlandi! 🎉")
    await show_goal_detail(update, context, stage["goal_id"], send_new=False)


def register(app):
    app.add_handler(new_goal_conversation)
    app.add_handler(add_stage_conversation)
    app.add_handler(add_task_conversation)
    app.add_handler(CallbackQueryHandler(goals_list_callback, pattern="^menu:goals$"))
    app.add_handler(CallbackQueryHandler(goal_view_callback, pattern="^goal:view:"))
    app.add_handler(CallbackQueryHandler(goal_refresh_callback, pattern="^goal:refresh:"))
    app.add_handler(CallbackQueryHandler(goal_delete_callback, pattern="^goal:delete:"))
    app.add_handler(CallbackQueryHandler(stage_view_callback, pattern="^stage:view:"))
    app.add_handler(CallbackQueryHandler(stage_done_callback, pattern="^stage:done:"))
