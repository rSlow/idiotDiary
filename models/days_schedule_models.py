import datetime
from typing import Optional

import constants
from .group_schedule_models import ScheduleByGroup, WeekByGroup, DayByGroup


class ScheduleByDays(dict):
    def __init__(self, weeks_dict: Optional[dict[str, WeekByGroup]] = None):
        super(ScheduleByDays, self).__init__(weeks_dict or {})

    @classmethod
    async def from_group_schedule(cls, group_schedule_obj: ScheduleByGroup):
        weeks = {week_str: WeekByDays.from_group_week(week_obj) for week_str, week_obj in group_schedule_obj.items()}
        return cls(weeks)

    @property
    def weeks(self):
        return list(self.keys())

    def is_last_week(self, date: datetime.date):
        if date >= max(self.keys()):
            return True
        return False


class WeekByDays(dict):
    @classmethod
    def from_group_week(cls, week_obj: WeekByGroup):
        days = {}
        for group_name, group_obj in week_obj.items():
            for day, day_obj in group_obj.items():
                days.setdefault(day, DayByDays())[group_name] = GroupDayByDays.from_day_by_groups_obj(day_obj, day)
        return cls(days)

    @property
    def days(self):
        return list(self.keys())


class DayByDays(dict):
    @property
    def groups(self):
        return list(self.keys())


class GroupDayByDays(dict):
    def __init__(self, day: datetime.date):
        super(GroupDayByDays, self).__init__()
        self.day = day

    @property
    def pairs(self):
        return list(self.keys())

    @classmethod
    def from_day_by_groups_obj(cls, day_by_groups_obj: DayByGroup, day):
        day_by_days_obj = cls(day)
        day_by_days_obj.update(day_by_groups_obj.items())
        return day_by_days_obj

    @property
    def message_text(self):
        blocks = list()
        blocks.append(f"Пары на <u>{self.day.strftime(constants.DATE_FORMAT)}</u>:")
        for num, pair in self.items():
            blocks.append(f"\n\n<b><u>{num} пара:</u></b> ")
            blocks.append(pair.message_text)
        return "".join(blocks)
