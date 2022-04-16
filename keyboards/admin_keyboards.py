from aiogram.types import ReplyKeyboardMarkup


def get_main_admin_keyboard():
    main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    main_buttons = ["Расписание 📝", "Рассылка 📨"]
    main_keyboard.add(*main_buttons)
    main_keyboard.add("Остановить бота ⛔")
    main_keyboard.add("↪ На главную")
    return main_keyboard


def get_schedule_admin_keyboard():
    main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    main_keyboard.add("Обновить с почты 🔁")
    main_keyboard.add("↪ На главную")
    return main_keyboard
