import os
import json
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =================== НАСТРОЙКИ ===================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@AutoXdrive")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/AutoXdrive")
USERS_FILE = "users.json"

# =================== ЛОГИ ===================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =================== ПОЛЬЗОВАТЕЛИ ===================
all_users = set()

def load_users() -> set:
    if Path(USERS_FILE).exists():
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_users(users: set) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

def register_user(user_id: int):
    if user_id not in all_users:
        all_users.add(user_id)
        save_users(all_users)
        logger.info(f"Новый пользователь: {user_id}, всего: {len(all_users)}")

all_users = load_users()

# =================== ТЕКСТЫ ===================
WELCOME_TEXT = """🎉 <b>Добро пожаловать!</b>

Чтобы участвовать в конкурсе, подпишитесь на канал 👇
"""
SUCCESS_TEXT = "✅ Вы подписаны на канал! Нажмите «УЧАВСТВОВАТЬ» ниже."
NOT_SUBSCRIBED_TEXT = "❌ Вы ещё не подписались на канал! Сначала подпишитесь, потом нажмите «УЧАВСТВОВАТЬ»."
CONTEST_TEXT = "🎉 Теперь вы участвуете в конкурсе, результат выложим в канал 5 апреля."

# =================== КЛАВИАТУРЫ ===================
def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🎯 УЧАВСТВОВАТЬ", callback_data="participate")]
    ]
    return InlineKeyboardMarkup(keyboard)

# =================== ПРОВЕРКА ПОДПИСКИ ===================
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

# =================== ОБРАБОТЧИКИ ===================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id)

    if await is_subscribed(user.id, context):
        await update.message.reply_text(SUCCESS_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    register_user(user.id)

    if query.data == "check_sub":
        if await is_subscribed(user.id, context):
            await query.edit_message_text(SUCCESS_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard())
        else:
            await query.edit_message_text(NOT_SUBSCRIBED_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard())

    elif query.data == "participate":
        if await is_subscribed(user.id, context):
            await query.edit_message_text(CONTEST_TEXT, parse_mode="HTML")
        else:
            await query.edit_message_text(NOT_SUBSCRIBED_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id)
    if await is_subscribed(user.id, context):
        await update.message.reply_text("Используйте кнопку «УЧАВСТВОВАТЬ» ниже.", parse_mode="HTML", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard())

# =================== MAIN ===================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
