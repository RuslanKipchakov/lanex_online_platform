"""
Обработчики Telegram-бота Lanex Online Platform.

Содержит:
    - Команду /start
    - Обработку заявок (просмотр и редактирование)
    - Меню выбора уровня тестов
    - Кнопку "Назад"

Маршруты регистрируются в диспетчере через register_handlers().
"""

from aiogram import Dispatcher, F, Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.base import AsyncSessionLocal
from database.crud.application import read_application_by_user_id
from database.crud.user_session import create_user_session
from logging_config import logger
from telegram.keyboards import (
    applications_menu,
    get_levels_menu,
    get_main_menu,
)

#  ИНИЦИАЛИЗАЦИЯ РОУТЕРА
router = Router()
_handlers_registered = False


def get_callback_message(
    callback: types.CallbackQuery, handler_name: str
) -> types.Message | None:
    """
    Возвращает объект `Message` из CallbackQuery, если он доступен и редактируем.

    Параметры:
        callback (types.CallbackQuery): объект callback от Telegram.
        handler_name (str): название обработчика, используется для логирования.

    Возвращает:
        types.Message | None: объект сообщения, если он доступен;
        None, если сообщение отсутствует или недоступно для редактирования.

    Логирует предупреждение через logger.warning(), если `callback.message` None
    или является InaccessibleMessage.
    """
    if not isinstance(callback.message, Message):
        logger.warning(
            "%s: callback.message is None or Inaccessible. user_id=%s",
            handler_name,
            callback.from_user.id if callback.from_user else "unknown",
        )
        return None
    return callback.message


def register_handlers(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики Telegram-бота.
    Гарантирует однократную регистрацию в пределах приложения.
    """
    global _handlers_registered
    if _handlers_registered:
        logger.warning(
            "Attempt to register Telegram handlers more than once. Skipping."
        )
        return

    dp.include_router(router)
    _handlers_registered = True

    logger.info("Telegram handlers registered successfully.")


# ---------------------------------------------------------------------------
#  КОМАНДА /start
# ---------------------------------------------------------------------------


@router.message(F.text == "/start")
async def cmd_start(message: types.Message) -> None:
    """
    Обрабатывает команду /start:
        - Регистрирует пользователя в базе (если новый)
        - Показывает главное меню
    """
    user = message.from_user
    if user is None:
        logger.warning(
            "Received /start command without from_user. message_id=%s",
            message.message_id,
        )
        return

    telegram_id = user.id
    telegram_username = user.username or "unknown"

    async with AsyncSessionLocal() as session:
        await create_user_session(session, telegram_id, telegram_username)

    await message.answer(
        "Привет! 👋 Я бот Lanex Education.", reply_markup=get_main_menu()
    )


# ---------------------------------------------------------------------------
#  КНОПКА: Изменить заявку
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "update_application")
async def handle_update_application(callback: types.CallbackQuery) -> None:
    """
    Загружает список заявок пользователя.
    Если заявок нет — сообщает об этом и показывает кнопку "Назад".
    """
    telegram_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        apps = await read_application_by_user_id(session, telegram_id)

    message = get_callback_message(callback, "update_application")
    if message is None:
        await callback.answer()
        return

    # Нет заявок
    if not apps:
        await message.edit_text(
            "У вас пока нет заявок.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")]
                ]
            ),
        )
        await callback.answer()
        return

    # Есть заявки → формируем кнопки
    app_buttons = [
        {
            "id": app.id,
            "name": app.applicant_name,
            "date": app.created_at.strftime("%Y-%m-%d"),
        }
        for app in apps
    ]

    await message.edit_text(
        "Ваши заявки:",
        reply_markup=applications_menu(app_buttons),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
#  КНОПКА: Проверить уровень
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "check_level")
async def show_levels(callback: types.CallbackQuery) -> None:
    """
    Показывает меню выбора уровня теста.
    """
    message = get_callback_message(callback, "check_level")
    if message is None:
        await callback.answer()
        return

    await message.edit_text(
        "Выберите уровень теста:",
        reply_markup=get_levels_menu(),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
#  КНОПКА: Назад
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "go_back")
async def handle_back(callback: types.CallbackQuery) -> None:
    """
    Возвращает пользователя в главное меню.
    """
    message = get_callback_message(callback, "go_back")
    if message is None:
        await callback.answer()
        return

    await message.edit_text(
        "Главное меню:",
        reply_markup=get_main_menu(),
    )
    await callback.answer()
