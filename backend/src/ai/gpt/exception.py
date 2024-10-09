import traceback


class LogTracebackExceptionError(Exception):
    """Абстракция для логирования traceback."""
    def __init__(self, message, log_traceback=True):
        super().__init__(message)
        self.log_traceback = log_traceback


class InWorkError(LogTracebackExceptionError):
    """Исключение, вызываемое, если запрос находится в работе."""
    pass


class LongQueryError(LogTracebackExceptionError):
    """Исключение для случаев, когда текст запроса слишком большой."""
    def __init__(self, message="Слишком большой текст запроса. Попробуйте сформулировать его короче."):
        self.message = message
        super().__init__(self.message, log_traceback=False)


class LowTokensBalanceError(LogTracebackExceptionError):
    """Недостаточно токенов."""
    def __init__(self, message="Недостаточно средств. Вы исчерпали свой лимит."):
        self.message = message
        super().__init__(self.message, log_traceback=False)


class UnhandledError(LogTracebackExceptionError):
    """Исключение для обработки неожиданных ошибок."""
    pass


class OpenAIRequestError(LogTracebackExceptionError):
    """Ошибки, связанные с запросами к OpenAI."""
    pass


class OpenAIResponseError(OpenAIRequestError):
    """Ошибки, связанные с ответами от OpenAI."""
    pass


class OpenAIConnectionError(OpenAIRequestError):
    """Ошибки соединения при запросах к OpenAI."""
    pass


class OpenAIJSONDecodeError(OpenAIRequestError):
    """Ошибки при десериализации ответов OpenAI."""
    pass


class ValueChoicesError(OpenAIRequestError):
    """Ошибки в содержании ответа."""
    pass


async def handle_exceptions(err: Exception, include_traceback: bool = False) -> tuple[str, type, str]:
    """
    Обработчик исключений для запросов к OpenAI.

    ### Args:
    - err (`Exception`): Объект исключения.
    - include_traceback (`bool`, optional): Флаг для включения трассировки из пространства текущего вызова.

    ### Returns:
    - tuple[`str`, `type`, `str`]: Кортеж с текстом ошибки, типом ошибки и трассировкой.

    """
    user_error_text = 'Что-то пошло не так 🤷🏼\nВозможно большой наплыв запросов, которые я не успеваю обрабатывать 🤯'
    error_messages = {
        InWorkError: 'Я ещё думаю над вашим вопросом.',
        LongQueryError: 'Слишком большой текст запроса. Попробуйте сформулировать его короче.',  # TODO тут что-то не так как ожидается
        LowTokensBalanceError: 'Недостаточно средств. Вы исчерпали свой лимит.',  # TODO тут тоже
        ValueChoicesError: user_error_text,
        OpenAIResponseError: 'Проблема в получении ответа от искусственного интеллекта. Вероятно, он временно недоступен.',
        OpenAIConnectionError: 'Проблема с подключением... Похоже, искусственный интеллект на мгновение отключился.',
        OpenAIJSONDecodeError: user_error_text,
        UnhandledError: user_error_text,
    }

    error_message = error_messages.get(type(err), user_error_text)
    if isinstance(error_message, str):
        formatted_error_message = error_message
    else:
        formatted_error_message = error_message(err)

    include_traceback = include_traceback or (hasattr(err, 'log_traceback') and err.log_traceback)
    traceback_str = ''
    if include_traceback:
        traceback_str = f'\n\nТрассировка:\n{traceback.format_exc()[-2048:]}'

    return formatted_error_message, type(err), traceback_str
