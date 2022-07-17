import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import constants
from models.group_schedule_models import ScheduleByGroup


class CustomBot(Bot):
    def __init__(self, *args, **kwargs):
        super(CustomBot, self).__init__(*args, **kwargs)

        self.schedule_by_groups = None
        self.schedule_by_days = None

        self.admins = [
            959148697,
        ]
        self.notification_data = {}
        self.users = []

    async def get_schedules(self):
        self.schedule_by_groups = await ScheduleByGroup.from_db()
        # self.schedule_by_days = ScheduleByDays.from_group_schedule(self.schedule_by_groups)

    async def send_message_to_admins(self, text, parse_mode="MarkdownV2", *args, **kwargs):
        if parse_mode == "MarkdownV2":
            text = "<b>ADMIN</b> " + text
        for admin in self.admins:
            await self.send_message(chat_id=admin,
                                    text=text,
                                    parse_mode=parse_mode,
                                    *args, **kwargs)

    def disable_jobs(self, user_id):
        if user_id in self.notification_data:
            for time, job in self.notification_data[user_id].items():
                job.remove()
            del self.notification_data[user_id]


logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
scheduler = AsyncIOScheduler(timezone=constants.TIMEZONE)

token = os.getenv("IDIOT_DIARY_BOT_TOKEN")

bot = CustomBot(token=token)
dispatcher = Dispatcher(bot=bot,
                        storage=storage)
