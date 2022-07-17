import datetime as dt

from aiogram import types
from aiogram.utils.exceptions import BotBlocked

from bot import bot
from functions.main_functions import get_start_week_day, get_required_date
from models.group_schedule_models import ScheduleByGroup
from orm.users import User


async def send_schedule_messages(user_id, dt_obj=None, group=None, limit_changing=None):
    if not dt_obj:
        try:
            date = get_required_date(limit_changing=limit_changing)
            dt_obj = bot.schedule_by_groups[get_start_week_day(dt.datetime.now())][group][date]
        except KeyError:
            return
    try:
        await bot.send_message(chat_id=user_id,
                               text=dt_obj.message_text,
                               parse_mode=types.ParseMode.HTML)
    except BotBlocked:
        await User.deactivate(user_id)
        bot.disable_jobs(user_id)


async def update_bot_schedule():
    schedule_obj = await ScheduleByGroup.from_db()
    bot.schedule_by_groups = schedule_obj
    # bot.schedule_by_days = ScheduleByDays.from_group_schedule(schedule_obj)
