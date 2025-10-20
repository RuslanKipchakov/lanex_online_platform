from aiogram import Router, types, F
from telegram.keyboards import get_main_menu, get_levels_menu, applications_menu
from database.crud.user_session import create_user_session
from database.crud.application import read_application_by_user_id
from database.base import AsyncSessionLocal

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
    telegram_id = callback.from_user.id

    async with AsyncSessionLocal() as session:
        apps = await read_application_by_user_id(session, telegram_id)

    if not apps:
        await callback.message.edit_text(
            "У вас пока нет заявок.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")]
            ])
        )
        await callback.answer()
        return

    app_buttons = [
        {"id": app.id, "name": app.applicant_name, "date": app.created_at.strftime("%Y-%m-%d")}
        for app in apps
    ]

    await callback.message.edit_text(
        "Ваши заявки:",
        reply_markup=applications_menu(app_buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "check_level")
async def show_levels(callback: types.CallbackQuery):
    init_data = getattr(callback.message, 'web_app_data', None)

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
