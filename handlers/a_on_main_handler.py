from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from bot import dispatcher
from keyboards import get_main_keyboard


@dispatcher.message_handler(commands=['cancel'], state="*")
@dispatcher.message_handler(Text(contains="На главную"), state="*")
async def to_main_menu(message: types.Message, state: FSMContext):
    if await state.get_state():
        await state.finish()
    await message.answer("Возвращаем в главное меню...",
                         reply_markup=get_main_keyboard(message.from_user.id))
