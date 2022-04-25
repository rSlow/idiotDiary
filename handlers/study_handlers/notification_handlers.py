import datetime as dt
import logging
from asyncio import sleep
from random import randrange

from aiogram import types
from aiogram.dispatcher.filters import Text
from sqlalchemy.exc import NoResultFound

import constants
from FSM import Schedule, ScheduleSettings
from bot import dispatcher, scheduler, bot
from functions.main_functions import n_text
from functions.schedule_functions import send_schedule_messages
from keyboards import (get_notifications_settings_keyboard,
                       get_notifications_group_keyboard,
                       get_groups_keyboard,
                       get_main_time_keyboard)
from orm.users import UsersSession, User, Notification


@dispatcher.message_handler(Text(contains="Оповещение"), state=Schedule.start)
async def schedule_menu(message: types.Message):
    user_data = message.from_user

    with UsersSession() as session:
        user = session.query(User).filter(User.user_id == user_data.id).one_or_none()
        if not user:
            user = User(user_id=user_data.id, fullname=user_data.full_name, username_mention=user_data.mention)
            session.add(user)
            session.commit()
        await Schedule.notifications.set()
        if user.notify_group and user.notify_times:
            await Schedule.notifications_ready.set()
            header_text = "Оповещения включены:" if user.notify_status else "Оповещения выключены."
            await message.answer(text=header_text,
                                 reply_markup=get_notifications_settings_keyboard(user=user))

            await message.answer(f"<b>Группа</b>: {user.notify_group}",
                                 parse_mode="HTML")

            times_block_msg = "\n".join(
                map(lambda notification: notification.time.strftime(constants.TIME_FORMAT),
                    sorted(user.notify_times, key=lambda x: x.time))
            )
            await message.answer(f"<b>Временные метки</b>:\n{times_block_msg}",
                                 parse_mode="HTML")
        else:
            await message.answer(
                text=f"Оповещения не настроены. Кнопка для включения появится после настройки.",
                reply_markup=get_notifications_settings_keyboard(user=user))


@dispatcher.message_handler(Text(contains="Включить"), state=Schedule.notifications_ready)
async def schedule_notifications_enable(message: types.Message):
    user_data = message.from_user

    with UsersSession.begin() as session:
        user = User.get(user_id=user_data.id, session=session)
        user.notify_status = 1

        group = user.notify_group
        notifies = user.notify_times
        for notify in notifies:
            job = scheduler.add_job(func=send_schedule_messages,
                                    trigger="cron",
                                    hour=notify.time.hour,
                                    minute=notify.time.minute,
                                    kwargs={
                                        "user_id": user_data.id,
                                        "group": group,
                                        "limit_changing": 9
                                    })
            bot.notification_data.setdefault(user.user_id, {})[notify.time.strftime(constants.TIME_FORMAT)] = job

    await schedule_menu(message)
    logging.info(f"[NOTIFICATION ON] {message.from_user.username}:{message.from_user.id}")


@dispatcher.message_handler(Text(contains="Выключить"), state=Schedule.notifications_ready)
async def schedule_main_notifications_disable(message: types.Message):
    user_id = message.from_user.id
    User.disable_notifications(user_id=user_id)
    bot.disable_jobs(user_id)

    await schedule_menu(message)
    logging.info(f"[NOTIFICATION OFF] {message.from_user.username}:{message.from_user.id}")


@dispatcher.message_handler(Text(contains="Группа"), state=[Schedule.notifications, Schedule.notifications_ready])
async def schedule_group_settings(message: types.Message):
    await ScheduleSettings.group.set()
    user_id = message.from_user.id
    with UsersSession.begin() as session:
        user = User.get(user_id=user_id, session=session)
        info_message = f"Текущая группа: {user.notify_group}" if user.notify_group else "Группа не установлена"
        await message.answer(text=info_message,
                             reply_markup=get_notifications_group_keyboard(user.notify_group))


@dispatcher.message_handler(lambda message: n_text(message.text) in ["Установить группу", "Изменить группу"],
                            state=ScheduleSettings.group)
async def schedule_set_menu_group_settings(message: types.Message):
    user_id = message.from_user.id
    User.disable_notifications(user_id=user_id)
    bot.disable_jobs(user_id)

    await ScheduleSettings.group_settings.set()
    week = next(iter(bot.schedule_by_groups.values()))
    groups = week.groups
    await message.answer(text="Выберите группу:",
                         reply_markup=get_groups_keyboard(groups))


@dispatcher.message_handler(regexp=r"\w+-\d{2}", state=ScheduleSettings.group_settings)
async def schedule_choice_group_settings(message: types.Message):
    """Setting group to notification scheduler."""
    with UsersSession.begin() as session:
        user = session.query(User).filter(User.user_id == message.from_user.id).one()
        user.notify_group = message.text
    await message.answer(text="Группа установлена.")
    await schedule_menu(message)


