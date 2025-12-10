def normalize_phone(phone: str) -> str:
    """
    Убирает все пробелы из номера телефона.
    Можно при необходимости добавить проверку на + в начале.
    """
    if not phone:
        return ""
    # Оставляем только цифры и знак + в начале
    phone = phone.strip()
    if phone.startswith("+"):
        return "+" + phone[1:].replace(" ", "")
    return phone.replace(" ", "")
