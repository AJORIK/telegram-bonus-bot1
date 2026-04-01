# bot.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@AutoXdrive")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/AutoXdrive")

if not BOT_TOKEN:
    raise ValueError("Укажите BOT_TOKEN в переменных окружения!")

# ================== ЛОГИРОВАНИЕ ==================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== ТЕКСТЫ ==================
WELCOME_TEXT = (
    "🎉 <b>Добро пожаловать!</b>\n\n"
    "Чтобы участвовать в конкурсе, подпишитесь на наш канал 👇\n"
    "После подписки нажмите <b>«✅ Проверить подписку»</b>"
)
SUCCESS_TEXT = "🎊 <b>Вы подписаны на канал!</b>\n\nНажмите <b>«УЧАВСТВОВАТЬ»</b>, чтобы принять участие!"
NOT_SUBSCRIBED_TEXT = (
    "❌ <b>Вы ещё не подписались на канал!</b>\nСначала подпишитесь, потом нажмите «✅ Проверить подписку»"
)
PARTICIPATE_TEXT = (
    "✅ <b>Теперь вы участвуете в конкурсе!</b>\nРезультаты будут выложены в канале 5 апреля."
)
ALREADY_PARTICIPATE_TEXT = (
    "⚠️ <b>Вы уже участвуете в конкурсе!</b>\nЖдите результатов 5 апреля."
)

# ================== КЛАВИАТУРЫ ==================
def get_subscribe_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📢 Подписаться на канал", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")],
        ]
    )

def get_main_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("УЧАВСТВОВАТЬ", callback_data="participate")]])

def get_back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back_menu")]])

# ================== ХРАНЕНИЕ УЧАСТНИКОВ ==================
participants = set()

# ================== ПРОВЕРКА ПОДПИСКИ ==================
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator", "owner"]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

# ================== ОБРАБОТЧИКИ ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_subscribed(user_id, context):
        await update.message.reply_text(SUCCESS_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard())

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "check_sub":
        if await is_subscribed(user_id, context):
            new_text, new_markup = SUCCESS_TEXT, get_main_keyboard()
        else:
            new_text, new_markup = NOT_SUBSCRIBED_TEXT, get_subscribe_keyboard()
        if query.message.text != new_text:
            await query.edit_message_text(text=new_text, parse_mode="HTML", reply_markup=new_markup)

    elif query.data == "participate":
        if not await is_subscribed(user_id, context):
            await query.edit_message_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard())
            return
        if user_id in participants:
            await query.edit_message_text(ALREADY_PARTICIPATE_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard())
        else:
            participants.add(user_id)
            await query.edit_message_text(PARTICIPATE_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard())

    elif query.data == "back_menu":
        if await is_subscribed(user_id, context):
            await query.edit_message_text(SUCCESS_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard())
        else:
            await query.edit_message_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_subscribed(user_id, context):
        await update.message.reply_text(
            "Нажмите кнопку «УЧАВСТВОВАТЬ» для участия.", parse_mode="HTML"
        )
    else:
        await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard())

# ================== ЗАПУСК ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
