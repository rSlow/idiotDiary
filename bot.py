import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


class CustomBot(Bot):
    def __init__(self, *args, **kwargs):
        super(CustomBot, self).__init__(*args, **kwargs)
        self.admins = [959148697, ]
        self.notification_data = {}
        self.users = []

    async def send_message_to_admins(self, text, parse_mode="MarkdownV2", *args, **kwargs):
        if parse_mode == "MarkdownV2":
            text = "*\[ADMIN\]* " + text
        for admin in self.admins:
            await self.send_message(chat_id=admin,
                                    text=text,
                                    parse_mode=parse_mode,
                                    *args, **kwargs)


logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
scheduler = AsyncIOScheduler(timezone="Asia/Vladivostok")

token = os.getenv("tg_token")

bot = CustomBot(token=token)
dispatcher = Dispatcher(bot=bot,
                        storage=storage)
