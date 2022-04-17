from aiogram import types

from bot import dispatcher


@dispatcher.message_handler(state="*")
async def delete(message: types.Message):
    await message.delete()
