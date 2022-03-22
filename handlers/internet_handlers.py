from bot import dispatcher
from aiogram import types
from functions import n_text
from aiogram.types import ReplyKeyboardMarkup
from FSM import DownloadLibrary
from functions import downloading_book


@dispatcher.message_handler(lambda message: n_text(message.text) == "Скачать с библиотеки")
async def download_library(message: types.Message):
    await DownloadLibrary.library.set()
    await message.answer(text="Для скачивания необходимо вставить ссылку с страницы книги.\n"
                              "Например:\n"
                              "http://elib.igps.ru/?14&type=card&"
                              "cid=ALSFR-cc6b6829-29df-4697-870c-c1520879daf9&remote=false")
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("↪ На главную")
    await message.answer(text="Введите ссылку:",
                         reply_markup=kb)


@dispatcher.message_handler(regexp=r"\bhttp://elib.igps.ru/[\S]+", state=DownloadLibrary.library)
async def await_link_library(message: types.Message):
    await DownloadLibrary.downloading_book.set()
    msg = await message.answer(text="Начинаю загрузку...")
    await downloading_book.download_book(msg=msg, link=message.text)
    await download_library(message)
