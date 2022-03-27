import json

from bot import dispatcher, scheduler, bot
from aiogram import types
from aiogram.dispatcher.filters import Text
import datetime as dt
from functions import n_text, send_schedule_messages, disable_jobs, append_job_in_scheduler, delete_job_from_scheduler
from FSM import Schedule, ScheduleSettings
from database import enable_notifications, disable_notifications, add_user, \
    set_group_to_user, set_time_to_user, get_user_data
from keyboards import get_notifications_settings_keyboard, \
    get_notifications_group_keyboard, get_groups_keyboard, \
    get_main_time_keyboard
from random import randrange
from asyncio import sleep


@dispatcher.message_handler(Text(contains="Оповещение"), state=Schedule.start)
async def schedule_menu(message: types.Message):
    user_id = message.from_user.id

    user_notify_data = get_user_data(user_id)
    if not user_notify_data:
        user_notify_data = (user_id, False, "", "[]")
        add_user(user_id)

    await Schedule.notifications.set()
    time_settings = json.loads(user_notify_data[3])
    if not user_notify_data[2] or not time_settings:
        await message.answer(
            text=f"Оповещения не настроены. Кнопка для включения появится после настройки.",
            reply_markup=get_notifications_settings_keyboard(status=False, ready=False))
    else:
        await Schedule.notifications_ready.set()
        if not user_notify_data[1]:
            await message.answer(
                text="Оповещения выключены.",
                reply_markup=get_notifications_settings_keyboard(status=False, ready=True))
        else:
            await message.answer(
                text="Оповещения включены:",
                reply_markup=get_notifications_settings_keyboard(status=True, ready=True))
        await message.answer(f"<b>Группа</b>: {user_notify_data[2]}",
                             parse_mode="HTML")
        times_block_msg = '\n'.join(json.loads(user_notify_data[3]))
        await message.answer(f"<b>Временные метки</b>:\n{times_block_msg}",
                             parse_mode="HTML")


@dispatcher.message_handler(Text(contains="Включить"), state=Schedule.notifications_ready)
async def schedule_notifications_enable(message: types.Message):
    user_id = message.from_user.id

    enable_notifications(user_id)

    group, times = get_user_data(user_id)[2], json.loads(get_user_data(user_id)[3])
    for time in times:
        user_time = dt.datetime.strptime(time, "%H:%M")
        job = scheduler.add_job(func=send_schedule_messages,
                                trigger="cron",
                                hour=user_time.hour,
                                minute=user_time.minute,
                                kwargs={
                                    "user_id": user_id,
                                    "group": group,
                                    "limit_changing": 9
                                })
        append_job_in_scheduler(user_id=user_id, time_str=time, job=job)

    await schedule_menu(message)
    print(f"[NOTIFICATION ON] {message.from_user.username}:{message.from_user.id}")


@dispatcher.message_handler(Text(contains="Выключить"), state=Schedule.notifications_ready)
async def schedule_main_notifications_disable(message: types.Message):
    user_id = message.from_user.id
    disable_notifications(user_id)
    disable_jobs(user_id)

    await schedule_menu(message)
    print(f"[NOTIFICATION OFF] {message.from_user.username}:{message.from_user.id}")


@dispatcher.message_handler(Text(contains="Группа"), state=[Schedule.notifications, Schedule.notifications_ready])
async def schedule_group_settings(message: types.Message):
    await ScheduleSettings.group.set()
    user_notify_data = get_user_data(message.from_user.id)
    group = user_notify_data[2] or None
    info_message = f"Текущая группа: {group}" if group else "Группа не установлена"
    await message.answer(text=info_message,
                         reply_markup=get_notifications_group_keyboard(group))


@dispatcher.message_handler(lambda message: n_text(message.text) in ["Установить группу", "Изменить группу"],
                            state=ScheduleSettings.group)
async def schedule_set_menu_group_settings(message: types.Message):
    user_id = message.from_user.id
    disable_notifications(user_id)
    disable_jobs(user_id)

    await ScheduleSettings.group_settings.set()

    with open("data/schedules/schedule_data_group.json", "r", encoding="utf-8-sig") as j_file:
        groups = json.load(j_file)

    await message.answer(text="Выберите группу:",
                         reply_markup=get_groups_keyboard(groups))


