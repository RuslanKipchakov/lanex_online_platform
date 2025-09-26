from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BASE_URL = "innovative-intuition-mynewenv.up.railway.app"

# Главное меню
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="Оставить заявку на обучение",
        web_app=WebAppInfo(url=f"{BASE_URL}/html_pages/application_page/application_page.html")
    )],
    [InlineKeyboardButton(text="Проверить свой уровень", callback_data="check_level")]
])

# Меню с уровнями тестов
levels_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(
        text="Starter",
        web_app=WebAppInfo(url=f"{BASE_URL}/html_pages/test_pages/levels/starter/starter_page.html")
    )],
    [InlineKeyboardButton(
        text="Elementary",
        web_app=WebAppInfo(url=f"{BASE_URL}/html_pages/test_pages/levels/elementary/elementary_page.html")
    )],
    [InlineKeyboardButton(
        text="Pre-Intermediate",
        web_app=WebAppInfo(url=f"{BASE_URL}/html_pages/test_pages/levels/pre_intermediate/pre_intermediate_page.html")
    )],
    [InlineKeyboardButton(
        text="Intermediate",
        web_app=WebAppInfo(url=f"{BASE_URL}/html_pages/test_pages/levels/intermediate/intermediate_page.html")
    )],
    [InlineKeyboardButton(
        text="Upper-Intermediate",
        web_app=WebAppInfo(url=f"{BASE_URL}/html_pages/test_pages/levels/upper_intermediate/upper_intermediate_page.html")
    )],
])
