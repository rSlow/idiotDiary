import logging

from bot import scheduler, bot
# from functions.imap_downloading import checking_schedule
from functions.schedule_functions import send_schedule_messages
from orm.users import UsersSession, User


async def on_startup(_):
    try:
        import handlers
    except ImportError as ex:
        logging.warn(msg=ex)

    with UsersSession() as session:
        all_users = [userdata[0] for userdata in session.query(User.user_id).all()]
        bot.users.extend(all_users)
        all_notifications_data: list[User] = session.query(User).filter(User.notify_status == 1).all()
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
                bot.notification_data.setdefault(user.user_id, {})[notification.time.strftime("%H:%M")] = job
    # logging.info(msg="Updating schedule with IMAP...")
    # await checking_schedule()
    # scheduler.add_job(func=checking_schedule,
    #                   trigger="interval",
    #                   seconds=60 * 60 * 6)


async def on_shutdown(_):
    print("[BOT STOP] Bot has been closed.")
