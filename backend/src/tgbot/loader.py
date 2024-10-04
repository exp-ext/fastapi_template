from warnings import filterwarnings

from src.conf import settings
from src.conf import logger
from telegram import Bot
from telegram.ext import Application
from telegram.warnings import PTBUserWarning

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

bot = Bot(token=settings.TELEGRAM_TOKEN)

application = (
    Application.builder()
    .updater(None)
    .token(settings.TELEGRAM_TOKEN)
    .read_timeout(7)
    .get_updates_read_timeout(42)
    .build()
)


async def set_webhook():
    url = f"https://{settings.DOMAIN}/bot/{settings.SECRET_BOT_URL}/webhooks/"
    try:
        response = await bot.set_webhook(url=url)
        logger.info(f"Webhook set to {url} with response: {response}")
        return True
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return False


async def remove_commands():
    await bot.delete_my_commands()
