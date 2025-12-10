"""
Обработчики Telegram-бота Lanex Online Platform.

Содержит:
    - Команду /start
    - Обработку заявок (просмотр и редактирование)
    - Меню выбора уровня тестов
    - Кнопку "Назад"

Маршруты регистрируются в диспетчере через register_handlers().
"""

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from telegram.keyboards import (
    get_main_menu,
    get_levels_menu,
    applications_menu,
)

from database.crud.user_session import create_user_session
from database.crud.application import read_application_by_user_id
from database.base import AsyncSessionLocal


#  ИНИЦИАЛИЗАЦИЯ РОУТЕРА
router = Router()
_handlers_registered = False


def register_handlers(dp) -> None:
    """
    Регистрирует обработчики Telegram-бота.
    Гарантирует однократную регистрацию в пределах приложения.
    """
    global _handlers_registered
    if _handlers_registered:
        return

    dp.include_router(router)
    _handlers_registered = True

    print("✅ Telegram handlers registered successfully.")


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
    telegram_id = message.from_user.id
    telegram_username = message.from_user.username or "unknown"

    async with AsyncSessionLocal() as session:
        await create_user_session(session, telegram_id, telegram_username)

    await message.answer(
        "Привет! 👋 Я бот Lanex Education.",
        reply_markup=get_main_menu()
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

    # Нет заявок
    if not apps:
        await callback.message.edit_text(
            "У вас пока нет заявок.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")]
            ])
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

    await callback.message.edit_text(
        "Ваши заявки:",
        reply_markup=applications_menu(app_buttons)
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
    await callback.message.edit_text(
        "Выберите уровень теста:",
        reply_markup=get_levels_menu()
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
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()
