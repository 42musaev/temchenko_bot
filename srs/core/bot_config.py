# bot_instance.py

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from core.config import settings


class BotSingleton:
    _instance = None

    @staticmethod
    def get_instance() -> Bot:
        if BotSingleton._instance is None:
            BotSingleton()
        return BotSingleton._instance

    def __init__(self):
        if BotSingleton._instance is not None:
            raise Exception('This class is a singleton!')
        else:
            BotSingleton._instance = Bot(
                token=settings.BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )


# Usage
def get_bot() -> Bot:
    return BotSingleton.get_instance()
