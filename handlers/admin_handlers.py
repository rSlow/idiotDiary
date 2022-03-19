from bot import dispatcher, bot
from aiogram import types
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.exceptions import BotBlocked

import os
import json

from functions import parsing_schedule, aioimap, n_text, get_file
from FSM import FSMAdmin
from keyboards import get_main_admin_keyboard, get_schedule_admin_keyboard
from database import deactivate_user, db


@dispatcher.message_handler(lambda message: message.text == "Панель администратора")
@dispatcher.message_handler(commands=["admin"])
async def main_admin(message: types.Message):
    if message.from_user.id not in bot.admins:
        await message.delete()
    else:
        await FSMAdmin.start.set()
        await message.answer(text="Панель ~идиота~ администратора\:",
                             reply_markup=get_main_admin_keyboard(),
                             parse_mode="MarkdownV2")


@dispatcher.message_handler(lambda message: n_text(message.text) == "Остановить бота",
                            state=FSMAdmin.start)
async def stop_bot(message: types.Message):
    await FSMAdmin.stop.set()
    await message.answer("Остановить бота?")


@dispatcher.message_handler(lambda message: message.text == "да",
                            state=FSMAdmin.stop)
async def stop_bot(_):
    db.commit()
    db.close()
    dispatcher.stop_polling()


@dispatcher.message_handler(lambda message: n_text(message.text) == "Расписание",
                            state=FSMAdmin.start)
async def schedule_options(message: types.Message):
    await FSMAdmin.schedule.set()
    await message.answer(text="Опции:",
                         reply_markup=get_schedule_admin_keyboard())


@dispatcher.message_handler(lambda message: n_text(message.text) == "Рассылка",
                            state=FSMAdmin.start)
async def mailing(message: types.Message):
    await FSMAdmin.mailing.set()
    await message.answer(f"Предварительно рассылка возможна на {len(bot.users)} пользователей.")
    await message.answer("Введите текст для рассылки:")


@dispatcher.message_handler(state=FSMAdmin.mailing)
async def schedule_options(message: types.Message):
    users = bot.users
    users.remove(message.from_user.id)
    count = 0
    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id,
                                   text=message.html_text,
                                   parse_mode="HTML")
            count += 1
        except BotBlocked:
            deactivate_user(user_id)

    await message.answer(text=f"Рассылка осуществлена на {count} пользователей.")
    if len(users) - count:
        await message.answer(text=f"Бот заблокирован у {len(users) - count} пользователей.")

    await main_admin(message)


@dispatcher.message_handler(lambda message: n_text(message.text) == "Обновить с почты",
                            state=FSMAdmin.schedule)
async def imap_update(message: types.Message):
    start_message = await message.answer(text="Начинаю обновление...")
    try:
        await aioimap.checking_schedule()
        await message.answer(text="Расписание обновлено.")
    except Exception as ex:
        await message.answer(
            text=f"*[ERROR]* {ex}",
            parse_mode="MarkdownV2")
    await start_message.delete()


@dispatcher.message_handler(lambda message: n_text(message.text) == "Загрузить",
                            state=FSMAdmin.schedule)
async def download_schedule_file(message: types.Message):
    await FSMAdmin.download_schedule.set()
    await message.answer(text="Выбери файл для загрузки:",
                         reply_markup=ReplyKeyboardRemove())


@dispatcher.message_handler(content_types=['document'],
                            state=FSMAdmin.download_schedule)
async def wait_document(message: types.Message):
    await FSMAdmin.start.set()
    if os.path.splitext(message.document.file_name)[1] != ".xlsx":
        await message.answer('Загружен не тот файл. Необходимо выбрать excel-файл')
    else:
        try:
            xl_file = await message.bot.get_file(file_id=message.document.file_id)
            xl_data = await get_file(file_path=xl_file.file_path)
            filename = "schedule.xlsx"

            with open(f"data/schedules/{filename}", "wb") as file:
                file.write(xl_data)

            data = parsing_schedule.parser_by_group(filename)

            with open("data/schedules/schedule_data_group.json", "w", encoding='utf-8-sig') as j_file:
                json.dump(data, j_file, indent=4, ensure_ascii=False)

            await message.answer('Расписание загружено и обновлено.',
                                 reply_markup=get_main_admin_keyboard())

            os.remove("data/schedules/schedule.xlsx")

        except Exception as ex:
            await message.answer(f"Произошла ошибка:\n{ex}",
                                 reply_markup=get_main_admin_keyboard())

        await FSMAdmin.start.set()
