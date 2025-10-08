from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import time

# BASE_URL = "https://innovative-intuition-mynewenv.up.railway.app"
# BASE_URL = "https://lanexonlineplatform-production.up.railway.app"
BASE_URL = "https://unsupplied-martina-theoretically.ngrok-free.dev"


def versioned_url(path: str) -> str:
    """Добавляет параметр версии, чтобы обойти кэш Telegram WebView"""
    return f"{BASE_URL}{path}?v={int(time.time())}"


# Главное меню
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="Оставить заявку на обучение",
        web_app=WebAppInfo(url=versioned_url("/html_pages/application_page/application_page.html"))
    )],
    [InlineKeyboardButton(text="Изменить заявку", callback_data="update_application")],
    [InlineKeyboardButton(text="Проверить свой уровень", callback_data="check_level")]
])

# Меню с уровнями тестов (+ кнопка Назад внизу)
levels_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="Starter",
        web_app=WebAppInfo(url=versioned_url("/html_pages/test_pages/levels/starter/starter_page.html"))
    )],
    [InlineKeyboardButton(
        text="Elementary",
        web_app=WebAppInfo(url=versioned_url("/html_pages/test_pages/levels/elementary/elementary_page.html"))
    )],
    [InlineKeyboardButton(
        text="Pre-Intermediate",
        web_app=WebAppInfo(url=versioned_url("/html_pages/test_pages/levels/pre_intermediate/pre_intermediate_page.html"))
    )],
    [InlineKeyboardButton(
        text="Intermediate",
        web_app=WebAppInfo(url=versioned_url("/html_pages/test_pages/levels/intermediate/intermediate_page.html"))
    )],
    [InlineKeyboardButton(
        text="Upper-Intermediate",
        web_app=WebAppInfo(url=versioned_url("/html_pages/test_pages/levels/upper_intermediate/upper_intermediate_page.html"))
    )],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")]
])

# Меню с заявками (динамическое)
def applications_menu(applications: list[dict]) -> InlineKeyboardMarkup:
    """
    applications = [{"id": 1, "name": "Ruslan", "date": "2025-09-29"}, ...]
    """
    buttons = []
    for app in applications:
        buttons.append([InlineKeyboardButton(
            text=f"{app['name']} ({app['date']})",
            callback_data=f"edit_app_{app['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
