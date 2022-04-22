from aiogram import types
from aiogram.dispatcher.filters import Text
from bot import bot
from aiogram.types import ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from FSM import FSMGames

from bot import dispatcher

unique_keys = {
    "12345": 100,
    "23456": 200
}

replace_table = {
    "1": 10,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6
}


@dispatcher.message_handler(Text(contains="Игры"))
async def games(message: types.Message, state: FSMContext):
    await FSMGames.start.set()
    game_names = bot.games.list_games
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(*game_names).add("↪ На главную")
    await message.answer(text="Доступны следующие игры:",
                         reply_markup=kb)


@dispatcher.message_handler(Text(contains=bot.games.list_games), state=FSMGames.start)
async def choose_room(message: types.Message, state: FSMContext):
    async with state.proxy() as proxy:
        proxy["game"] = bot.games.find_by_name(message.text)
    await FSMGames.at_game.set()
    await message.answer(f"Выбрана игра {message.text}.\n"
                         f"Существующие комнаты:")


@dispatcher.message_handler(Text(contains="Создать комнату"), state=FSMGames.at_game)
async def set_room_password(message: types.Message, state: FSMContext):
    pass

# @dispatcher.message_handler(Text(contains="Игры"), state="*")
# async def start(message: types.Message, state: FSMContext):
#     sym = r"""#$%&*+/?@[\]{|}"""
#     # values = [choice(sym) for _ in range(5)]
#     values = [str(randint(1, 6)) for _ in range(5)]
#
#     await message.answer(text=f"{' '.join(values)}")
#
#     values.sort()
#     if unique_keys.get("".join(values)):
#         res = unique_keys.get("".join(values))
#     else:
#         c = Counter(values)
#         res = 0
#         for key, count in c.items():
#             if count == 3:
#                 res += replace_table[key] * 10
#             elif count == 4:
#                 res += replace_table[key] * 20
#             elif count == 5:
#                 res += replace_table[key] * 100
#             elif key in ["1", "5"]:
#                 res += replace_table[key] * count
#     print(res)
