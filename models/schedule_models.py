from datetime import date as d, timedelta as td
from typing import Optional
import logging

import pandas as pd
from numpy import nan


def to_date(dt64):
    return pd.Timestamp(dt64).to_pydatetime().date()


class Schedule(dict):
    def __init__(self, *dates_and_timestamps: Optional[str]):
        super(Schedule, self).__init__()
        self._temp_kw = {}
        self.filenames = {}

        for date, timestamp in dates_and_timestamps:
            self._data = pd.read_excel(f"data/schedules/{timestamp}.xlsx",
                                       sheet_name=0,
                                       header=None
                                       )
            self.filenames[date.strftime("%d/%m/%y")] = timestamp
            try:
                self._temp_kw.update(self._parse_to_weeks(self._data))
            except Exception as ex:
                logging.error(msg=ex)
                raise ex
            finally:
                del self._data

        self.update(self._temp_kw)
        del self._temp_kw

    def _parse_to_weeks(self, df):
        weeks = {}
        start_week_rows_idx = df.loc[df[0] == "дата/пара"].index.to_list()
        start_week_rows_idx.append(self._data.shape[0] + 1)

        start_index = start_week_rows_idx[0]
        for idx in start_week_rows_idx[1:]:
            week: pd.DataFrame = df.iloc[start_index:idx]
            week.set_index(0, inplace=True)
            week.columns = week.iloc[0]
            week: pd.DataFrame = week.iloc[1:]

            start_date = to_date(week.index.values[0])
            start_date -= td(days=start_date.weekday())
            weeks[start_date] = Week(week, start_date)

            start_index = idx
        return weeks

    @property
    def weeks(self):
        return list(self.keys())

    def get_actual_filename(self):
        for timestamp in sorted(self.values()):
            return f"{timestamp}.xlsx"

    def is_last(self, date: d):
        if date >= max(self.keys()):
            return True
        return False

    def __str__(self):
        return f"Schedule{self.weeks}"


class Week(dict):
    def __init__(self, dataframe: pd.DataFrame, start_date=None):
        super(Week, self).__init__()
        self.data = dataframe
        self.start_date = start_date or to_date(self.data.index.values[0])

        self.pair_block: pd.DataFrame = self.data.iloc[:, 0]
        self.update(self._parse_to_groups())

        del self.data, self.pair_block

    def _parse_to_groups(self):
        groups = {}
        group_names = self.data.filter(regex=r"\w+-\d{2}").columns
        idx_groups = [self.data.columns.get_loc(group_name) for group_name in group_names]

        for idx in idx_groups:
            group: pd.DataFrame = self.data.iloc[:, idx:idx + 3]
            group.insert(loc=0,
                         column="пара",
                         value=self.pair_block)
            group_name = group.iloc[:, 1].name
            groups[group_name] = Group(group, group_name, self.start_date)
        return groups

    @property
    def groups(self):
        return list(self.keys())

    @classmethod
    def from_filename(cls, filename):
        df = pd.read_excel(f"data/schedules/{filename}",
                           sheet_name=0,
                           na_values="",
                           header=0,
                           index_col=0)
        return cls(df)


class Group(dict):
    def __init__(self, dataframe: pd.DataFrame, group_name, start_date):
        super(Group, self).__init__()
        self.data = dataframe
        self.start_date = start_date
        self.group_name = group_name
        self.update(self._parse_to_days())

        del self.data

    def _parse_to_days(self):
        days = {}
        dates = self.data.loc[self.data.index.notna()].index.to_list()

        days_idx = [self.data.index.get_loc(date) for date in dates]
        days_idx.append(self.data.shape[0] + 1)

        start_idx = days_idx[0]
        for idx in days_idx[1:]:
            day_data = self.data.iloc[start_idx:idx]
            day = to_date(day_data.index.values[0])
            day_obj = Day(day_data, day)
            if day_obj:
                days[day] = day_obj
            start_idx = idx
        return days

    @property
    def days(self):
        return list(self.keys())

    @property
    def message_text(self):
        blocks = list()
        blocks.append(f"<b><u>Пары на неделю с "
                      f"{self.days[0].strftime('%d/%m/%y')} "
                      f"по {self.days[-1].strftime('%d/%m/%y')}"
                      f"</u></b>")

        for date, day in self.items():
            blocks.append(f"\n\n{day.message_text}")
        return "".join(blocks)


