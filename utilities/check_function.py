"""
Функции для проверки тестов пользователя по ключу правильных ответов.

Содержит:
    - глобальный словарь ключей ответов;
    - нормализацию ответов;
    - проверку отдельного ответа;
    - асинхронную проверку всех результатов теста.
"""

from typing import Any, Dict, Iterable, Optional, Union

from pydantic import BaseModel

# Тип ключей: уровень -> таск -> номер вопроса -> правильный ответ
AnswerKeyType = Dict[str, Dict[str, Union[str, list[str]]]]

# ==== Глобальные ключи правильных ответов ====
global_answer_key: Dict[str, AnswerKeyType] = {
    "Starter": {
        "task1": {
            "1": "C",
            "2": "C",
            "3": "B",
            "4": "C",
            "5": "C",
            "6": "B",
            "7": "A",
            "8": "B",
            "9": "C",
            "10": "D",
            "11": "B",
            "12": "C",
            "13": "C",
            "14": "B",
            "15": "B",
            "16": "A",
            "17": "C",
            "18": "C",
            "19": "A",
            "20": "B",
        },
        "task2": {
            "1": "C",
            "2": "C",
            "3": "A",
            "4": "A",
            "5": "A",
            "6": "A",
            "7": "B",
            "8": "A",
            "9": "A",
            "10": "C",
            "11": "A",
            "12": "B",
            "13": "A",
            "14": "A",
            "15": "B",
            "16": "A",
            "17": "B",
            "18": "A",
            "19": "A",
            "20": "A",
        },
    },
    "Elementary": {
        "task1": {
            "1": "B",
            "2": "A",
            "3": "B",
            "4": "C",
            "5": "B",
            "6": "A",
            "7": "B",
            "8": "C",
            "9": "A",
            "10": "A",
            "11": "B",
            "12": "A",
            "13": "B",
            "14": "B",
            "15": "A",
        },
        "task2": {
            "1": "B",
            "2": "False",
            "3": ["Monday", "Mon"],
            "4": "B",
            "5": "C",
            "6": "True",
            "7": ["2", "two"],
            "8": "C",
            "9": "C",
            "10": "False",
        },
        "task3": {
            "1": "B",
            "2": "B",
            "3": "B",
            "4": "B",
            "5": "B",
            "6": "B",
            "7": "B",
            "8": "A",
            "9": "C",
            "10": "C",
        },
    },
    "Pre-Intermediate": {
        "task1": {
            "1": "B",
            "2": "B",
            "3": "A",
            "4": "B",
            "5": "B",
            "6": "C",
            "7": "C",
            "8": "A",
            "9": "B",
            "10": "B",
            "11": "B",
            "12": "C",
            "13": "B",
            "14": "C",
            "15": "B",
        },
        "task2": {
            "1": "C",
            "2": "B",
            "3": "B",
            "4": "C",
            "5": ["four days", "4 days"],
            "6": "pasta",
            "7": ["90 minutes", "ninety minutes"],
            "8": "south",
            "9": ["3", "three"],
            "10": ["2", "two"],
            "11": ["1", "one"],
            "12": "C",
        },
        "task3": {
            "1": "B",
            "2": "C",
            "3": "D",
            "4": "B",
            "5": "A",
            "6": "B",
            "7": "B",
            "8": "B",
            "9": "A",
            "10": "C",
            "11": "C",
            "12": "A",
            "13": "A",
            "14": "C",
            "15": "B",
        },
    },
    "Intermediate": {
        "task1": {
            "1": "C",
            "2": "B",
            "3": "A",
            "4": "C",
            "5": "B",
            "6": "B",
            "7": "A",
            "8": "B",
            "9": "B",
            "10": "A",
            "11": "A",
            "12": "C",
            "13": "B",
            "14": "B",
            "15": "B",
        },
        "task2": {
            "1": "C",
            "2": "B",
            "3": "D",
            "4": "C",
            "5": "C",
            "6": "school",
            "7": "rebuild",
            "8": "families",
            "9": "flight",
            "10": "next year",
            "11": "1",
            "12": "2",
            "13": "4",
            "14": "3",
            "15": "5",
        },
        "task3": {
            "1": "C",
            "2": "C",
            "3": "C",
            "4": "B",
            "5": "D",
            "6": "C",
            "7": "C",
            "8": "C",
            "9": "D",
            "10": "C",
            "11": "B",
            "12": "C",
            "13": "C",
            "14": "D",
            "15": "C",
        },
    },
    "Upper-Intermediate": {
        "task1": {
            "1": "A",
            "2": "A",
            "3": "A",
            "4": "C",
            "5": "A",
            "6": "A",
            "7": "B",
            "8": "B",
            "9": "B",
            "10": "A",
            "11": "A",
            "12": "C",
            "13": "C",
            "14": "A",
            "15": "C",
        },
        "task2": {
            "1": "C",
            "2": "B",
            "3": "D",
            "4": "C",
            "5": "B",
            "6": "C",
            "7": "C",
            "8": "C",
            "9": "C",
            "10": "B",
        },
        "task3": {
            "1": "B",
            "2": "C",
            "3": "D",
            "4": "A",
            "5": "B",
            "6": "D",
            "7": "A",
            "8": "C",
            "9": "B",
            "10": "D",
            "11": "B",
        },
    },
}


