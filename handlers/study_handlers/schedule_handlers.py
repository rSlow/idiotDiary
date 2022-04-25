import datetime as dt
from asyncio import sleep
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup

import constants
from FSM import Schedule, ScheduleByGroup, ScheduleByDay, ScheduleByTeacher
from bot import dispatcher, bot
from functions.main_functions import get_start_week_day
from functions.main_functions import n_text
from functions.schedule_functions import send_schedule_messages, get_required_date
from keyboards import get_schedule_keyboard, get_groups_keyboard
from models.days_schedule_models import GroupDayByDays


@dispatcher.message_handler(Text(contains="Расписание"))
async def schedule_menu(message: types.Message):
    await Schedule.start.set()
    await message.answer(text="Доступны следующие функции:",
                         reply_markup=get_schedule_keyboard())


@dispatcher.message_handler(Text(contains="Файлы расписания"), state=Schedule.start)
async def schedule_files(message: types.Message):
    await Schedule.files.set()
    dates = bot.schedule_by_groups.filenames.keys()
    kb = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True).add(*dates)
    kb.add("↪ На главную")
    await message.answer(text="Выберите дату", reply_markup=kb)


@dispatcher.message_handler(regexp=r"\d{2}/\d{2}/\d{2}", state=Schedule.files)
async def release_schedule_file(message: types.Message):
    logging.info(f"[FILE SCHEDULE] {message.from_user.username}:"
                 f"{message.from_user.id} ")
    try:
        filename = f"{bot.schedule_by_groups.filenames[message.text]}.xlsx"
        doc = types.InputFile(f"data/schedules/{filename}",
                              filename=f"{message.text}.xlsx".replace("/", "-"))
        await message.answer_document(doc)
    except KeyError:
        msg = await message.answer(text="Не лезь!")
        await message.delete()
        await sleep(5)
        await msg.delete()


@dispatcher.message_handler(commands=["rasp"], state="*")
@dispatcher.message_handler(Text(contains="По группам"), state=Schedule.start)
async def schedule_by_groups(message: types.Message, state: FSMContext):
    await ScheduleByGroup.group.set()
    async with state.proxy() as proxy_data:
        start_week_day = proxy_data["current_start_week_date"] = get_start_week_day(dt.datetime.now())
        try:
            groups = bot.schedule_by_groups[start_week_day].groups
        except KeyError:
            start_week_day = proxy_data["current_start_week_date"] = bot.schedule_by_groups.first
            groups = bot.schedule_by_groups[start_week_day].groups

    await message.answer(text="Выберите группу:", reply_markup=get_groups_keyboard(groups))


@dispatcher.message_handler(regexp=r"\w+-\d{2}", state=ScheduleByGroup.group)
async def schedule_group_by_group(message: types.Message, state: FSMContext, group=None):
    await ScheduleByGroup.date_for_group.set()

    async with state.proxy() as proxy_data:
        if not group:
            proxy_data['group'] = message.text
        group = proxy_data['group']
        start_week_day = proxy_data["current_start_week_date"]

    days = bot.schedule_by_groups[start_week_day][group]

    now = get_required_date(limit_changing=14)
    buttons = [f"{day.strftime(constants.DATE_FORMAT)}{' 🕘' * (now == day)}" for day in days]
    dates_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons).row("На неделю 🗓")

    if not bot.schedule_by_groups.is_last_week(start_week_day):
        dates_keyboard.insert("Следующая неделя")
    dates_keyboard.add("↪ На главную")

    await message.answer(text="Выберите дату:", reply_markup=dates_keyboard)


@dispatcher.message_handler(Text(contains="На неделю"), state=ScheduleByGroup.date_for_group)
async def send_schedule_week(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy_data:
        group = proxy_data['group']
        start_week_day = proxy_data["current_start_week_date"]

    week_obj = bot.schedule_by_groups[start_week_day][group]
    await message.answer(text=week_obj.message_text, parse_mode=types.ParseMode.HTML)


@dispatcher.message_handler(Text(contains="Следующая неделя"), state=ScheduleByGroup.date_for_group)
async def send_schedule_by_groups_next_week(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy_data:
        proxy_data["current_start_week_date"] += dt.timedelta(weeks=1)
        group = proxy_data["group"]
    await schedule_group_by_group(message=message, state=state, group=group)


@dispatcher.message_handler(regexp=r"\d{2}/\d{2}/\d{2}", state=ScheduleByGroup.date_for_group)
async def schedule_by_groups_date(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy_data:
        group = proxy_data['group']
        start_week_day = proxy_data["current_start_week_date"]
    date = dt.datetime.strptime(n_text(message.text), constants.DATE_FORMAT).date()
    dt_obj = bot.schedule_by_groups[start_week_day][group][date]

    await send_schedule_messages(user_id=message.from_user.id,
                                 dt_obj=dt_obj)


@dispatcher.message_handler(Text(contains="По дням"), state=Schedule.start)
async def schedule_by_days_menu(message: types.Message, state: FSMContext):
    await ScheduleByDay.day.set()

    async with state.proxy() as proxy_data:
        try:
            start_week_day = proxy_data["current_start_week_date"]
            if not start_week_day:
                start_week_day = proxy_data["current_start_week_date"] = get_start_week_day(dt.datetime.now())
                days = bot.schedule_by_days[start_week_day].days
        except KeyError:
            start_week_day = proxy_data["current_start_week_date"] = bot.schedule_by_groups.first
            days = bot.schedule_by_days[start_week_day].days

    now = get_required_date(limit_changing=14)
    buttons = [f"{day.strftime(constants.DATE_FORMAT)}{' 🕘' * (now == day)}" for day in days]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3).add(*buttons)

    if not bot.schedule_by_days.is_last_week(start_week_day):
        kb.insert("Следующая неделя")
    kb.add("↪ На главную")

    await message.answer(text="Выберите день:", reply_markup=kb)


@dispatcher.message_handler(Text(contains="Следующая неделя"), state=ScheduleByDay.day)
async def send_schedule_by_days_next_week(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy_data:
        proxy_data["current_start_week_date"] += dt.timedelta(weeks=1)
    await schedule_by_days_menu(message=message, state=state)


@dispatcher.message_handler(regexp=r"\d{2}/\d{2}/\d{2}", state=ScheduleByDay.day)
async def schedule_by_days_date(message: types.Message, state: FSMContext):
    await ScheduleByDay.group_for_day.set()
    day_str = n_text(message.text)

    async with state.proxy() as proxy_data:
        start_week_day = proxy_data["current_start_week_date"]
        date = proxy_data["day"] = dt.datetime.strptime(day_str, constants.DATE_FORMAT).date()
    groups = bot.schedule_by_days[start_week_day][date]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4).add(*groups).add("↪ На главную")
    await message.answer(text="Выберите группу:", reply_markup=kb)


@dispatcher.message_handler(regexp=r"\w+-\d{2}", state=ScheduleByDay.group_for_day)
async def schedule_group_by_day(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy_data:
        start_week_day = proxy_data["current_start_week_date"]
        day = proxy_data["day"]

    group_day_obj: GroupDayByDays = bot.schedule_by_days[start_week_day][day][message.text]
    await message.answer(text=group_day_obj.message_text, parse_mode=types.ParseMode.HTML)
