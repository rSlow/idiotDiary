from aiogram.dispatcher.filters.state import StatesGroup, State


class Schedule(StatesGroup):
    start = State()
    notifications = State()
    notifications_ready = State()
    files = State()
    settings = State()


class ScheduleByGroup(StatesGroup):
    group = State()
    date_for_group = State()


class ScheduleByDay(StatesGroup):
    day = State()
    group_for_day = State()


class ScheduleByTeacher(StatesGroup):
    teacher = State()
    group_for_teacher = State()


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