class FrontendTestPayload(BaseModel):
    """
    Модель входных данных теста, получаемых от frontend.

    Attributes:
        level (str): Уровень теста (Starter, Elementary, Pre-Intermediate и т.д.).
        username (str): Имя пользователя или идентификатор ученика.
        answers (Dict[str, Dict[str, str]]): Ответы пользователя,
            где ключ первого уровня — название задания (task1, task2),
            а второго — номер вопроса и ответ пользователя.
    """

    level: str
    username: str
    answers: Dict[str, Dict[str, str]]


def normalize_answer(ans: str) -> str:
    """
    Приводит ответ пользователя к стандартной форме для сравнения.

    Преобразования:
        - Стриминг пробелов.
        - Приведение к нижнему регистру.
        - Словесные числа → цифры.

    Аргументы:
        ans (str): Исходный ответ пользователя.

    Returns:
        str: Нормализованный ответ.
    """
    if not ans:
        return ""
    ans = ans.strip().lower()
    mapping = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
    }
    return mapping.get(ans, ans)


def is_correct(user_answer: str, correct_answer: Optional[str | Iterable[str]]) -> bool:
    """
    Проверяет, совпадает ли ответ пользователя с правильным.

    Аргументы:
        user_answer (str): Ответ пользователя.
        correct_answer (str | Iterable[str] | None):
            Правильный ответ, набор допустимых вариантов
            или None, если ключ отсутствует.

    Returns:
        bool: True, если ответ верный, иначе False.
    """
    if not correct_answer:
        return False

    user_norm = normalize_answer(user_answer)

    if isinstance(correct_answer, str):
        return user_norm == normalize_answer(correct_answer)

    return user_norm in {normalize_answer(a) for a in correct_answer}


async def check_test_results(
    frontend_response: FrontendTestPayload,
) -> dict[str, Any]:
    """
    Асинхронно проверяет ответы пользователя по ключу правильных ответов.

    Аргументы:
        frontend_response (FrontendTestPayload): Валидированные данные от frontend.
            Пример:
                {
                    "level": "Starter",
                    "answers": {
                        "task1": {"1": "A", "2": "B", ...},
                        "task2": {...},
                        ...
                    }
                }

    Returns:
        dict: Результаты проверки с пометками "correct"/"incorrect" и общим процентом.
    """
    result: dict[str, Any] = {}
    level_key: AnswerKeyType = global_answer_key.get(frontend_response.level, {})
    total_scores = []

    for task, answers in frontend_response.answers.items():
        if task not in level_key:
            result[task] = "open"
            continue

        correct_answers = level_key[task]
        task_result: dict[str, str] = {}
        score = 0

        for q_num, user_answer in answers.items():
            if user_answer and is_correct(user_answer, correct_answers.get(q_num)):
                task_result[q_num] = "correct"
                score += 1
            else:
                task_result[q_num] = "incorrect"

        task_result["score"] = f"{score}/{len(correct_answers)}"
        result[task] = task_result
        total_scores.append(score / len(correct_answers))

    # Итоговый процент (среднее по всем закрытым таскам)
    result["total"] = (
        f"{sum(total_scores) / len(total_scores) * 100:.1f}%" if total_scores else "0%"
    )

    return result
