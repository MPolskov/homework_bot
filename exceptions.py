class LostEnvVarError(Exception):
    """Исключение переменной окружения.
    Данное исключение вызывается,
    если какая-либо переменная окружения пустая.
    """

    pass

class UnknownStatusError(Exception):
    """Исключение статуса проверки ДЗ.
    """

    pass

class KeyError(Exception):
    """Исключение статуса проверки ДЗ.
    """

    pass