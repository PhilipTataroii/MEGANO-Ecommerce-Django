
from django.utils.translation import get_language


SUPPORTED_LANGUAGES = ("ru", "ro", "en")


def get_current_language():
    """Возвращает выбранный язык магазина."""
    language = (get_language() or "ru").split("-")[0]

    if language not in SUPPORTED_LANGUAGES:
        return "ru"

    return language


def get_translated_value(obj, field_name):
    """
    Возвращает перевод поля для текущего языка.
    Если перевода нет, возвращает исходное значение.
    """
    language = get_current_language()

    translations = getattr(obj, "translations", None)

    if translations is not None:
        translation = translations.filter(
            language=language
        ).first()

        if translation is not None:
            value = getattr(translation, field_name, None)

            if value:
                return value

    return getattr(obj, field_name, "")
