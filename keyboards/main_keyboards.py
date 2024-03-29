from aiogram.types import ReplyKeyboardMarkup

from bot import bot


def get_main_keyboard(user_id):
    main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    main_buttons = ["Расписание 📚", "Скачать с библиотеки 🌎"]
    main_keyboard.add(*main_buttons)
    if user_id in bot.admins:
        main_keyboard.insert("Панель администратора")

    return main_keyboard


def get_schedule_keyboard():
    schedule_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    schedule_keyboard.add("По группам 👨‍👧‍👦", "По дням 📆")
    # schedule_keyboard.add("По преподавателям 🧑‍🏫")
    schedule_keyboard.add("Оповещение 🔉", "↪ На главную")
    return schedule_keyboard


def get_groups_keyboard(groups):
    groups_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    groups_keyboard.row_width = 4
    groups_keyboard.add(*groups)
    groups_keyboard.add("↪ На главную")
    return groups_keyboard
