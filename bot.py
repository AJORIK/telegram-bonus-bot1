import logging
import os
import json
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ============================================================
#  НАСТРОЙКИ
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@AutoXdrive")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/AutoXdrive")

USERS_FILE = "users.json"

# ============================================================
#  ТЕКСТЫ
# ============================================================
WELCOME_TEXT = """
🎉 <b>Добро пожаловать!</b>

Чтобы участвовать в конкурсе, подпишитесь на наш канал 👇
После подписки нажмите <b>«✅ Проверить подписку»</b>
"""

SUCCESS_TEXT = """
🎊 <b>Вы подписаны на канал!</b>

Нажмите <b>«УЧАВСТВОВАТЬ»</b>, чтобы принять участие в конкурсе!
"""

NOT_SUBSCRIBED_TEXT = """
❌ <b>Вы ещё не подписались на канал!</b>

Пожалуйста, сначала подпишитесь на канал,
а затем нажмите «✅ Проверить подписку».
"""

PARTICIPATE_TEXT = """
✅ <b>Теперь вы участвуете в конкурсе!</b>

Результаты будут выложены в канале 5 апреля.
"""

ALREADY_PARTICIPATE_TEXT = """
⚠️ <b>Вы уже участвуете в конкурсе!</b>

Ждите результатов, которые будут опубликованы в канале 5 апреля.
"""

# ============================================================
#  ЛОГИРОВАНИЕ
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================================
#  СОХРАНЕНИЕ / ЗАГРУЗКА ПОЛЬЗОВАТЕЛЕЙ
# ============================================================
def load_users() -> set:
    try:
        if Path(USERS_FILE).exists():
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                return set(data)
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей: {e}")
    return set()


def save_users(users: set) -> None:
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователей: {e}")


all_users = load_users()
participants = set()  # хранит ID пользователей, которые нажали «УЧАВСТВОВАТЬ»

# ============================================================
#  ПРОВЕРКА ПОДПИСКИ
# ============================================================
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_ID, user_id=user_id
        )
        return member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER,
        ]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False


# ============================================================
#  КЛАВИАТУРЫ
# ============================================================
def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("УЧАВСТВОВАТЬ", callback_data="participate")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_menu")]]
    return InlineKeyboardMarkup(keyboard)


# ============================================================
#  ОБРАБОТЧИКИ КОМАНД
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"Пользователь {user.full_name} ({user.id}) запустил бота")
    all_users.add(user.id)

    if await is_subscribed(user.id, context):
        await update.message.reply_text(
            SUCCESS_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
        )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    if await is_subscribed(user.id, context):
        await update.message.reply_text(
            SUCCESS_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
        )


# ============================================================
#  ОБРАБОТЧИКИ CALLBACK-КНОПОК
# ============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "check_sub":
        if await is_subscribed(user.id, context):
            await query.edit_message_text(
                SUCCESS_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                NOT_SUBSCRIBED_TEXT,
                parse_mode="HTML",
                reply_markup=get_subscribe_keyboard(),
            )

    elif query.data == "participate":
        if not await is_subscribed(user.id, context):
            await query.edit_message_text(
                WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
            )
            return

        if user.id in participants:
            await query.edit_message_text(
                ALREADY_PARTICIPATE_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard()
            )
        else:
            participants.add(user.id)
            await query.edit_message_text(
                PARTICIPATE_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard()
            )

    elif query.data == "back_menu":
        if await is_subscribed(user.id, context):
            await query.edit_message_text(
                SUCCESS_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
            )


# ============================================================
#  ОБРАБОТКА ОБЫЧНЫХ СООБЩЕНИЙ
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    if await is_subscribed(user.id, context):
        await update.message.reply_text(
            "Нажмите кнопку «УЧАВСТВОВАТЬ» для участия в конкурсе.",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
        )


# ============================================================
#  ЗАПУСК БОТА
# ============================================================
def main() -> None:
    if BOT_TOKEN == "ВАШ_ТОКЕН_БОТА":
        print("❌ ОШИБКА: Укажите токен бота в переменной BOT_TOKEN!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    print(f"👥 Пользователей в базе: {len(all_users)}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
