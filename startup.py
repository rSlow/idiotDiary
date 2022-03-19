from bot import scheduler, bot
from functions import aioimap, append_job_in_scheduler
from database import get_all_notifications, get_all_users
import json
import datetime as dt
from functions.schedule_functions import send_schedule_messages


async def on_startup(_):
    bot.users.extend(get_all_users())
    # await aioimap.checking_schedule()

    for user_id, _, group, time_str in get_all_notifications():
        time_settings = json.loads(time_str)
        for time in time_settings:
            user_dt_obj = dt.datetime.strptime(time, "%H:%M")

            job = scheduler.add_job(func=send_schedule_messages,
                                    trigger="cron",
                                    hour=user_dt_obj.hour,
                                    minute=user_dt_obj.minute,
                                    kwargs={
                                        "user_id": user_id,
                                        "group": group,
                                        "limit_changing": 9
                                    })
            append_job_in_scheduler(user_id=user_id, time_str=time, job=job)

    scheduler.add_job(func=aioimap.checking_schedule,
                      trigger="interval",
                      seconds=60 * 60 * 6)
