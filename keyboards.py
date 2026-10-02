"""
keyboards.py
Botda ishlatiladigan barcha InlineKeyboardMarkup klaviaturalar shu yerda.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils import status_emoji, FAIL_REASONS


def start_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Boshlash", callback_data="start:begin")]])


def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton("🎯 Maqsadlarim", callback_data="menu:goals")],
        [InlineKeyboardButton("➕ Yangi maqsad", callback_data="menu:newgoal")],
        [InlineKeyboardButton("📅 Bugungi reja", callback_data="menu:today")],
        [InlineKeyboardButton("📝 Bugungi Check-in", callback_data="menu:checkin")],
        [InlineKeyboardButton("📊 Natijalarim", callback_data="menu:stats")],
        [InlineKeyboardButton("🔥 Streak", callback_data="menu:streak")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="menu:settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def back_to_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Asosiy menyu", callback_data="menu:back")]])


def goals_list_keyboard(goals):
    rows = []
    for g in goals:
        rows.append([InlineKeyboardButton(f"🎯 {g['title']} ({g['progress']}%)",
                                           callback_data=f"goal:view:{g['id']}")])
    rows.append([InlineKeyboardButton("➕ Yangi maqsad", callback_data="menu:newgoal")])
    rows.append([InlineKeyboardButton("⬅️ Asosiy menyu", callback_data="menu:back")])
    return InlineKeyboardMarkup(rows)


def goal_detail_keyboard(goal_id, stages):
    rows = []
    for s in stages:
        mark = "✅" if s["status"] == "done" else "▫️"
        rows.append([InlineKeyboardButton(f"{mark} {s['title']}",
                                           callback_data=f"stage:view:{s['id']}")])
    rows.append([InlineKeyboardButton("📋 Bosqich qo'shish", callback_data=f"goal:addstage:{goal_id}")])
    rows.append([InlineKeyboardButton("📅 Bugungi vazifa qo'shish", callback_data=f"goal:addtask:{goal_id}")])
    rows.append([InlineKeyboardButton("🔄 Progressni yangilash", callback_data=f"goal:refresh:{goal_id}")])
    rows.append([InlineKeyboardButton("🗑 Maqsadni o'chirish", callback_data=f"goal:delete:{goal_id}")])
    rows.append([InlineKeyboardButton("⬅️ Maqsadlarim", callback_data="menu:goals")])
    return InlineKeyboardMarkup(rows)


def stage_detail_keyboard(stage_id, goal_id):
    rows = [
        [InlineKeyboardButton("📅 Shu bosqichga vazifa qo'shish", callback_data=f"stage:addtask:{stage_id}")],
        [InlineKeyboardButton("✅ Bosqichni yakunlash", callback_data=f"stage:done:{stage_id}")],
        [InlineKeyboardButton("⬅️ Maqsadga qaytish", callback_data=f"goal:view:{goal_id}")],
    ]
    return InlineKeyboardMarkup(rows)


def confirm_stages_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ha, bosqichlarga bo'lamiz", callback_data="newgoal:stages_yes")],
        [InlineKeyboardButton("➡️ Yo'q, keyinroq", callback_data="newgoal:stages_no")],
    ])


def finish_stages_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Bosqichlarni tugatish", callback_data="newgoal:stages_done")],
    ])


def daily_tasks_keyboard(tasks):
    rows = []
    for t in tasks:
        emoji = status_emoji(t["status"])
        rows.append([InlineKeyboardButton(f"{emoji} {t['title']}", callback_data=f"task:open:{t['id']}")])
    rows.append([InlineKeyboardButton("⬅️ Asosiy menyu", callback_data="menu:back")])
    return InlineKeyboardMarkup(rows)


def task_status_keyboard(task_id):
    rows = [
        [
            InlineKeyboardButton("✅ Bajarildi", callback_data=f"task:status:{task_id}:done"),
            InlineKeyboardButton("🟡 Qisman", callback_data=f"task:status:{task_id}:partial"),
        ],
        [InlineKeyboardButton("❌ Bajarilmadi", callback_data=f"task:status:{task_id}:failed")],
        [InlineKeyboardButton("⬅️ Bugungi reja", callback_data="menu:today")],
    ]
    return InlineKeyboardMarkup(rows)


def fail_reason_keyboard(task_id):
    rows = []
    for code, label in FAIL_REASONS.items():
        rows.append([InlineKeyboardButton(label, callback_data=f"reason:{task_id}:{code}")])
    return InlineKeyboardMarkup(rows)


def split_task_keyboard(task_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✂️ Ha, bo'lib beraylik", callback_data=f"split:yes:{task_id}")],
        [InlineKeyboardButton("➡️ Yo'q, kerak emas", callback_data=f"split:no:{task_id}")],
    ])


def settings_keyboard(user):
    reminders_status = "🔔 Yoqilgan" if user["reminders_on"] else "🔕 O'chirilgan"
    rows = [
        [InlineKeyboardButton(f"🌅 Ertalabki reja vaqti: {user['morning_time']}", callback_data="settings:morning")],
        [InlineKeyboardButton(f"🌙 Kechki check-in vaqti: {user['evening_time']}", callback_data="settings:evening")],
        [InlineKeyboardButton(f"Eslatmalar: {reminders_status}", callback_data="settings:toggle")],
        [InlineKeyboardButton("⬅️ Asosiy menyu", callback_data="menu:back")],
    ]
    return InlineKeyboardMarkup(rows)


def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bekor qilish", callback_data="conv:cancel")]])
