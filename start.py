from aiogram import executor

from bot import scheduler, dispatcher
from orm.schedules import SchedulesBase, SchedulesEngine
from orm.users import UsersBase, UsersEngine
from startup_shutdown import on_startup, on_shutdown

if __name__ == '__main__':
    UsersBase.metadata.create_all(bind=UsersEngine)
    SchedulesBase.metadata.create_all(bind=SchedulesEngine)
    scheduler.start()
    executor.start_polling(dispatcher=dispatcher,
                           skip_updates=True,
                           on_startup=on_startup,
                           on_shutdown=on_shutdown)
