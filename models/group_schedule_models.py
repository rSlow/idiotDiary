from datetime import date as d, timedelta as td

import constants
from orm import schedules


class ScheduleByGroup:
    def __init__(self, orm_weeks: list[schedules.Week]):
        self.weeks = [WeekByGroup(orm_week) for orm_week in orm_weeks]

    @classmethod
    async def from_db(cls):
        weeks_list = await schedules.Week.get_actual_weeks()
        return cls(weeks_list)

    @property
    def first_week(self):
        return self.weeks[0]

    @property
    def weeks_list(self):
        return [week.monday_day for week in self.weeks]

    def __getitem__(self, key):
        for week in self.weeks:
            if week.monday_day == key:
                return week
        else:
            raise KeyError

    def next_week_is_last(self, date: d, group):
        try:
            return self[date + td(days=7)][group] is None
        except KeyError:
            return True


class WeekByGroup:
    def __init__(self, orm_week: schedules.Week):
        self.groups = [GroupByGroup(orm_group) for orm_group in orm_week.groups]
        self.monday_day = orm_week.monday_day

    def __str__(self):
        return f"Week from {self.monday_day}"

    def __getitem__(self, key):
        for group in self.groups:
            if group.name == key:
                return group
        else:
            raise KeyError

    @property
    def all_days_list(self):
        days = []
        for group in self.groups:
            for day in group.days:
                if day.day not in days:
                    days.append(day.day)
        return days

    @property
    def groups_list(self):
        return [group.name for group in self.groups]


class GroupByGroup:
    def __init__(self, orm_group: schedules.Group):
        self.days = [DayByGroup(orm_day) for orm_day in orm_group.days]
        self.name = orm_group.name

    @property
    def message_text(self):
        blocks = list()
        blocks.append(f"<b><u>Пары на неделю с "
                      f"{self.days[0].day.strftime(constants.DATE_FORMAT)} "
                      f"по {self.days[-1].day.strftime(constants.DATE_FORMAT)}"
                      f"</u></b>")

        for day in self.days:
            blocks.append(f"\n\n{day.message_text}")
        return "".join(blocks)

    @property
    def days_list(self):
        return [day.day.strftime(constants.DATE_FORMAT) for day in self.days]

    def __str__(self):
        return f"Group {self.name}"

    def __getitem__(self, key):
        for day in self.days:
            if day.day == key:
                return day
        else:
            raise KeyError


class DayByGroup:
    def __init__(self, orm_day: schedules.Day):
        self.pairs = [orm_pair for orm_pair in orm_day.pairs]
        self.day = orm_day.day

    @property
    def message_text(self):
        blocks = list()
        blocks.append(f"Пары на <u>{self.day.strftime(constants.DATE_FORMAT)}</u>:")
        for pair in self.pairs:
            if pair:
                blocks.append(f"\n\n<b><u>{pair.pair_num} пара:</u></b> ")
                blocks.append(pair.message_text)
        return "".join(blocks)

    def __bool__(self):
        for val in self.pairs:
            if val:
                return True
        return False
