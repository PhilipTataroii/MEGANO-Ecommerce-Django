
"""Проверка номеров для учебной платёжной системы."""


def validate_payment_number(number):
    """Проверяет формат и чётность учебного номера."""
    number = str(number)

    if not number.isascii() or not number.isdecimal():
        raise ValueError("Номер должен содержать только цифры.")

    if not 1 <= len(number) <= 8:
        raise ValueError("Номер должен содержать не более 8 цифр.")

    if int(number) % 2 != 0:
        raise ValueError("Номер должен быть чётным.")

    return number


def process_payment(number):
    """Имитирует ответ платёжного сервиса."""
    number = validate_payment_number(number)

    if number.endswith("0"):
        return False, "Платёж отклонён учебной платёжной системой."

    return True, ""
