from bot import bot

__all__ = (
    "disable_jobs",
)


def disable_jobs(user_id):
    if user_id in bot.notification_data:
        for time, job in bot.notification_data[user_id].items():
            job.remove()
        del bot.notification_data[user_id]
