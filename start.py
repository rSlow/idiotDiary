from aiogram import executor
from handlers import *
from bot import scheduler
from startup_shutdown import on_startup, on_shutdown
from database import Base, engine

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    scheduler.start()
    executor.start_polling(dispatcher=dispatcher,
                           skip_updates=True,
                           on_startup=on_startup,
                           on_shutdown=on_shutdown)
