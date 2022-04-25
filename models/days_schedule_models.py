import datetime

from .group_schedule_models import ScheduleByGroup, WeekByGroup, DayByGroup, PairByGroup
from typing import Optional
import constants


class ScheduleByDays(dict):
    def __init__(self, weeks_dict: Optional[dict[str, WeekByGroup]] = None):
        super(ScheduleByDays, self).__init__(weeks_dict or {})

    @classmethod
    def from_group_schedule(cls, group_schedule_obj: ScheduleByGroup):
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


class PairByDays:
    @classmethod
    def from_pair_by_group_obj(cls, pair_by_group_obj: PairByGroup):
        pair_by_days_obj = cls()
        keys = [
            "first_subject",
            "first_teacher",
            "first_type",
            "first_theme",
            "first_auditory",
            "second_subject",
            "second_auditory",
            "second_teacher",
            "second_type",
            "second_theme",
            "second_auditory"
        ]
        for attr in keys:
            by_group_attr = getattr(pair_by_group_obj, attr, None)
            if by_group_attr:
                setattr(pair_by_days_obj, attr, by_group_attr)
        return pair_by_days_obj

    @property
    def message_text(self):
        return lambda: PairByGroup.message_text
