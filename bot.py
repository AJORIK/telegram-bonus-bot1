import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.error import BadRequest
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

all_users = set()


# ================== Работа с файлом пользователей ==================
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()
    except json.JSONDecodeError:
        logger.warning("users.json повреждён или пустой, создаю новый список пользователей")
        return set()


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(users), f, ensure_ascii=False, indent=2)


def register_user(user_id: int):
    if user_id not in all_users:
        all_users.add(user_id)
        save_users(all_users)
        logger.info(f"Новый пользователь: {user_id}")


all_users = load_users()


# ================== Вспомогательные функции ==================
def get_channel_url():
    channel_name = CHANNEL_ID.lstrip("@")
    return f"https://t.me/{channel_name}"


def subscribe_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Подписаться на канал", url=get_channel_url())],
        [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")]
    ])


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 УЧАВСТВОВАТЬ", callback_data="participate")]
    ])


async def safe_edit_message(query, text: str, reply_markup=None):
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    except BadRequest as e:
        error_text = str(e)
        if "Message is not modified" in error_text:
            logger.info("Сообщение не изменилось, пропускаю edit_message_text")
            await query.answer("Ничего не изменилось")
            return
        raise


# ================== Проверка подписки ==================
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in (
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER
        )
    except BadRequest as e:
        logger.warning(f"Ошибка проверки подписки: {e}")
        return False
    except Exception as e:
        logger.exception(f"Неожиданная ошибка проверки подписки: {e}")
        return False


# ================== Обработчики ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)

    if await is_subscribed(user_id, context):
        await update.message.reply_text(
            "✅ Вы подписаны! Нажмите УЧАВСТВОВАТЬ",
            reply_markup=main_keyboard()
        )
    else:
        await update.message.reply_text(
            "🎉 Подпишитесь на канал, затем нажмите «Проверить подписку».",
            reply_markup=subscribe_keyboard()
        )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    register_user(user_id)

    if query.data == "check_sub":
        if await is_subscribed(user_id, context):
            await safe_edit_message(
                query,
                "✅ Вы подписаны! Нажмите УЧАВСТВОВАТЬ",
                reply_markup=main_keyboard()
            )
        else:
            await safe_edit_message(
                query,
                "❌ Вы не подписаны! Сначала подпишитесь.",
                reply_markup=subscribe_keyboard()
            )

    elif query.data == "participate":
        if await is_subscribed(user_id, context):
            await safe_edit_message(
                query,
                "🎉 Теперь вы участвуете в конкурсе, результат 5 апреля!"
            )
        else:
            await safe_edit_message(
                query,
                "❌ Вы не подписаны! Сначала подпишитесь.",
                reply_markup=subscribe_keyboard()
            )


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)

    if await is_subscribed(user_id, context):
        await update.message.reply_text(
            "Используйте кнопку УЧАВСТВОВАТЬ",
            reply_markup=main_keyboard()
        )
    else:
        await update.message.reply_text(
            "Подпишитесь на канал и нажмите «Проверить подписку».",
            reply_markup=subscribe_keyboard()
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Ошибка при обработке update:", exc_info=context.error)


# ================== MAIN ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    app.add_error_handler(error_handler)

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