@dispatcher.message_handler(regexp=r"\w+-\d{2}", state=ScheduleSettings.group_settings)
async def schedule_choice_group_settings(message: types.Message):
    """Setting group to notification scheduler."""
    set_group_to_user(group=message.text, user_id=message.from_user.id)
    await message.answer(text="Группа установлена.")
    await schedule_menu(message)


@dispatcher.message_handler(Text(contains="Удалить группу"), state=ScheduleSettings.group)
async def schedule_del_group_settings(message: types.Message):
    user_id = message.from_user.id
    set_group_to_user(group="", user_id=user_id)
    disable_notifications(user_id)
    disable_jobs(user_id)

    await message.answer(text="Группа удалена.")
    await schedule_menu(message)


@dispatcher.message_handler(Text(contains="Время"), state=[Schedule.notifications, Schedule.notifications_ready])
async def schedule_time_settings(message: types.Message):
    await ScheduleSettings.time.set()
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    time_encoded = user_data[3] or '[]'

    notifications = user_data[1]
    time_settings = json.loads(time_encoded)
    if notifications and not time_settings:
        disable_notifications(user_id)

    times = '\n'.join(time_settings)
    info_message = f"Установлены следующие метки оповещения:\n{times}" \
        if time_settings else "Время не настроено."
    await message.answer(text=info_message,
                         reply_markup=get_main_time_keyboard(time_settings))


@dispatcher.message_handler(Text(contains="Удалить все метки"), state=ScheduleSettings.time)
async def schedule_set_time_settings(message: types.Message):
    user_id = message.from_user.id
    set_time_to_user("[]", user_id)
    disable_jobs(user_id)
    disable_notifications(user_id)

    await schedule_menu(message)


@dispatcher.message_handler(regexp=r"\d{1,2}:\d{1,2} .", state=ScheduleSettings.time)
async def schedule_set_time_settings(message: types.Message):
    """Deleting one job notification from scheduler."""
    user_id = message.from_user.id
    time_encoded = get_user_data(user_id)[3]
    time_settings: list = json.loads(time_encoded)
    try:
        if user_id in bot.notification_data:
            delete_job_from_scheduler(user_id, n_text(message.text))
        time_settings.remove(n_text(message.text))
        set_time_to_user(json.dumps(time_settings), user_id)
        await message.answer(text=f"Время {n_text(message.text)} удалено.",
                             reply_markup=get_main_time_keyboard(time_settings))

        if len(time_settings) == 0:
            disable_notifications(user_id)
            await schedule_menu(message)

    except ValueError:
        msg = await message.answer("Не лезь!")
        await message.delete()
        await sleep(5)
        await msg.delete()


@dispatcher.message_handler(Text(contains="Добавить время оповещения"), state=ScheduleSettings.time)
async def schedule_wait_time_settings(message: types.Message):
    await ScheduleSettings.time_set.set()
    times_for_example = '\n'.join([f"{randrange(1, 24):02}:{randrange(0, 60):02}" for _ in range(3)])
    await message.answer(text=f"Оповещение происходит на грядущие пары. Смена дня оповещения произойдет в 09:00.\n\n"
                              f"Пример формата времени:\n\n"
                              f"{times_for_example}")
    await message.answer(text="Введите время оповещения:")


@dispatcher.message_handler(regexp=r"\d{1,2}:\d{1,2}", state=ScheduleSettings.time_set)
async def schedule_set_time_settings(message: types.Message):
    """Adding new time to notification scheduler"""
    try:
        user_id = message.from_user.id
        dt.datetime.strptime(message.text, "%H:%M").time()  # checking to right format

        user_data = get_user_data(user_id)
        group, time_encoded = user_data[2], user_data[3] or '[]'
        time_settings: list = json.loads(time_encoded)
        time_settings.append(message.text)
        time_settings.sort(key=lambda x: dt.datetime.strptime(x, "%H:%M"))
        set_time_to_user(json.dumps(time_settings), user_id)

        user_dt_obj = dt.datetime.strptime(message.text, "%H:%M")

        if user_data[1]:
            job = scheduler.add_job(func=send_schedule_messages,
                                    trigger="cron",
                                    hour=user_dt_obj.hour,
                                    minute=user_dt_obj.minute,
                                    kwargs={
                                        "user_id": user_id,
                                        "group": group,
                                        "limit_changing": 9
                                    })
            append_job_in_scheduler(user_id=user_id, time_str=message.text, job=job)
        await schedule_menu(message)

    except ValueError:
        await message.delete()
        await message.answer(text="Неправильный формат! Попробуйте еще раз.")
