from aiogram import executor
from handlers import *
from bot import scheduler
from startup import on_startup

if __name__ == '__main__':
    scheduler.start()
    executor.start_polling(dispatcher=dispatcher,
                           skip_updates=True,
                           on_startup=on_startup)
