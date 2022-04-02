from bot import dispatcher, bot
from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from keyboards import get_main_keyboard, get_internet_keyboard, get_study_keyboard
from database import Session, User


@dispatcher.message_handler(commands=["start", "help"], state="*")
async def start(message: types.Message, state: FSMContext):
    user_data = message.from_user
    users = bot.users
    if user_data.id not in users:
        with Session() as session:
            session.add(
                User(user_id=user_data.id,
                     fullname=user_data.full_name,
                     username_mention=user_data.mention)
            )
            session.commit()
        users.append(user_data.id)
        print(f"[NEW USER] {user_data.username}:{user_data.id}")

    if await state.get_state():
        await state.finish()

    await message.bot.send_message(chat_id=user_data.id,
                                   text="Добро пожаловать. Выберите действие:",
                                   reply_markup=get_main_keyboard(message.from_user.id)
                                   )


@dispatcher.message_handler(Text(equals="Учёба 📚"))
async def study_menu(message: types.Message):
    await message.answer(text="Доступны следующие функции:",
                         reply_markup=get_study_keyboard())


@dispatcher.message_handler(Text(equals="Интернет 🌍"))
async def internet_menu(message: types.Message):
    await message.answer(text="Доступны следующие функции:",
                         reply_markup=get_internet_keyboard())
