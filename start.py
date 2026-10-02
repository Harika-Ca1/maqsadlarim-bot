"""
handlers/start.py
/start buyrug'i va asosiy menyuga qaytish.
"""
from telegram import Update
from telegram.ext import ContextTypes

import database as db
from keyboards import start_keyboard, main_menu_keyboard

WELCOME_TEXT = (
    "👋 Salom, {name}!\n\n"
    "Men <b>Maqsadlarim</b> botiman — uzoq muddatli maqsadlaringizni unutmasligingiz, "
    "ularni kichik va real vazifalarga bo'lib, har kuni bajarib borishingiz uchun "
    "yordamchiman.\n\n"
    "Men sizga:\n"
    "🎯 Katta maqsadni bosqichlarga bo'lishda\n"
    "📅 Har kunlik rejani tuzishda\n"
    "📝 Kechqurun natijalarni tekshirishda\n"
    "🔥 Faollik streak'ini saqlashda\n"
    "📊 Progressni tahlil qilishda\n"
    "yordam beraman.\n\n"
    "Boshlashga tayyormisiz?"
)

MAIN_MENU_TEXT = "📍 Asosiy menyu. Nima qilamiz?"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.get_or_create_user(user.id, user.username, user.first_name)
    await db.touch_user(user.id)
    text = WELCOME_TEXT.format(name=user.first_name or "do'stim")
    await update.message.reply_text(text, reply_markup=start_keyboard(), parse_mode="HTML")


async def start_begin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await db.touch_user(update.effective_user.id)
    await query.edit_message_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())


async def back_to_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await db.touch_user(update.effective_user.id)
    try:
        await query.edit_message_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    except Exception:
        await context.bot.send_message(update.effective_chat.id, MAIN_MENU_TEXT,
                                        reply_markup=main_menu_keyboard())


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Boshqa modullardan asosiy menyuni yangi xabar sifatida chiqarish uchun."""
    await context.bot.send_message(update.effective_chat.id, MAIN_MENU_TEXT,
                                    reply_markup=main_menu_keyboard())
