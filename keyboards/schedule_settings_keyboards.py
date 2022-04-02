from aiogram.types import ReplyKeyboardMarkup


def get_notifications_settings_keyboard(user):
    notifications_settings_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    notifications_settings_keyboard.add("Группа 👨‍👧‍👧")
    notifications_settings_keyboard.insert("Время ⏳")
    if user.notify_group and user.notify_times:
        if not user.notify_status:
            notifications_settings_keyboard.add("Включить ☑")
        else:
            notifications_settings_keyboard.add("Выключить 🚫")
        notifications_settings_keyboard.insert("↪ На главную")
    else:
        notifications_settings_keyboard.add("↪ На главную")
    return notifications_settings_keyboard


def get_notifications_group_keyboard(group):
    notifications_group_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    if group:
        notifications_group_keyboard.add("Изменить группу 🔄")
        notifications_group_keyboard.insert("Удалить группу 🗑")
    else:
        notifications_group_keyboard.add("Установить группу 📲")
    notifications_group_keyboard.add("↪ На главную")

    return notifications_group_keyboard


def get_main_time_keyboard(times_map_obj):
    main_time_keyboard = ReplyKeyboardMarkup(resize_keyboard=True,
                                             one_time_keyboard=True)
    main_time_keyboard.row_width = 4
    times = list(map(lambda x: x + " ❌", times_map_obj))
    main_time_keyboard.add(*times)
    main_time_keyboard.add("Добавить время оповещения 🕞")
    if times:
        main_time_keyboard.add("Удалить все метки ❌❌❌")
    main_time_keyboard.add("↪ На главную")
    return main_time_keyboard
