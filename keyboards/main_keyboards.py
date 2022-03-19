from aiogram.types import ReplyKeyboardMarkup
from bot import bot


def get_main_keyboard(user_id):
    main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    main_buttons = ["Учёба 📚", "Интернет 🌍"]
    main_keyboard.add(*main_buttons)
    if user_id in bot.admins:
        main_keyboard.add("Панель администратора")

    return main_keyboard


def get_study_keyboard():
    study_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    study_buttons = ["Расписание 📝", ]
    study_keyboard.add(*study_buttons)
    study_keyboard.add("↪ На главную")
    return study_keyboard


def get_schedule_keyboard():
    schedule_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    schedule_buttons = [
        "Оповещение 🔉",
        "Узнать расписание 📝"]
    schedule_keyboard.add(*schedule_buttons)
    schedule_keyboard.add("Актуальный файл 🧾")
    schedule_keyboard.add("↪ На главную")
    return schedule_keyboard


def get_groups_keyboard(groups):
    groups_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    groups_keyboard.row_width = 4
    groups_keyboard.add(*groups)
    groups_keyboard.add("↪ На главную")
    return groups_keyboard


def get_teachers_keyboard(teachers):
    teachers_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    teachers_keyboard.add(*sorted(teachers))
    teachers_keyboard.add("↪ На главную")
    return teachers_keyboard


def get_teacher_dates_keyboard(teachers):
    teachers_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    teachers_keyboard.add(*teachers)
    teachers_keyboard.add("↪ На главную")
    return teachers_keyboard
