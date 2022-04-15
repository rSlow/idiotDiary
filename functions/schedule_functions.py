import aiohttp
from bot import token, bot
import aiogram.utils.markdown as md
from aiogram import types
from aiogram.utils.exceptions import BotBlocked
import datetime as dt
import pytz
import json
from database import User
from functions.db_schedule_functions import disable_jobs

__all__ = (
    "get_file",
    "send_schedule_messages",
    "get_actual_date",
    "get_schedule_data_from_dt",
    "send_schedule_messages_to_teachers",
)


async def get_file(file_path):
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as response:
            data = await response.read()
    return data


async def send_schedule_messages(user_id, dt_obj=None, group=None, limit_changing=None):
    if not dt_obj:
        try:
            date = get_actual_date(limit_changing=limit_changing)
            dt_obj = bot.schedule[group][date]
        except KeyError:
            return
    try:
        await bot.send_message(chat_id=user_id,
                               text=dt_obj.message_text,
                               parse_mode=types.ParseMode.HTML)

    except BotBlocked:  # checking if user blocks bot
        User.deactivate(user_id)
        disable_jobs(user_id)


async def send_schedule_messages_to_teachers(user_id, teacher, dt_obj=None, limit_changing=None):
    if not dt_obj:
        dt_obj = get_actual_date(limit_changing=limit_changing or 14)
    dt_str = dt_obj.strftime('%d/%m/%y')

    data = get_schedule_teacher_data_from_dt(dt_obj=dt_obj, teacher=teacher)

    answers = dict()  # collecting message blocks
    for pair, pair_data in data.items():
        answer = list()

        answer.append(f"<b>Группа {pair_data['group']}: </b>")
        answer.append(f"<b>{pair_data['subject']}</b>\n")
        answer.append(f"тема {pair_data['theme']} ")
        answer.append(f"({pair_data['subject_type']})")

        auditory = pair_data.get("auditory", None)
        if auditory:
            answer.append(f", аудитория {auditory}")

        answers[int(pair)] = answer

    pairs = max(max(answers), 3)
    try:
        if not answers:
            await bot.send_message(chat_id=user_id,
                                   text=f"Пар на {dt_str} нету :)")
        else:
            await bot.send_message(chat_id=user_id,
                                   text=f"Пары на <u>{dt_str}</u>:",
                                   parse_mode=types.ParseMode.HTML)

            for pair in range(1, pairs + 1):
                answer = answers.get(pair, [])
                if not answer:
                    answer.append(f"Отсутствует")
                answer.insert(0, f"<b><u>{int(pair)} пара:</u></b>\n")
                answer_str = "".join(answer)
                await bot.send_message(chat_id=user_id,
                                       text=md.text(answer_str),
                                       parse_mode=types.ParseMode.HTML)

    except BotBlocked:  # checking if user blocks bot
        pass


def get_actual_date(limit_changing=None):
    now = dt.datetime.now(tz=pytz.timezone("Asia/Vladivostok"))
    if limit_changing:
        if now.hour >= limit_changing:
            now += dt.timedelta(days=1)
    return now.date()


def get_schedule_data_from_dt(dt_obj, group):
    with open("data/schedules/schedule_data_group.json", "r", encoding="utf-8-sig") as j_file:
        data = json.load(j_file)[group].get(dt_obj.strftime("%d/%m/%y"), None)
    return data or None


def get_schedule_teacher_data_from_dt(dt_obj, teacher):
    with open("data/schedules/schedule_data_teacher.json", "r", encoding="utf-8-sig") as j_file:
        data = json.load(j_file)[teacher].get(dt_obj.strftime("%d/%m/%y"), None)
    return data or None
