import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup

from FSM import DownloadLibrary
from bot import dispatcher, bot
from keyboards import get_main_keyboard
from orm.users import User


@dispatcher.message_handler(commands=["start", "help"], state="*")
async def start(message: types.Message, state: FSMContext):
    user_data = message.from_user
    users = bot.users
    if user_data.id not in users:
        await User.add_user(user_data)
        users.append(user_data.id)
        logging.info(f"[NEW USER] {user_data.username}:{user_data.id}")

    if await state.get_state():
        await state.finish()

    await message.bot.send_message(chat_id=user_data.id,
                                   text="Добро пожаловать. Выберите действие:",
                                   reply_markup=get_main_keyboard(message.from_user.id))
