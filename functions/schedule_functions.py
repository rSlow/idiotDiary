import datetime as dt

import pytz
from aiogram import types
from aiogram.utils.exceptions import BotBlocked

from bot import bot
from functions.main_functions import get_start_week_day
from orm.users import User


async def send_schedule_messages(user_id, dt_obj=None, group=None, limit_changing=None):
    if not dt_obj:
        try:
            date = get_required_date(limit_changing=limit_changing)
            dt_obj = bot.schedule[get_start_week_day(dt.datetime.now())][group][date]
        except KeyError:
            return
    try:
        await bot.send_message(chat_id=user_id,
                               text=dt_obj.message_text,
                               parse_mode=types.ParseMode.HTML)

    except BotBlocked:
        User.deactivate(user_id)
        bot.disable_jobs(user_id)


def get_required_date(limit_changing=None):
    now = dt.datetime.now(tz=pytz.timezone("Asia/Vladivostok"))
    if limit_changing:
        if now.hour >= limit_changing:
            now += dt.timedelta(days=1)
    return now.date()