@dispatcher.message_handler(Text(contains="Удалить группу"), state=ScheduleSettings.group)
async def schedule_del_group_settings(message: types.Message):
    user_id = message.from_user.id
    with UsersSession.begin() as session:
        user = session.query(User).filter(User.user_id == user_id).one()
        user.notify_group = None
        user.notify_status = False

    bot.disable_jobs(user_id)

    await message.answer(text="Группа удалена.")
    await schedule_menu(message)


@dispatcher.message_handler(Text(contains="Время"), state=[Schedule.notifications, Schedule.notifications_ready])
async def schedule_time_settings(message: types.Message):
    await ScheduleSettings.time.set()
    user_id = message.from_user.id
    times_list = []
    with UsersSession.begin() as session:
        user = User.get(user_id=user_id, session=session)
        if user.notify_times:
            times_list.extend(list(map(lambda notification: notification.time.strftime(constants.TIME_FORMAT),
                                       sorted(user.notify_times, key=lambda x: x.time))))
            times = '\n'.join(times_list)
            info_message = f"Установлены следующие метки оповещения:\n{times}"
        else:
            info_message = "Время не настроено."

    await message.answer(text=info_message,
                         reply_markup=get_main_time_keyboard(times_list))


@dispatcher.message_handler(Text(contains="Удалить все метки"), state=ScheduleSettings.time)
async def schedule_del_all_time_settings(message: types.Message):
    user_id = message.from_user.id
    with UsersSession.begin() as session:
        user = User.get(user_id=user_id, session=session)
        user.notify_times = []
        user.notify_status = False

    bot.disable_jobs(user_id)
    await schedule_menu(message)


@dispatcher.message_handler(regexp=r"\d{1,2}:\d{1,2} .", state=ScheduleSettings.time)
async def notification_time_delete(message: types.Message):
    """Deleting one job notification from scheduler."""
    user_id = message.from_user.id
    with UsersSession() as session:
        try:
            time_obj = dt.datetime.strptime(n_text(message.text), constants.TIME_FORMAT).time()
            notification = session.query(Notification).filter(Notification.user_id == user_id).filter(
                Notification.time == time_obj).one()
            session.delete(notification)
            session.commit()

            user = User.get(user_id=user_id, session=session)
            times_map_obj = list(map(lambda notify_data: notify_data.time.strftime(constants.TIME_FORMAT),
                                     sorted(user.notify_times, key=lambda x: x.time)))

            bot.notification_data[user_id][n_text(message.text)].remove()
            del bot.notification_data[user_id][n_text(message.text)]

            await message.answer(text=f"Время {n_text(message.text)} удалено.",
                                 reply_markup=get_main_time_keyboard(times_map_obj))

            if len(times_map_obj) == 0:
                user = User.get(user_id=notification.user_id, session=session)
                user.notify_status = False
                session.commit()
                await schedule_menu(message)

        except (ValueError, NoResultFound):
            msg = await message.answer("Не лезь!")
            await message.delete()
            await sleep(5)
            await msg.delete()


@dispatcher.message_handler(Text(contains="Добавить время оповещения"), state=ScheduleSettings.time)
async def notification_time_add_wait(message: types.Message):
    await ScheduleSettings.time_set.set()
    times_for_example = '\n'.join([f"{randrange(1, 24):02}:{randrange(0, 60):02}" for _ in range(3)])
    await message.answer(text=f"Оповещение происходит на грядущие пары. Смена дня оповещения произойдет в 09:00.\n\n"
                              f"Пример формата времени:\n\n"
                              f"{times_for_example}")
    await message.answer(text="Введите время оповещения:")


@dispatcher.message_handler(regexp=r"\d{1,2}:\d{1,2}", state=ScheduleSettings.time_set)
async def notification_time_add_confirm(message: types.Message):
    """Adding new time to notification scheduler"""
    try:
        user_data = message.from_user
        with UsersSession.begin() as session:
            user = User.get(user_id=user_data.id, session=session)
            time = dt.datetime.strptime(message.text, constants.TIME_FORMAT).time()
            session.add(Notification(
                user_id=user.user_id,
                time=time
            ))

            if user.notify_status == 1:
                job = scheduler.add_job(func=send_schedule_messages,
                                        trigger="cron",
                                        hour=time.hour,
                                        minute=time.minute,
                                        kwargs={
                                            "user_id": user.user_id,
                                            "group": user.notify_group,
                                            "limit_changing": 9
                                        })
                bot.notification_data.setdefault(user.user_id, {})[time.strftime(constants.TIME_FORMAT)] = job
        await schedule_menu(message)

    except ValueError:
        await message.delete()
        await message.answer(text="Неправильный формат! Попробуйте еще раз.")
