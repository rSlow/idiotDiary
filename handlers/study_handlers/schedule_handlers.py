from bot import dispatcher, bot
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup
from aiogram.dispatcher.filters import Text
import datetime as dt
import pytz

from keyboards import get_schedule_keyboard, get_groups_keyboard, \
    get_teachers_keyboard, get_teacher_dates_keyboard
from FSM import Schedule
from functions import n_text, send_schedule_messages, send_schedule_messages_to_teachers
import json
from functions.parsing_schedule import get_actual_filename


@dispatcher.message_handler(Text(contains="Расписание"))
async def schedule_menu(message: types.Message):
    await Schedule.start.set()
    await message.answer(text="Доступны следующие функции:",
                         reply_markup=get_schedule_keyboard())


@dispatcher.message_handler(commands=["rasp"], state="*")
@dispatcher.message_handler(Text(contains="Узнать расписание"), state=Schedule.start)
async def schedule_menu_check(message: types.Message):
    await Schedule.category.set()

    category_schedule_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    category_schedule_kb.add("Для курсантов 👨‍🎓", "Для преподавателей 👨‍🏫")
    category_schedule_kb.add("↪ На главную")

    await message.answer(text="Выберите катерогию:",
                         reply_markup=category_schedule_kb)


@dispatcher.message_handler(Text(contains="Актуальный файл"), state=Schedule.start)
async def release_schedule_file(message: types.Message):
    actual_filename = get_actual_filename()
    print(f"[FILE SCHEDULE] {message.from_user.username}:"
          f"{message.from_user.id} ")

    doc = types.InputFile(f"data/schedules/{actual_filename}",
                          filename=actual_filename)
    await message.answer_document(doc)


@dispatcher.message_handler(Text(contains="Для курсантов"), state=Schedule.category)
async def schedule_group_menu(message: types.Message):
    await Schedule.group.set()
    groups = bot.schedule.groups

    await message.answer(text="Выберите группу:",
                         reply_markup=get_groups_keyboard(groups))


@dispatcher.message_handler(regexp=r"\w+-\d{2}", state=Schedule.group)
async def schedule_group(message: types.Message, state: FSMContext):
    await Schedule.date_for_group.set()

    async with state.proxy() as proxy_data:
        group = proxy_data['group'] = message.text

    days = bot.schedule[group]

    now = dt.datetime.now(tz=pytz.timezone("Asia/Vladivostok"))
    if now.hour >= 14:
        now += dt.timedelta(days=1)
    now = now.date()

    buttons = [f"{day.strftime('%d/%m/%y')}{' 🕘' * (now == day)}" for day in days]
    dates_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    dates_keyboard.add(*buttons)
    dates_keyboard.add("↪ На главную")

    await message.answer(text="Выберите дату:",
                         reply_markup=dates_keyboard)

    print(f"[SCHEDULE] {message.from_user.username}:"
          f"{message.from_user.id}")


@dispatcher.message_handler(regexp=r"\d{2}/\d{2}/\d{2}", state=Schedule.date_for_group)
async def schedule_date(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy_data:
        group = proxy_data['group']
        date = dt.datetime.strptime(n_text(message.text), "%d/%m/%y").date()
        dt_obj = bot.schedule[group][date]

    await send_schedule_messages(user_id=message.from_user.id,
                                 dt_obj=dt_obj)


@dispatcher.message_handler(Text(contains="Для преподавателей"), state=Schedule.category)
async def schedule_teacher_menu(message: types.Message):
    await Schedule.teacher.set()

    with open("data/schedules/schedule_data_teacher.json", "r", encoding="utf-8-sig") as j_file:
        teachers = json.load(j_file).keys()

    await message.answer(text="Выберите преподавателя:",
                         reply_markup=get_teachers_keyboard(teachers))


@dispatcher.message_handler(regexp=r"(\w&\D)+\s+(\w&\D)[.](\w&\D)[.]", state=Schedule.teacher)
async def schedule_teacher_menu(message: types.Message, state: FSMContext):
    with open("data/schedules/schedule_data_teacher.json", "r", encoding="utf-8-sig") as j_file:
        teachers_data = json.load(j_file)
        if message.text in teachers_data:
            await Schedule.date_for_teacher.set()
            async with state.proxy() as proxy_data:
                teacher = proxy_data["teacher"] = message.text

            teacher_data = teachers_data[teacher]
            dates = sorted(teacher_data.keys(), key=lambda x: dt.datetime.strptime(x, "%d/%m/%y"))

            now = dt.datetime.now(tz=pytz.timezone("Asia/Vladivostok"))
            if now.hour >= 14:
                now += dt.timedelta(days=1)

            buttons = []
            for date in dates:
                if now.strftime("%d/%m/%y") == date:
                    buttons.append(f"{date} 🕘")
                else:
                    buttons.append(date)

            await message.answer(text="Выберите дату:",
                                 reply_markup=get_teacher_dates_keyboard(buttons))


@dispatcher.message_handler(regexp=r"\d{2}/\d{2}/\d{2}", state=Schedule.date_for_teacher)
async def schedule_teacher_menu(message: types.Message, state: FSMContext):
    with open("data/schedules/schedule_data_teacher.json", "r", encoding="utf-8-sig") as j_file:
        teachers_data = json.load(j_file)
        date = n_text(message.text)
        async with state.proxy() as proxy_data:
            teacher = proxy_data["teacher"]
        if date in teachers_data[teacher]:
            dt_obj = dt.datetime.strptime(date, "%d/%m/%y")

            await send_schedule_messages_to_teachers(user_id=message.from_user.id,
                                                     teacher=teacher,
                                                     dt_obj=dt_obj)
