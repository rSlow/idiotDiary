import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot import scheduler, bot
from functions.schedule_functions import send_schedule_messages
from orm.base import Session, create_database
from orm.users import User
import constants


async def on_startup(_):
    try:
        import handlers
    except ImportError as ex:
        logging.warn(msg=ex)

    await create_database()

    scheduler.start()

    logging.info(msg="[UPDATE SCHEDULE] Start to updating schedule...")
    await bot.update_schedules()

    async with Session() as session:
        async with session.begin():
            result = await session.execute(select(User.user_id))
            bot.users.extend(result.scalars().all())

            all_notifications_data: list[User] = (await session.execute(
                select(
                    User
                ).where(
                    User.notify_status is True
                ).options(
                    selectinload(User.notify_times)
                )
            )).scalars().all()

            for user in all_notifications_data:
                for notification in user.notify_times:
                    job = scheduler.add_job(func=send_schedule_messages,
                                            trigger="cron",
                                            hour=notification.time.hour,
                                            minute=notification.time.minute,
                                            kwargs={
                                                "user_id": user.user_id,
                                                "group": user.notify_group,
                                                "limit_changing": 9
                                            })
                    bot.notification_data.setdefault(user.user_id, {})[
                        notification.time.strftime(constants.TIME_FORMAT)
                    ] = job

        scheduler.add_job(func=bot.update_schedules,
                          trigger="interval",
                          seconds=60 * 60 * 6)


async def on_shutdown(_):
    logging.info("[BOT STOP] Bot has been closed.")
