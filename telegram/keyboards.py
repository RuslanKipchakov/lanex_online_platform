from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import time
import urllib.parse

BASE_URL = "https://lanexonlineplatform-mynewenv.up.railway.app"


def versioned_url(path: str, init_data: str = None) -> str:
    """Добавляет параметр версии и Telegram initData если доступно"""
    url = f"{BASE_URL}{path}?v={int(time.time())}"

    if init_data:
        # Add Telegram WebApp init data
        url += f"&tgWebAppData={urllib.parse.quote(init_data)}"

    return url


# Главное меню
def get_main_menu(init_data: str = None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Оставить заявку на обучение",
            web_app=WebAppInfo(url=versioned_url("/html_pages/application_page/application_page.html", init_data))
        )],
        [InlineKeyboardButton(text="Изменить заявку", callback_data="update_application")],
        [InlineKeyboardButton(text="Проверить свой уровень", callback_data="check_level")]
    ])


# Меню с уровнями тестов
def get_levels_menu(init_data: str = None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Starter",
            web_app=WebAppInfo(url=versioned_url("/html_pages/test_pages/levels/starter/starter_page.html", init_data))
        )],
        [InlineKeyboardButton(
            text="Elementary",
            web_app=WebAppInfo(
                url=versioned_url("/html_pages/test_pages/levels/elementary/elementary_page.html", init_data))
        )],
        [InlineKeyboardButton(
            text="Pre-Intermediate",
            web_app=WebAppInfo(
                url=versioned_url("/html_pages/test_pages/levels/pre_intermediate/pre_intermediate_page.html",
                                  init_data))
        )],
        [InlineKeyboardButton(
            text="Intermediate",
            web_app=WebAppInfo(
                url=versioned_url("/html_pages/test_pages/levels/intermediate/intermediate_page.html", init_data))
        )],
        [InlineKeyboardButton(
            text="Upper-Intermediate",
            web_app=WebAppInfo(
                url=versioned_url("/html_pages/test_pages/levels/upper_intermediate/upper_intermediate_page.html",
                                  init_data))
        )],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")]
    ])


# Меню с заявками (динамическое)
def applications_menu(applications: list[dict], init_data: str = None) -> InlineKeyboardMarkup:
    buttons = []
    for app in applications:
        buttons.append([InlineKeyboardButton(
            text=f"{app['name']} ({app['date']})",
            callback_data=f"edit_app_{app['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)