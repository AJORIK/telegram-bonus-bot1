import logging
import os
import json
import asyncio
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
#  НАСТРОЙКИ — ЗАПОЛНИТЕ ПЕРЕД ЗАПУСКОМ
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")       # Токен от @BotFather
CHANNEL_ID = os.getenv("CHANNEL_ID", "@PromoRadar_WB")       # @username или числовой ID канала
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/PromoRadar_WB")  # Ссылка на канал

# Интервал рассылки в секундах (3 часа = 10800 секунд)
MAILING_INTERVAL = int(os.getenv("MAILING_INTERVAL", "10800"))

# Файл для хранения ID пользователей
USERS_FILE = "users.json"

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
#  📬 ТЕКСТ АВТОМАТИЧЕСКОЙ РАССЫЛКИ (каждые 3 часа)
# ============================================================
MAILING_TEXT = """
<a href="https://flagmanway61.com/c8ffaea0c">FLAGMAN</a> — твой игровой рай с фриспинами, щедрыми бонусами и настоящими джекпотами🔥

🎁 <b>Welcome Pack:</b>

💸 <b>+125%</b> к первому депозиту — начни с бонусом!

🎰 <b>600 FS</b> за второе пополнение — крути без ограничений!

💰 <b>+125%</b> к третьему депозиту — удвой свой шанс на выигрыш!
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
#  СОХРАНЕНИЕ / ЗАГРУЗКА ПОЛЬЗОВАТЕЛЕЙ
# ============================================================
def load_users() -> set:
    """Загружает список ID пользователей из файла."""
    try:
        if Path(USERS_FILE).exists():
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                return set(data)
    except Exception as e:
        logger.error(f"Ошибка загрузки пользователей: {e}")
    return set()


def save_users(users: set) -> None:
    """Сохраняет список ID пользователей в файл."""
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователей: {e}")


# Глобальный набор ID всех пользователей бота
all_users = load_users()


def register_user(user_id: int) -> None:
    """Регистрирует нового пользователя."""
    if user_id not in all_users:
        all_users.add(user_id)
        save_users(all_users)
        logger.info(f"Новый пользователь зарегистрирован: {user_id}. Всего: {len(all_users)}")


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


def get_mailing_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для рассылки с кнопкой 'Получить бонус'."""
    keyboard = [
        [InlineKeyboardButton("🎁 ПОЛУЧИТЬ БОНУС", url="https://flagmanway61.com/c8ffaea0c")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================================
#  ОБРАБОТЧИКИ КОМАНД
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    logger.info(f"Пользователь {user.full_name} ({user.id}) запустил бота")
    
    # Регистрируем пользователя для рассылки
    register_user(user.id)

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
    register_user(user.id)
    
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
    register_user(user.id)
    
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
    register_user(user.id)

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
    register_user(user.id)
    
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
#  📬 АВТОМАТИЧЕСКАЯ РАССЫЛКА КАЖДЫЕ 3 ЧАСА
# ============================================================
async def send_mailing(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет рекламное сообщение всем пользователям бота."""
    users = load_users()
    if not users:
        logger.info("Рассылка: нет пользователей")
        return
    
    logger.info(f"📬 Начинаю рассылку для {len(users)} пользователей...")
    
    success = 0
    failed = 0
    blocked = []
    
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=MAILING_TEXT,
                parse_mode="HTML",
                reply_markup=get_mailing_keyboard(),
                disable_web_page_preview=False,
            )
            success += 1
            # Пауза чтобы не превысить лимиты Telegram API
            await asyncio.sleep(0.1)
        except Exception as e:
            error_msg = str(e).lower()
            if "blocked" in error_msg or "deactivated" in error_msg or "not found" in error_msg:
                blocked.append(user_id)
                logger.info(f"Пользователь {user_id} заблокировал бота — удаляю из базы")
            else:
                logger.error(f"Ошибка отправки для {user_id}: {e}")
            failed += 1
    
    # Удаляем заблокировавших пользователей из базы
    if blocked:
        updated_users = users - set(blocked)
        save_users(updated_users)
        all_users.clear()
        all_users.update(updated_users)
        logger.info(f"Удалено {len(blocked)} заблокировавших пользователей")
    
    logger.info(f"📬 Рассылка завершена! Успешно: {success}, Ошибок: {failed}")


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

    # ── Запуск автоматической рассылки каждые 3 часа ──
    job_queue = app.job_queue
    job_queue.run_repeating(
        send_mailing,
        interval=MAILING_INTERVAL,   # Каждые 3 часа (10800 секунд)
        first=60,                     # Первая рассылка через 60 секунд после старта
        name="mailing_3h",
    )
    logger.info(f"📬 Рассылка настроена: каждые {MAILING_INTERVAL // 3600} ч. {(MAILING_INTERVAL % 3600) // 60} мин.")

    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
    print(f"📬 Рассылка каждые {MAILING_INTERVAL} секунд ({MAILING_INTERVAL // 3600} часа)")
    print(f"👥 Пользователей в базе: {len(all_users)}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
