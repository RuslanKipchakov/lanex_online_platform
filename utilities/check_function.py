import asyncio

# ==== Глобальные ключи правильных ответов ====
global_answer_key = {
    "starter": {
        "task1": {
            "1": "C", "2": "C", "3": "B", "4": "C", "5": "C",
            "6": "B", "7": "A", "8": "B", "9": "C", "10": "D",
            "11": "B", "12": "C", "13": "C", "14": "B", "15": "B",
            "16": "A", "17": "C", "18": "C", "19": "A", "20": "B",
        },
        "task2": {
            "1": "C", "2": "C", "3": "A", "4": "A", "5": "A",
            "6": "A", "7": "B", "8": "A", "9": "A", "10": "C",
            "11": "A", "12": "B", "13": "A", "14": "A", "15": "B",
            "16": "A", "17": "B", "18": "A", "19": "A", "20": "A",
        },
    },
    "elementary": {
        "task1": {
            "1": "B", "2": "A", "3": "B", "4": "C", "5": "B",
            "6": "A", "7": "B", "8": "C", "9": "A", "10": "A",
            "11": "B", "12": "A", "13": "B", "14": "B", "15": "A"
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
            "10": "False"
        },
        "task3": {
            "1": "B", "2": "B", "3": "B", "4": "B", "5": "B",
            "6": "B", "7": "B", "8": "A", "9": "C", "10": "C"
        }
    },
    "pre_intermediate": {
        "task1": {
            "1": "B", "2": "B", "3": "A", "4": "B", "5": "B",
            "6": "C", "7": "C", "8": "A", "9": "B", "10": "B",
            "11": "B", "12": "C", "13": "B", "14": "C", "15": "B"
        },
        "task2": {
            "1": "C", "2": "B", "3": "B", "4": "C",
            "5": ["four days", "4 days"],
            "6": "pasta",
            "7": ["90 minutes", "ninety minutes"],
            "8": "south",
            "9": ["3", "three"],
            "10": ["2", "two"],
            "11": ["1", "one"],
            "12": "C"
        },
        "task3": {
            "1": "B", "2": "C", "3": "D", "4": "B", "5": "A",
            "6": "B", "7": "B", "8": "B", "9": "A", "10": "C",
            "11": "C", "12": "A", "13": "A", "14": "C", "15": "B"
        }
    },
    "intermediate": {
        "task1": {
            "1": "C", "2": "B", "3": "A", "4": "C", "5": "B",
            "6": "B", "7": "A", "8": "B", "9": "B", "10": "A",
            "11": "A", "12": "C", "13": "B", "14": "B", "15": "B"
        },
        "task2": {
            "1": "C", "2": "B", "3": "D", "4": "C", "5": "C",
            "6": "school",
            "7": "rebuild",
            "8": "families",
            "9": "flight",
            "10": "next year",
            "11": "1",
            "12": "2",
            "13": "4",
            "14": "3",
            "15": "5"
        },
        "task3": {
            "1": "C", "2": "C", "3": "C", "4": "B", "5": "D",
            "6": "C", "7": "C", "8": "C", "9": "D", "10": "C",
            "11": "B", "12": "C", "13": "C", "14": "D", "15": "C"
        }
    },
    "upper_intermediate": {
        "task1": {
            "1": "A", "2": "A", "3": "A", "4": "C", "5": "A",
            "6": "A", "7": "B", "8": "B", "9": "B", "10": "A",
            "11": "A", "12": "C", "13": "C", "14": "A", "15": "C"
        },
        "task2": {
            "1": "C", "2": "B", "3": "D", "4": "C", "5": "B",
            "6": "C", "7": "C", "8": "C", "9": "C", "10": "B"
        },
        "task3": {
            "1": "B", "2": "C", "3": "D", "4": "A", "5": "B",
            "6": "D", "7": "A", "8": "C", "9": "B", "10": "D",
            "11": "B"
        }
    }
}


# ==== Нормализация и проверка ====
def normalize_answer(ans: str) -> str:
    """Приводит ответ к стандартной форме для сравнения."""
    if not ans:
        return ""
    ans = ans.strip().lower()

    # Словесные числа → цифры
    mapping = {
        "one": "1", "two": "2", "three": "3",
        "four": "4", "five": "5", "six": "6",
        "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    }
    return mapping.get(ans, ans)


def is_correct(user_answer: str, correct_answer) -> bool:
    """Проверяет, совпадает ли ответ пользователя с правильным."""
    user_norm = normalize_answer(user_answer)

    if isinstance(correct_answer, str):
        return user_norm == normalize_answer(correct_answer)

    if isinstance(correct_answer, (list, tuple, set)):
        return user_norm in [normalize_answer(a) for a in correct_answer]

    return False


# ==== Основная функция проверки ====
async def check_test_results(frontend_response: dict) -> dict:
    """Проверяет ответы пользователя по ключу правильных ответов."""
    result = {}
    level = frontend_response["level"]
    level_key = global_answer_key.get(level, {})

    total_scores = []

    for task, answers in frontend_response["answers"].items():
        # Если для этого таска нет ключа → открытые задания
        if task not in level_key:
            result[task] = "open"
            continue

        # Проверка закрытых вопросов
        correct_answers = level_key[task]
        task_result = {}
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

    # Итоговый процент (среднее по всем таскам)
    if total_scores:
        avg_score = sum(total_scores) / len(total_scores) * 100
        result["total"] = f"{avg_score:.1f}%"
    else:
        result["total"] = "0%"

    return result
