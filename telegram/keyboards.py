"""
Клавиатуры Telegram WebApp и обычных кнопок для Lanex Online Platform.

Содержит:
    - Главное меню
    - Меню выбора уровней тестов
    - Динамическое меню с заявками пользователя

Все URL формируются через versioned_url() для обхода кэширования Telegram WebView.
"""

import time
import urllib.parse
from typing import List, Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import settings

BASE_URL: str = settings.base_url


def versioned_url(path: str, init_data: Optional[str] = None) -> str:
    """
    Формирует WebApp URL с уникальной временной меткой, чтобы Telegram
    всегда загружал свежую версию страницы.

    Args:
        path (str): относительный путь (например: "/html_pages/...").
        init_data (str | None): Telegram initData (для авторизации WebApp).

    Returns:
        str: Полный URL с параметрами для обхода кэша.
    """
    timestamp = int(time.time())
    sep = "&" if "?" in path else "?"

    url = f"{BASE_URL}{path}{sep}v={timestamp}"

    if init_data:
        url += f"&tgWebAppData={urllib.parse.quote(init_data)}"

    url += f"&_nocache={timestamp}"
    return url


# ---------------------------------------------------------------------------
#  Главное меню
# ---------------------------------------------------------------------------

def get_main_menu(init_data: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Возвращает главное меню с выбором действий:
        - Оставить заявку
        - Изменить заявку
        - Пройти тест на уровень
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Оставить заявку на обучение",
                web_app=WebAppInfo(
                    url=versioned_url("/html_pages/application_page/application_page.html", init_data)
                ),
            )
        ],
        [InlineKeyboardButton(text="Изменить заявку", callback_data="update_application")],
        [InlineKeyboardButton(text="Проверить свой уровень", callback_data="check_level")],
    ])


# ---------------------------------------------------------------------------
#  Меню выбора уровней тестов
# ---------------------------------------------------------------------------

LEVEL_BUTTONS = [
    ("Starter", "/html_pages/test_pages/levels/starter/starter_page.html"),
    ("Elementary", "/html_pages/test_pages/levels/elementary/elementary_page.html"),
    ("Pre-Intermediate", "/html_pages/test_pages/levels/pre_intermediate/pre_intermediate_page.html"),
    ("Intermediate", "/html_pages/test_pages/levels/intermediate/intermediate_page.html"),
    ("Upper-Intermediate", "/html_pages/test_pages/levels/upper_intermediate/upper_intermediate_page.html"),
]


def get_levels_menu(init_data: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Меню выбора уровня теста.
    Генерируется автоматически на основе LEVEL_BUTTONS.
    """
    rows = []
    for label, path in LEVEL_BUTTONS:
        rows.append([
            InlineKeyboardButton(
                text=label,
                web_app=WebAppInfo(url=versioned_url(path, init_data)),
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------------------------------------------------------------------
#  Динамическое меню заявок
# ---------------------------------------------------------------------------

def applications_menu(applications: List[dict], init_data: Optional[str] = None) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру со списком заявок пользователя.

    Args:
        applications (list[dict]): список заявок, каждая с полями:
            - id: int
            - name: str
            - date: str (формат отображения)
        init_data (str | None): Telegram WebApp initData

    Returns:
        InlineKeyboardMarkup: меню заявок
    """
    rows = []

    for app in applications:
        edit_url = versioned_url(
            f"/html_pages/application_page/application_page.html?edit_id={app['id']}",
            init_data,
        )
        rows.append([
            InlineKeyboardButton(
                text=f"{app['name']} ({app['date']})",
                web_app=WebAppInfo(url=edit_url),
            )
        ])

    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="go_back")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
