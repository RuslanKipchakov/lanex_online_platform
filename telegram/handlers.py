from aiogram import Router, types, F
from telegram.keyboards import get_main_menu, get_levels_menu, applications_menu
from database.base import AsyncSessionLocal
from database.crud.user_session import create_user_session

router = Router()


def register_handlers(dp):
    dp.include_router(router)


@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    telegram_id = message.from_user.id
    telegram_username = message.from_user.username

    async with AsyncSessionLocal() as session:
        await create_user_session(session, telegram_id, telegram_username)

    await message.answer(
        "Привет! 👋 Я бот Lanex Education.",
        reply_markup=get_main_menu()
    )


@router.callback_query(F.data == "update_application")
async def handle_update_application(callback: types.CallbackQuery):
    fake_apps = [
        {"id": 1, "name": "Ruslan", "date": "2025-09-29"},
        {"id": 2, "name": "Anna", "date": "2025-09-20"},
    ]
    await callback.message.edit_text(
        "Ваши заявки:",
        reply_markup=applications_menu(fake_apps)
    )
    await callback.answer()


@router.callback_query(F.data == "check_level")
async def show_levels(callback: types.CallbackQuery):
    # Get init data from the callback to pass to WebApp
    init_data = callback.message.web_app_data if hasattr(callback.message, 'web_app_data') else None

    await callback.message.edit_text(
        "Выберите уровень теста:",
        reply_markup=get_levels_menu(init_data)
    )
    await callback.answer()


@router.callback_query(F.data == "go_back")
async def handle_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()