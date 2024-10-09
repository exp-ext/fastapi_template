import asyncio

from src.utils.re_compile import COMMAND_PATTERN
from telegram import Update
from telegram.ext import ContextTypes

from ..loader import bot, logger
from .patterns import COMMANDS, KEYBOARD
from .redis_crud import RedisCRUDManager


async def clear_commands(update: Update) -> None:
    """Удаление команд бота из чата."""
    try:
        chat_id = update.message.chat.id
        message_id = update.message.message_id
        text = ''
        message_command = update.message.text

        if update.message.location or update.message.contact:
            text = 'delete'
        else:
            if message_command:
                command = COMMAND_PATTERN.findall(message_command)
                if command:
                    text = command[0]

        if text or message_command in COMMANDS:
            await bot.delete_message(chat_id, message_id)

    except Exception:
        text = (
            'Для корректной работы, я должен быть администратором группы! '
            'Иначе я не смогу удалять технические сообщения.'
        )
        await bot.send_message(chat_id, text)


async def delete_scheduled_job(context, job_name):
    if job_name:
        job = context.job_queue.get_jobs_by_name(job_name)
        if job:
            job[0].schedule_removal()


async def remove_incoming_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: str = None) -> None:
    """
    Удаление клавиатуры после нажатия.
    ### Args:
    - update (:obj:`Update`)
    - context (:obj:`ContextTypes.DEFAULT_TYPE`)
    - message_id (:obj:`str`): optionals
    """
    chat_id = update.effective_chat.id
    del_menu_id = message_id if message_id else update.effective_message.message_id
    try:
        await context.bot.delete_message(chat_id, del_menu_id)
        keyboard_manager = RedisCRUDManager(pattern=KEYBOARD)
        asyncio.gather(
            keyboard_manager.delete_messages_for_chat_id(chat_id),
            delete_scheduled_job(context, f'{KEYBOARD}:{chat_id}:{del_menu_id}')
        )
    except Exception as error:
        logger.error(error)


async def delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        job = context.job
        await context.bot.delete_message(chat_id=job.data['chat_id'], message_id=job.data['message_id'])
    except Exception as error:
        logger.error(error)


async def delete_inline_keyboards_or_messages_by_ids(chat_id, message_ids, context):
    for message_id in message_ids:
        try:
            asyncio.gather(
                context.bot.delete_message(chat_id=chat_id, message_id=message_id),
                delete_scheduled_job(context, f'{KEYBOARD}:{message_id}')
            )
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение: {e}")
