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
    "get_actual_dt",
    "get_schedule_data_from_dt",
    "send_schedule_messages_to_teachers",
)


async def get_file(file_path):
    url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as response:
            data = await response.read()
    return data


async def send_schedule_messages(user_id, group, dt_obj=None, limit_changing=None):
    if not dt_obj:
        dt_obj = get_actual_dt(limit_changing=limit_changing or 14)

    try:  # for dates which don't have data (sunday) - for notifications
        data = get_schedule_data_from_dt(dt_obj=dt_obj, group=group)
        if not data:
            return

    except (KeyError, ValueError, IndexError):
        return

    answers = []  # collecting message blocks
    for pair, pair_data in data.items():

        if not any(pair_data.values()):
            continue

        answers.append(f"\n<b><u>{int(pair)} пара:</u></b>")

        f_subject = pair_data.get("f_subject", None)
        if f_subject:
            answers.append(f"<b>{f_subject}</b>")

        f_auditory = pair_data.get("f_auditory", None)
        if f_auditory:
            answers.append(f"- аудитория {f_auditory}")

        f_theme = pair_data.get("f_theme", None)
        if f_theme:
            answers.append(md.text(f"\nтема № {f_theme}"))

        f_type = pair_data.get("f_type", None)
        if f_type:
            answers.append(f"({f_type})")

        f_teacher = pair_data.get("f_teacher", None)
        if f_teacher:
            answers.append(f"\nпреподаватель: {f_teacher}")

        s_subject = pair_data.get("s_subject", None)
        if s_subject:
            answers.append(f"\n<b>{s_subject}</b>")

        s_auditory = pair_data.get("s_auditory", None)
        if s_auditory:
            answers.append(f"- аудитория {s_auditory}")

        s_theme = pair_data.get("s_theme", None)
        if s_theme:
            answers.append(md.text(f"\nтема № {s_theme}"))

        s_type = pair_data.get("s_type", None)
        if s_type:
            answers.append(f"({s_type})")

        s_teacher = pair_data.get("s_teacher", None)
        if s_teacher:
            answers.append(f"\nпреподаватель: {s_teacher}")

    try:
        if not answers:
            await bot.send_message(chat_id=user_id,
                                   text='Открывай бутылочку пивка, пар нет 🍺')
        else:
            answers.insert(0, f"Пары на <u>{dt_obj.strftime('%d/%m/%y')}</u>:")
            await bot.send_message(chat_id=user_id,
                                   text=md.text(*answers),
                                   parse_mode=types.ParseMode.HTML)

    except BotBlocked:  # checking if user blocks bot
        User.deactivate(user_id)
        disable_jobs(user_id)


async def send_schedule_messages_to_teachers(user_id, teacher, dt_obj=None, limit_changing=None):
    if not dt_obj:
        dt_obj = get_actual_dt(limit_changing=limit_changing or 14)
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


def get_actual_dt(limit_changing=None):
    now = dt.datetime.now(tz=pytz.timezone("Asia/Vladivostok"))
    if limit_changing:
        if now.hour >= limit_changing:
            now = now + dt.timedelta(days=1)
    return now


def get_schedule_data_from_dt(dt_obj, group):
    with open("data/schedules/schedule_data_group.json", "r", encoding="utf-8-sig") as j_file:
        data = json.load(j_file)[group].get(dt_obj.strftime("%d/%m/%y"), None)
    return data or None


def get_schedule_teacher_data_from_dt(dt_obj, teacher):
    with open("data/schedules/schedule_data_teacher.json", "r", encoding="utf-8-sig") as j_file:
        data = json.load(j_file)[teacher].get(dt_obj.strftime("%d/%m/%y"), None)
    return data or None
