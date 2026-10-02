"""
bot.py
"Maqsadlarim" Telegram botini ishga tushirish nuqtasi.

Ishga tushirish:
    python bot.py

Talab qilinadigan narsalar requirements.txt va README.md faylida ko'rsatilgan.
"""
import logging

from telegram import Update
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes,
)

from config import BOT_TOKEN
import database as db

from handlers import start, goals, daily_plan, checkin, stats, settings, jobs

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Umumiy /cancel buyrug'i - har qanday joriy amalni bekor qiladi."""
    context.user_data.clear()
    await update.message.reply_text("❌ Amal bekor qilindi. /start orqali qayta boshlashingiz "
                                      "mumkin.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ <b>Yordam</b>\n\n"
        "/start — botni ishga tushirish va asosiy menyu\n"
        "/cancel — joriy amalni bekor qilish\n"
        "/help — ushbu yordam matni\n\n"
        "Asosiy menyudagi tugmalar orqali maqsad qo'shishingiz, kunlik rejani ko'rishingiz, "
        "check-in qilishingiz va natijalaringizni kuzatishingiz mumkin."
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def post_init(application: Application):
    """Dastur ishga tushgandan so'ng bazani tayyorlaydi va fon job'larni qo'yadi."""
    await db.init_db()
    jobs.register_jobs(application)
    logger.info("Ma'lumotlar bazasi tayyor va fon vazifalar (job) rejalashtirildi.")


def main():
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Umumiy buyruqlar
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("help", help_command))
    # /cancel alohida guruhda: avval har bir suhbat (ConversationHandler) o'zining
    # /cancel fallback'ini ishlatadi (0-guruh), so'ng shu umumiy handler ham chaqiriladi
    # (agar hech qanday faol suhbat bo'lmasa, foydalanuvchiga tushunarli xabar beradi).
    application.add_handler(CommandHandler("cancel", cancel_command), group=1)

    # /start -> "Boshlash" tugmasi va asosiy menyuga qaytish
    application.add_handler(CallbackQueryHandler(start.start_begin_callback,
                                                  pattern="^start:begin$"))
    application.add_handler(CallbackQueryHandler(start.back_to_menu_callback,
                                                  pattern="^menu:back$"))

    # Har bir modulning handlerlarini ro'yxatdan o'tkazish
    goals.register(application)
    daily_plan.register(application)
    checkin.register(application)
    stats.register(application)
    settings.register(application)

    logger.info("Bot ishga tushmoqda...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
