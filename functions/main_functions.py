from datetime import timedelta as td, datetime as dt, date as d

from pandas import Timestamp

import constants

__all__ = (
    "n_text",
    "get_start_week_day",
    "to_date",
    "get_required_date",
    "get_required_datetime",
)


def n_text(obj: str):
    return "".join([let for let in obj if let.isascii() or let.isalnum()]).strip()


def get_start_week_day(dt_obj: dt = None):
    if dt_obj is None:
        dt_obj = dt.now(tz=constants.TIMEZONE)

    if dt_obj.isoweekday() == 7 and dt_obj.hour >= 14:
        dt_obj -= td(days=dt_obj.weekday() - 7)
    else:
        dt_obj -= td(days=dt_obj.weekday())
    d_obj = dt_obj.date()

    return d_obj


def to_date(dt64) -> d:
    return Timestamp(dt64).to_pydatetime().date()


def get_required_date(limit_changing=None):
    return get_required_datetime(limit_changing=limit_changing).date()


def get_required_datetime(limit_changing=None):
    now = dt.now(tz=constants.TIMEZONE)
    if limit_changing:
        if now.hour >= limit_changing:
            now += td(days=1)
    return now
