from aiogram import Router, types, F
from telegram.keyboards import main_menu, levels_menu

router = Router()


def register_handlers(dp):
    dp.include_router(router)


# ✅ обработчик команды /start (aiogram v3)
@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! 👋 Я бот Lanex Education.",
        reply_markup=main_menu
    )


# ✅ обработчик callback кнопки "Проверить свой уровень"
@router.callback_query(F.data == "check_level")
async def show_levels(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите уровень теста:",
        reply_markup=levels_menu
    )
    await callback.answer()  # убираем «часики» у кнопки
