from datetime import timedelta as td, datetime as dt

__all__ = (
    "n_text",
    "get_start_week_day",
)


def n_text(obj: str):
    return "".join([let for let in obj if let.isascii() or let.isalnum()]).strip()


def get_start_week_day(datetime: dt):
    if datetime.isoweekday() == 7 and datetime.hour >= 14:
        datetime -= td(days=datetime.weekday() - 7)
    else:
        datetime -= td(days=datetime.weekday())
    return datetime.date()
