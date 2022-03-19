from bot import bot

__all__ = (
    "disable_jobs",
    "append_job_in_scheduler",
    "delete_job_from_scheduler",
)


def disable_jobs(user_id):
    if user_id in bot.notification_data:
        for time, job in bot.notification_data[user_id].items():
            job.remove()
        del bot.notification_data[user_id]


def append_job_in_scheduler(user_id, time_str, job):
    if bot.notification_data.get(user_id) is None:
        bot.notification_data[user_id] = {}
    bot.notification_data[user_id][time_str] = job


def delete_job_from_scheduler(user_id, time_str):
    bot.notification_data[user_id][time_str].remove()
