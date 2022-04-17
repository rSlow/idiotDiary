from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from asyncio import sleep
from random import randint, shuffle
import time

from bot import dispatcher


@dispatcher.message_handler(Text(contains="Игры"), state="*")
async def start(message: types.Message, state: FSMContext):
    values = [randint(1, 6) for _ in range(5)]
    user_id = message.from_user.id
    msg = await message.answer(text=f"{[values]}")
    start_time = time.time()
    while time.time() - start_time < 5:
        values = [randint(1, 6) for _ in range(5)]
        await sleep(0.1)
        await msg.edit_text(text=f"{[values]}")
    print("end")