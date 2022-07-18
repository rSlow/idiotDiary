from datetime import date as d, timedelta as td

import constants


class ScheduleByDays:
    def __init__(self, schedule):
        self.weeks = [WeekByDays(week) for week in schedule.weeks]

    @property
    def weeks_list(self):
        return [week.monday_day for week in self.weeks]

    @property
    def first_week(self):
        return self.weeks[0]

    def __getitem__(self, key):
        for week in self.weeks:
            if week.monday_day == key:
                return week
        else:
            raise KeyError

    def next_week_is_last(self, date: d):
        try:
            return self[date + td(days=7)] is None
        except KeyError:
            return True


class WeekByDays:
    def __init__(self, week):
        self.monday_day = week.monday_day
        self.days = []

        for day in week.all_days_list:
            day_obj = DayByDays(day)
            for group in week.groups:
                day_obj.groups.append(GroupDayByDays(group, day))
            self.days.append(day_obj)

    @property
    def days_list(self):
        return [day.day for day in self.days]

    def __getitem__(self, key):
        for day in self.days:
            if day.day == key:
                return day
        else:
            raise KeyError


class DayByDays:
    def __init__(self, day: d):
        self.day = day
        self.groups = []

    @property
    def groups_list(self):
        return [group.name for group in self.groups]

    def __getitem__(self, key):
        for group in self.groups:
            if group.name == key:
                return group
        else:
            raise KeyError


class GroupDayByDays:
    def __init__(self, group, day: d):
        self.day = day
        self.name = group.name
        self.pairs = group[day].pairs

    @property
    def message_text(self):
        blocks = list()
        blocks.append(f"Пары на <u>{self.day:{constants.DATE_FORMAT}}</u>:")
        for pair in self.pairs:
            blocks.append(f"\n\n<b><u>{pair.pair_num} пара:</u></b> ")
            blocks.append(pair.message_text)
        return "".join(blocks)
