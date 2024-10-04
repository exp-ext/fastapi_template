from telegram.ext import MessageHandler, filters

from src.tgbot.handlers.chat_distributor import check_request


async def setup_handlers(dp):
    # GPT assist
    dp.add_handler(MessageHandler(filters.TEXT, check_request))
    return dp
