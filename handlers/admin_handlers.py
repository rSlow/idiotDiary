from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.exceptions import BotBlocked

from FSM import FSMAdmin
from bot import dispatcher, bot
from orm.users import User


@dispatcher.message_handler(Text(contains="Панель администратора"))
@dispatcher.message_handler(commands=["admin"])
async def main_admin(message: types.Message):
    if message.from_user.id not in bot.admins:
        await message.delete()
    else:
        kb = ReplyKeyboardMarkup(resize_keyboard=True).add("Расписание 📝", "Рассылка 📨").add(
            "Остановить бота ⛔").add("↪ На главную")

        await FSMAdmin.start.set()
        await message.answer(text="Панель ~идиота~ администратора\:",
                             reply_markup=kb,
                             parse_mode="MarkdownV2")


@dispatcher.message_handler(Text(contains="Остановить бота"), state=FSMAdmin.start)
async def stop_bot(message: types.Message):
    await FSMAdmin.stop.set()
    await message.answer("Остановить бота?")


@dispatcher.message_handler(Text(equals="да"), state=FSMAdmin.stop)
async def finally_stop_bot(_):
    dispatcher.stop_polling()


@dispatcher.message_handler(Text(contains="Расписание"), state=FSMAdmin.start)
async def schedule_options(message: types.Message):
    await FSMAdmin.schedule.set()
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add("Обновить с почты 🔁", "↪ На главную")
    await message.answer(text="Опции:", reply_markup=kb)


@dispatcher.message_handler(Text(contains="Рассылка"), state=FSMAdmin.start)
async def mailing_settings(message: types.Message):
    await FSMAdmin.mailing.set()
    await message.answer(f"Предварительно рассылка возможна на {len(bot.users)} пользователей.")
    await message.answer("Введите текст для рассылки:")


@dispatcher.message_handler(state=FSMAdmin.mailing)
async def mailing(message: types.Message):
    users = bot.users.copy()
    users.remove(message.from_user.id)
    count = 0
    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id,
                                   text=message.html_text,
                                   parse_mode="HTML")
            count += 1
        except BotBlocked:
            await User.deactivate(user_id)

    await message.answer(text=f"Рассылка осуществлена на {count} пользователей.")
    if len(users) - count:
        await message.answer(text=f"Бот заблокирован у {len(users) - count} пользователей.")

    await main_admin(message)


@dispatcher.message_handler(Text(contains="Обновить с почты"), state=FSMAdmin.schedule)
async def imap_update(message: types.Message):
    start_message = await message.answer(text="Начинаю обновление...")
    try:
        await bot.update_schedules()
        await message.answer(text="Расписание обновлено.")
    except Exception as ex:
        await message.answer(
            text=f"<b>[ERROR]</b> {ex}",
            parse_mode=types.ParseMode.HTML)
        raise ex
    await start_message.delete()
