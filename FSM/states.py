from aiogram.dispatcher.filters.state import StatesGroup, State


class Schedule(StatesGroup):
    start = State()
    notifications = State()
    notifications_ready = State()
    settings = State()
    category = State()

    group = State()
    date_for_group = State()

    teacher = State()
    date_for_teacher = State()


class DownloadLibrary(StatesGroup):
    library = State()
    downloading_book = State()


class ScheduleSettings(StatesGroup):
    group = State()
    group_settings = State()
    time = State()
    time_set = State()


class FSMAdmin(StatesGroup):
    start = State()
    stop = State()
    mailing = State()
    schedule = State()
    download_schedule = State()
