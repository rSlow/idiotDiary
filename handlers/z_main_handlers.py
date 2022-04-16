from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bot import dispatcher, bot
from keyboards import get_main_keyboard
from orm.users import User


@dispatcher.message_handler(Text(contains="На главную"), state="*")
async def to_main_menu(message: types.Message, state: FSMContext):
    user_data = message.from_user
    users = bot.users
    if user_data.id not in users:
        User.add_new_user(user_data)
        users.append(user_data.id)
        print(f"[NEW USER] {user_data.username}:{user_data.id}")

    if await state.get_state():
        await state.finish()
    await message.answer("Возвращаем в главное меню...",
                         reply_markup=get_main_keyboard(message.from_user.id))


@dispatcher.message_handler(commands=['cancel'], state="*")
async def cancel(message: types.Message, state: FSMContext):
    if await state.get_state():
        await state.finish()
    await message.answer("Отменено.",
                         reply_markup=get_main_keyboard(message.from_user.id))


@dispatcher.message_handler(state="*")
async def delete(message: types.Message):
    await message.delete()
