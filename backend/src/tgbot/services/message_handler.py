import traceback

import telegram
from django.conf import settings
from src.utils.re_compile import NUMBER_BYTE_OFFSET
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..loader import bot
from .cleaner import delete_message


async def send_service_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, reply_text: str, parse_mode: str = None, message_thread_id: int = None) -> None:
    """
    Отправляет сообщение в чат и запускает процесс удаления сообщения
    с отсрочкой в 20 секунд.
    - chat_id (:obj:`int` | :obj:`str`) - ID чата.
    - reply_text (:obj:`str`) - текс сообщения
    - parse_mode (:obj:`str`) - Markdown or HTML.
    - message_thread_id (:obj:`str`) - номер темы для супергрупп
    """
    message = await bot.send_message(
        chat_id,
        reply_text,
        parse_mode,
        message_thread_id=message_thread_id
    )
    context.job_queue.run_once(
        delete_message,
        20,
        chat_id=chat_id,
        name=f'send_service_message: {chat_id}',
        data={'chat_id': chat_id, 'message_id': message.message_id}
    )


def find_byte_offset(message):
    """
    Ищет в сообщении числовое значение после 'byte offset'.
    Возвращает найденное значение как целое число или None, если совпадение не найдено.
    """
    match = NUMBER_BYTE_OFFSET.search(message)
    if match:
        return int(match.group(1))
    return None


def delete_at_byte_offset(text, offset):
    """
    Безопасно удаляет символ по указанному смещению байтов из текста в кодировке UTF-8.
    """
    byte_text = text.encode('utf-8')
    if offset < 0 or offset >= len(byte_text):
        return text
    while offset > 0 and (byte_text[offset] & 0xC0) == 0x80:
        offset -= 1
    end_offset = offset + 1
    while end_offset < len(byte_text) and (byte_text[end_offset] & 0xC0) == 0x80:
        end_offset += 1
    modified_byte_text = byte_text[:offset] + byte_text[end_offset:]
    try:
        return modified_byte_text.decode('utf-8')
    except UnicodeDecodeError:
        return text


def split_message(text, max_length=4000):
    """
    Разбивает текст на части, не превышающие max_length символов.
    """
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


async def send_message_to_chat(chat_id: int, message: str, reply_to_message_id: int = None, parse_mode: ParseMode = None, retry_count: int = 3) -> None:
    """
    Отправляет сообщение через Telegram бота с возможностью исправления и повторной отправки при ошибке.

    ### Args:
    - chat_id (`int`): Идентификатор чата в Telegram.
    - message (`str`): Текст сообщения.
    - reply_to_message_id (`int`, optional): Идентификатор сообщения, на которое нужно ответить.
    - parse_mode (`ParseMode`, optional): Режим парсинга сообщения.
    - retry_count (`int`, optional): Количество попыток отправки при ошибке.

    ### Return:
    - send_message (`telegram.Message`): В случае успеха возвращается отправленное сообщение.

    """
    origin_message = message
    for attempt in range(retry_count, -1, -1):
        try:
            send_message = await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode,
                reply_to_message_id=reply_to_message_id,
            )
            return send_message
        except telegram.error.BadRequest as err:
            if "Message is too long" in str(err):
                messages = split_message(message)
                for msg in messages:
                    await bot.send_message(chat_id=chat_id, text=msg, reply_to_message_id=reply_to_message_id)
            if attempt <= 1:
                message = origin_message
                parse_mode = None
                continue
            error_message = str(err)
            offset = find_byte_offset(error_message)
            if offset is not None:
                message = delete_at_byte_offset(message, offset)

        except Exception as err:
            if attempt == 0:
                traceback_str = traceback.format_exc()
                await bot.send_message(
                    chat_id=settings.TELEGRAM_ADMIN_ID,
                    text=f'Необработанная ошибка в `send_message_to_chat`: {str(err)}\n\nТрассировка:\n{traceback_str[-1024:]}'
                )
                return None
