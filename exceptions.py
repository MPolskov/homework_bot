class LostEnvVarError(Exception):
    """Исключение: Отсутствие переменной окружения.
    Исключение вызывается, если какая-либо
    переменная окружения отсутствует.
    """

    pass


class UnknownStatusError(Exception):
    """Исключение: неизвестный статус.
    Исключение вызывается, если получен
    неожидаемый статус проверки работы.
    """

    pass


class MissingKeyError(Exception):
    """Исключение: отсутствует необходимый ключ.
    Исключение вызывается, если в словаре отсутствует
    необходимый для дальнейшей работы ключ.
    """

    pass


class HTTPStatusError(Exception):
    """Исключение: Статус ответа отличается от 200 (ОК)."""

    pass


class ResponseFormatError(TypeError):
    """Исключение: Формат ответа не соответствует ожидаемому."""

    pass
