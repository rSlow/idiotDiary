import datetime as dt

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup
from asyncio import sleep

from FSM import Schedule
from bot import dispatcher, bot
from functions.main_functions import get_start_week_day
from functions.main_functions import n_text
from functions.schedule_functions import send_schedule_messages, get_required_date
from keyboards import get_schedule_keyboard, get_groups_keyboard


@dispatcher.message_handler(Text(contains="Расписание"))
async def schedule_menu(message: types.Message):
    await Schedule.start.set()
    await message.answer(text="Доступны следующие функции:",
                         reply_markup=get_schedule_keyboard())


@dispatcher.message_handler(Text(contains="Файлы расписания"), state=Schedule.start)
async def schedule_files(message: types.Message):
    await Schedule.files.set()
    dates = bot.schedule.filenames.keys()
    kb = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True).add(*dates)
    kb.add("↪ На главную")
    await message.answer(text="Выберите дату", reply_markup=kb)


@dispatcher.message_handler(regexp=r"\d{2}/\d{2}/\d{2}", state=Schedule.files)
async def release_schedule_file(message: types.Message):
    print(f"[FILE SCHEDULE] {message.from_user.username}:"
          f"{message.from_user.id} ")
    try:
        filename = f"{bot.schedule.filenames[message.text]}.xlsx"
        doc = types.InputFile(f"data/schedules/{filename}",
                              filename=f"{message.text}.xlsx".replace("/", "-"))
        await message.answer_document(doc)
    except KeyError:
        msg = await message.answer(text="Не лезь!")
        await message.delete()
        await sleep(5)
        await msg.delete()


@dispatcher.message_handler(commands=["rasp"], state="*")
@dispatcher.message_handler(Text(contains="Узнать расписание"), state=Schedule.start)
async def schedule_group_menu(message: types.Message, state: FSMContext):
    await Schedule.group.set()
    async with state.proxy() as proxy_data:
        start_week_day = proxy_data["current_start_week_date"] = get_start_week_day(dt.datetime.now())
        try:
            groups = bot.schedule[start_week_day].groups
        except KeyError:
            start_week_day = proxy_data["current_start_week_date"] = next(iter(bot.schedule))
            groups = bot.schedule[start_week_day].groups

    await message.answer(text="Выберите группу:", reply_markup=get_groups_keyboard(groups))


@dispatcher.message_handler(regexp=r"\w+-\d{2}", state=Schedule.group)
async def schedule_group(message: types.Message, state: FSMContext, group=None):
    await Schedule.date_for_group.set()

    async with state.proxy() as proxy_data:
        if not group:
            proxy_data['group'] = message.text
        group = proxy_data['group']
        start_week_day = proxy_data["current_start_week_date"]

    days = bot.schedule[start_week_day][group]

    now = get_required_date(limit_changing=14)

    buttons = [f"{day.strftime(bot.DATE_FORMAT)}{' 🕘' * (now == day)}" for day in days]
    dates_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    dates_keyboard.add(*buttons)
    dates_keyboard.row("На неделю 🗓")
    if not bot.schedule.is_last(start_week_day):
        dates_keyboard.insert("Следующая неделя")
    dates_keyboard.add("↪ На главную")

    await message.answer(text="Выберите дату:", reply_markup=dates_keyboard)

    print(f"[SCHEDULE] {message.from_user.username}:"
          f"{message.from_user.id}")


@dispatcher.message_handler(Text(contains="На неделю"), state=Schedule.date_for_group)
async def send_schedule_week(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy_data:
        group = proxy_data['group']
        start_week_day = proxy_data["current_start_week_date"]

    week_obj = bot.schedule[start_week_day][group]
    await message.answer(text=week_obj.message_text, parse_mode=types.ParseMode.HTML)


@dispatcher.message_handler(Text(contains="Следующая неделя"), state=Schedule.date_for_group)
async def send_schedule_next_week(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy_data:
        proxy_data["current_start_week_date"] += dt.timedelta(weeks=1)
        group = proxy_data["group"]
    await schedule_group(message=message, state=state, group=group)


@dispatcher.message_handler(regexp=r"\d{2}/\d{2}/\d{2}", state=Schedule.date_for_group)
async def schedule_date(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy_data:
        group = proxy_data['group']
        start_week_day = proxy_data["current_start_week_date"]
        date = dt.datetime.strptime(n_text(message.text), bot.DATE_FORMAT).date()
        dt_obj = bot.schedule[start_week_day][group][date]

    await send_schedule_messages(user_id=message.from_user.id,
                                 dt_obj=dt_obj)
