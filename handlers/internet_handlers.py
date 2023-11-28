import logging

from aiogram import types
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.exceptions import NetworkError

from FSM import DownloadLibrary
from bot import dispatcher
from functions import igps_downloading


@dispatcher.message_handler(Text(contains="Скачать с библиотеки"))
async def download_library(message: types.Message):
    await DownloadLibrary.library.set()
    await message.answer(text="Для скачивания необходимо вставить ссылку с страницы книги.\n"
                              "Например:\n"
                              "http://elib.igps.ru/?type=card&cid=ALSFR-e0e02395-1133-4e4e-b383-bf9999f9cf5d")
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Ссылка:")
    kb.add("↪ На главную")
    await message.answer(text="Введите ссылку:",
                         reply_markup=kb)


@dispatcher.message_handler(regexp=r"\bhttp[s]*://elib.igps.ru/[\S]+", state=DownloadLibrary.library)
async def await_link_library(message: types.Message):
    await DownloadLibrary.downloading_book.set()
    msg = await message.answer(text="Начинаю загрузку...")
    try:
        await igps_downloading.download_book(msg=msg, link=message.text)
        await message.answer(text="Загрузка завершена.")
    except NetworkError:
        await msg.answer(text="Размер файла превышает 50 МБ - ограничение Telegram. "
                              "Способы загрузки пока в разработке.")
    except Exception as ex:
        logging.info(ex)
