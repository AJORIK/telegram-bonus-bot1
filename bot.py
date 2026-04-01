import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@AutoXdrive")
USERS_FILE = "users.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

all_users = set()

# ================== Работа с файлом пользователей ==================
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

def register_user(user_id: int):
    if user_id not in all_users:
        all_users.add(user_id)
        save_users(all_users)
        logger.info(f"Новый пользователь: {user_id}")

all_users = load_users()

# ================== Клавиатуры ==================
def subscribe_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/AutoXdrive")],
        [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")]
    ])

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 УЧАВСТВОВАТЬ", callback_data="participate")]
    ])

# ================== Проверка подписки ==================
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        logger.warning(f"Ошибка проверки подписки: {e}")
        return False

# ================== Обработчики ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    if await is_subscribed(user_id, context):
        await update.message.reply_text(
            "✅ Вы подписаны! Нажмите УЧАВСТВОВАТЬ", reply_markup=main_keyboard()
        )
    else:
        await update.message.reply_text(
            "🎉 Подпишитесь на канал, затем нажмите Проверить подписку",
            reply_markup=subscribe_keyboard()
        )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    register_user(user_id)

    if query.data == "check_sub":
        if await is_subscribed(user_id, context):
            await query.edit_message_text(
                "✅ Вы подписаны! Нажмите УЧАВСТВОВАТЬ", reply_markup=main_keyboard()
            )
        else:
            await query.edit_message_text(
                "❌ Вы не подписаны! Сначала подпишитесь.", reply_markup=subscribe_keyboard()
            )
    elif query.data == "participate":
        if await is_subscribed(user_id, context):
            await query.edit_message_text("🎉 Теперь вы участвуете в конкурсе, результат 5 апреля!")
        else:
            await query.edit_message_text(
                "❌ Вы не подписаны! Сначала подпишитесь.", reply_markup=subscribe_keyboard()
            )

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    if await is_subscribed(user_id, context):
        await update.message.reply_text("Используйте кнопку УЧАВСТВОВАТЬ", reply_markup=main_keyboard())
    else:
        await update.message.reply_text(
            "Подпишитесь на канал и нажмите Проверить подписку", reply_markup=subscribe_keyboard()
        )

# ================== MAIN ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