class Day(dict):
    def __init__(self, dataframe: pd.DataFrame, day):
        super(Day, self).__init__()
        self.data = dataframe.reset_index(drop=True)
        self.day = day
        self.update(self._parse_to_pairs())

        del self.data

    def _parse_to_pairs(self):
        pairs = {}
        pairs_idx = self.data.loc[self.data["пара"].notna()].index.to_list()
        if not pairs_idx:
            self.data["пара"] = pd.DataFrame([1, nan, nan, 2, nan, nan, 3])
            pairs_idx.extend([0, 3, 6])
        pairs_idx.append(self.data.shape[0] + 1)

        start_idx = pairs_idx[0]
        for idx in pairs_idx[1:]:
            pair_data = self.data.iloc[start_idx:idx]
            pair_num = int(pair_data.iloc[0, 0])
            pair_obj = Pair(pair_data.iloc[:, 1:], pair_num)
            if pair_obj:
                pairs[pair_num] = pair_obj
            start_idx = idx
        return pairs

    @property
    def pairs(self):
        return list(self.keys())

    @property
    def message_text(self):
        blocks = list()
        blocks.append(f"Пары на <u>{self.day.strftime('%d/%m/%y')}</u>:")
        for num, pair in self.items():
            blocks.append(f"\n\n<b><u>{num} пара: </u></b>")
            blocks.append(pair.message_text)
        return "".join(blocks)

    def __bool__(self):
        for val in self.values():
            if val:
                return True
        return False


class Pair:
    def __init__(self, dataframe: pd.DataFrame, pair_num):
        self.data = dataframe.fillna(value="")
        self.pair_num = pair_num
        self._parse()
        del self.data

    def _set_attr(self, name, loc):
        first_value = loc[0]
        try:
            second_value = loc[1]
        except IndexError:
            second_value = first_value

        try:
            data = self.data.iloc[first_value[0], first_value[1]] or self.data.iloc[second_value[0], second_value[1]]
            if data:
                setattr(self, name, data)
        except IndexError:
            pass

    def _parse(self):
        keys_3 = {
            "first_subject": ((0, 0),),
            "first_teacher": ((1, 0),),
            "first_type": ((0, 1),),
            "first_theme": ((0, 2),),
            "first_auditory": ((1, 2), (1, 1)),
            "second_subject": ((2, 0),),
            "second_auditory": ((2, 2), (2, 1))
        }
        keys_4 = {
            "second_teacher": ((3, 0),),
            "second_type": ((2, 1),),
            "second_theme": ((2, 2),),
            "second_auditory": ((3, 2), (3, 1)),
        }

        for name, loc in keys_3.items():
            self._set_attr(name, loc)

        if len(self.data) == 4:
            for name, loc in keys_4.items():
                self._set_attr(name, loc)

    def __bool__(self):
        attrs = self.__dict__.copy()
        del attrs["pair_num"]
        return True if attrs else False

    @property
    def message_text(self):
        blocks = []

        first_subject = getattr(self, "first_subject", None)
        if first_subject:
            blocks.append(f"<b>{first_subject}</b>")

        first_auditory = getattr(self, "first_auditory", None)
        if first_auditory:
            blocks.append(f" - аудитория {first_auditory}")

        first_theme = getattr(self, "first_theme", None)
        if first_theme:
            blocks.append(f"\nтема № {first_theme}")

        first_type = getattr(self, "first_type", None)
        if first_type:
            blocks.append(f" ({first_type})")

        first_teacher = getattr(self, "first_teacher", None)
        if first_teacher:
            blocks.append(f" - {first_teacher}")

        second_subject = getattr(self, "second_subject", None)
        if second_subject:
            blocks.append(f"\n<b>{second_subject}</b>")

        second_auditory = getattr(self, "second_auditory", None)
        if second_auditory:
            blocks.append(f" - аудитория {second_auditory}")

        second_theme = getattr(self, "second_theme", None)
        if second_theme:
            blocks.append(f"\nтема № {second_theme}")

        second_type = getattr(self, "second_type", None)
        if second_type:
            blocks.append(f" ({second_type})")

        second_teacher = getattr(self, "second_teacher", None)
        if second_teacher:
            blocks.append(f" - {second_teacher}")

        return "".join(blocks)


if __name__ == '__main__':
    s = Schedule("a2-f15-m32953-2.xlsx")
    print(s)
