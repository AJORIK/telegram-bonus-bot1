import logging
import os
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
#  НАСТРОЙКИ — ЗАПОЛНИТЕ ПЕРЕД ЗАПУСКОМ
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")       # Токен от @BotFather
CHANNEL_ID = os.getenv("CHANNEL_ID", "@PromoRadar_WB")       # @username или числовой ID канала
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/PromoRadar_WB")  # Ссылка на канал

# ============================================================
#  ТЕКСТЫ СООБЩЕНИЙ (HTML-разметка)
# ============================================================

# Приветствие — показывается при /start если НЕ подписан
WELCOME_TEXT = """
🎉 <b>Добро пожаловать!</b>

Чтобы получить доступ ко всем функциям бота
и забрать свой <b>🎁 бонус</b>, подпишитесь на наш канал 👇

После подписки нажмите <b>«✅ Проверить подписку»</b>
"""

# Текст после успешной подписки
SUCCESS_TEXT = """
🎊 <b>Отлично! Вы подписаны на канал!</b>

Теперь вам доступны все функции бота.
Нажмите <b>«🎁 Забрать бонус»</b>, чтобы получить подарок!
"""

# Текст если пользователь не подписан
NOT_SUBSCRIBED_TEXT = """
❌ <b>Вы ещё не подписались на канал!</b>

Пожалуйста, сначала подпишитесь на канал,
а затем нажмите «✅ Проверить подписку».
"""

# ============================================================
#  🎁 БОНУС — НАСТРОЙТЕ ПОД СЕБЯ
# ============================================================
BONUS_TEXT = """
🎁 <b>Ваш бонус!</b>

🔥 Поздравляем! Вот ваш подарок:

━━━━━━━━━━━━━━━━━━
🎟 Промокод: <code>BBR</code>
🎰 Бонус: <b>225 Free Spins</b>
💰 + <b>600%</b> к депозиту
━━━━━━━━━━━━━━━━━━

Активируйте промокод <code>BBR</code> и получите
225 фриспинов и 600% к вашему депозиту! 🚀

Спасибо, что подписались на наш канал! ❤️
"""

# Текст меню
MENU_TEXT = """
📋 <b>Главное меню</b>

Вот что я умею:
• 🎁 Забрать бонус
• 📢 Информация о канале
• ❓ Помощь

Выберите нужный пункт 👇
"""

# ============================================================
#  ЛОГИРОВАНИЕ
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Храним ID пользователей, которые уже забрали бонус
bonus_claimed_users = set()


# ============================================================
#  ПРОВЕРКА ПОДПИСКИ
# ============================================================
async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, подписан ли пользователь на канал."""
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
    """Клавиатура с кнопкой подписки и проверки."""
    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню после успешной подписки."""
    keyboard = [
        [InlineKeyboardButton("🎁 Забрать бонус", callback_data="get_bonus")],
        [
            InlineKeyboardButton("📢 О канале", callback_data="about_channel"),
            InlineKeyboardButton("❓ Помощь", url="https://t.me/suerde"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка 'Назад в меню'."""
    keyboard = [[InlineKeyboardButton("◀️ Назад в меню", callback_data="back_menu")]]
    return InlineKeyboardMarkup(keyboard)


# ============================================================
#  ОБРАБОТЧИКИ КОМАНД
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    logger.info(f"Пользователь {user.full_name} ({user.id}) запустил бота")

    if await is_subscribed(user.id, context):
        await update.message.reply_text(
            SUCCESS_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
        )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /menu."""
    user = update.effective_user
    if await is_subscribed(user.id, context):
        await update.message.reply_text(
            MENU_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
        )


async def bonus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /bonus."""
    user = update.effective_user
    if await is_subscribed(user.id, context):
        bonus_claimed_users.add(user.id)
        await update.message.reply_text(
            BONUS_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard()
        )
    else:
        await update.message.reply_text(
            WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
        )


# ============================================================
#  ОБРАБОТЧИКИ CALLBACK-КНОПОК
# ============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на inline-кнопки."""
    query = update.callback_query
    await query.answer()
    user = query.from_user

    # ── Проверка подписки ──
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

    # ── 🎁 Забрать бонус ──
    elif query.data == "get_bonus":
        if not await is_subscribed(user.id, context):
            await query.edit_message_text(
                WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
            )
            return

        bonus_claimed_users.add(user.id)
        logger.info(f"Пользователь {user.full_name} ({user.id}) забрал бонус")

        await query.edit_message_text(
            BONUS_TEXT, parse_mode="HTML", reply_markup=get_back_keyboard()
        )

    # ── О канале ──
    elif query.data == "about_channel":
        if not await is_subscribed(user.id, context):
            await query.edit_message_text(
                WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
            )
            return
        text = (
            f"📢 <b>О канале</b>\n\n"
            f"В этом канале вы ежедневно можете получить лучшие бонусы!\n\n"
            f"🔗 Ссылка: {CHANNEL_URL}"
        )
        await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=get_back_keyboard()
        )

    # ── Назад в меню ──
    elif query.data == "back_menu":
        if await is_subscribed(user.id, context):
            await query.edit_message_text(
                MENU_TEXT, parse_mode="HTML", reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                WELCOME_TEXT, parse_mode="HTML", reply_markup=get_subscribe_keyboard()
            )


# ============================================================
#  ОБРАБОТКА ОБЫЧНЫХ СООБЩЕНИЙ
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Перехватывает любое текстовое сообщение и проверяет подписку."""
    user = update.effective_user
    if await is_subscribed(user.id, context):
        await update.message.reply_text(
            "Используйте /menu для навигации 😊",
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
    """Запуск бота."""
    if BOT_TOKEN == "ВАШ_ТОКЕН_БОТА":
        print("❌ ОШИБКА: Укажите токен бота в переменной BOT_TOKEN!")
        print("   Получите токен у @BotFather в Telegram")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("bonus", bonus_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
