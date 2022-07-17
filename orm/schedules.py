from datetime import timedelta as td

import pandas as pd
from numpy import nan
from sqlalchemy import Column, Integer, Date, String
from sqlalchemy import ForeignKey
from sqlalchemy import select, func, desc
from sqlalchemy.orm import relationship, selectinload

from functions.main_functions import get_start_week_day, to_date, get_required_datetime
from orm.base import Base, Session


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)

    # down
    weeks = relationship("Week",
                         back_populates="file",
                         cascade="all, delete, delete-orphan")

    @staticmethod
    def _to_weeks_df_list(file_df: pd.DataFrame):
        weeks_df_list = []
        weeks_idx = file_df.loc[file_df[0] == "дата/пара"].index.to_list()
        weeks_idx.append(file_df.shape[0] + 1)

        start_week_idx = weeks_idx[0]
        for week_idx in weeks_idx[1:]:
            week_xl: pd.DataFrame = file_df.iloc[start_week_idx:week_idx]
            week_xl.set_index(0, inplace=True)
            week_xl.columns = week_xl.iloc[0]
            week_xl: pd.DataFrame = week_xl.iloc[1:]

            start_week_idx = week_idx
            weeks_df_list.append(week_xl)

        return weeks_df_list

    @classmethod
    def from_file(cls, file_io_or_name, timestamp):
        file_xl = pd.read_excel(
            io=file_io_or_name,
            sheet_name=0,
            header=None
        )

        weeks_df_list = cls._to_weeks_df_list(file_xl)
        file = cls(
            timestamp=timestamp,
            weeks=[Week.from_df(week_df) for week_df in weeks_df_list]
        )

        return file

    async def to_db(self):
        async with Session() as session:
            async with session.begin():
                session.add(self)

    @classmethod
    async def get_last_timestamp(cls):
        async with Session() as session:
            q = select(
                func.max(cls.timestamp)
            )
            res = await session.execute(q)
            return res.scalars().one() or 0


class Week(Base):
    __tablename__ = "weeks"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey(File.id))

    monday_day = Column(Date)

    # up
    file = relationship("File",
                        back_populates="weeks")
    # down
    groups = relationship("Group",
                          back_populates="week",
                          cascade="all, delete, delete-orphan")

    @staticmethod
    def _get_monday_date(df):
        start_date = to_date(df.index.values[0])
        start_date -= td(days=start_date.weekday())
        return start_date

    @classmethod
    def from_df(cls, df):
        monday_day = cls._get_monday_date(df)
        groups_df_list = cls._to_groups_df_list(df)

        return cls(
            monday_day=monday_day,
            groups=[Group.from_df(group_df) for group_df in groups_df_list]
        )

    @staticmethod
    def _to_groups_df_list(week_df: pd.DataFrame):
        groups_df_list = []
        pair_block: pd.Series = week_df.iloc[:, 0]
        group_names = week_df.filter(regex=r"\w+-\d+").columns
        idx_groups = [week_df.columns.get_loc(group_name) for group_name in group_names]

        for group_idx in idx_groups:
            group_xl: pd.DataFrame = week_df.iloc[:, group_idx:group_idx + 3]
            group_xl.insert(loc=0,
                            column="пара",
                            value=pair_block)
            groups_df_list.append(group_xl)

        return groups_df_list

    @classmethod
    async def get_actual_weeks(cls):
        async with Session() as session:
            sub_q = select(
                cls.monday_day, func.max(File.timestamp)
            ).join(
                File
            ).filter(
                cls.monday_day >= get_start_week_day(get_required_datetime(limit_changing=14))
            ).group_by(
                cls.monday_day
            ).order_by(
                cls.monday_day
            )

            result = (await session.execute(sub_q)).fetchall()

            weeks_list = []
            for monday, timestamp in result:
                q = select(
                    cls
                ).join(
                    File
                ).filter(
                    cls.monday_day == monday
                ).filter(
                    File.timestamp == timestamp
                ).options(
                    selectinload(cls.groups).selectinload(Group.days).selectinload(Day.pairs)
                )
                week = (await session.execute(q)).scalars().one_or_none()

                if week is not None:
                    weeks_list.append(week)

            if len(weeks_list) == 0:
                q = select(
                    Week
                ).order_by(
                    desc(cls.monday_day)
                ).options(
                    selectinload(cls.groups).selectinload(Group.days).selectinload(Day.pairs)
                )
                res = await session.execute(q)
                weeks_list = [res.scalars().first()]

        return weeks_list


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    week_id = Column(Integer, ForeignKey(Week.id))

    name = Column(String(20))

    # up
    week = relationship("Week",
                        back_populates="groups")
    # down
    days = relationship("Day",
                        back_populates="group",
                        cascade="all, delete, delete-orphan")

    @staticmethod
    def _get_group_name(df):
        name = df.iloc[:, 1].name
        return name

    @classmethod
    def from_df(cls, df):
        group_name = cls._get_group_name(df)
        days_df_list = cls._to_days_df_list(df)

        return cls(
            name=group_name,
            days=[Day.from_df(day_df) for day_df in days_df_list]
        )

    @staticmethod
    def _to_days_df_list(group_df: pd.DataFrame):
        days_df_list = []
        dates = group_df.loc[group_df.index.notna()].index.to_list()

        days_idx = [group_df.index.get_loc(date) for date in dates]
        days_idx.append(group_df.shape[0] + 1)

        start_day_idx = days_idx[0]
        for day_idx in days_idx[1:]:
            day_df = group_df.iloc[start_day_idx:day_idx]
            days_df_list.append(day_df)
            start_day_idx = day_idx

        return days_df_list


class Day(Base):
    __tablename__ = "days"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey(Group.id))

    day = Column(Date)

    # up
    group = relationship("Group",
                         back_populates="days")
    # down
    pairs = relationship("Pair",
                         back_populates="day",
                         cascade="all, delete, delete-orphan")

    @staticmethod
    def _get_day(df):
        day = to_date(df.index.values[0])
        return day

    @classmethod
    def from_df(cls, df):
        day = cls._get_day(df)
        pairs_df_list = cls._to_pairs_df_list(df)

        return cls(
            day=day,
            pairs=[Pair.from_df(pair_df) for pair_df in pairs_df_list]
        )

    @staticmethod
    def _to_pairs_df_list(day_df: pd.DataFrame):
        pairs_df_list = []
        day_df = day_df.reset_index(drop=True)
        pairs_idx = day_df.loc[day_df["пара"].notna()].index.to_list()
        if not pairs_idx:
            day_df["пара"] = pd.DataFrame([1, nan, nan, 2, nan, nan, 3])
            pairs_idx.extend([0, 3, 6])
        pairs_idx.append(day_df.shape[0] + 1)

        start_pair_idx = pairs_idx[0]
        for pair_idx in pairs_idx[1:]:
            pair_xl = day_df.iloc[start_pair_idx:pair_idx]
            pairs_df_list.append(pair_xl)

            start_pair_idx = pair_idx

        return pairs_df_list


class Pair(Base):
    __tablename__ = "pairs"

    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey(Day.id))

    pair_num = Column(Integer)

    first_subj_name = Column(String(255), nullable=True)
    first_subj_auditory = Column(String(255), nullable=True)
    first_subj_teacher = Column(String(255), nullable=True)
    first_subj_type = Column(String(255), nullable=True)
    first_subj_theme = Column(String(255), nullable=True)

    second_subj_name = Column(String(255), nullable=True)
    second_subj_auditory = Column(String(255), nullable=True)
    second_subj_teacher = Column(String(255), nullable=True)
    second_subj_type = Column(String(255), nullable=True)
    second_subj_theme = Column(String(255), nullable=True)

    # up
    day = relationship("Day",
                       back_populates="pairs")

    @staticmethod
    def _get_pair_num(df):
        return int(df.iloc[0, 0])

    @classmethod
    def from_df(cls, df):
        pair_num = cls._get_pair_num(df)
        df = df.fillna(value="").iloc[:, 1:]

        pair = cls(
            pair_num=pair_num
        )
        pair.set_attrs_from_df(df)
        return pair

    def set_attrs_from_df(self, df: pd.DataFrame):
        keys_3 = {
            "first_subj_name": ((0, 0),),
            "first_subj_auditory": ((1, 2), (1, 1)),
            "first_subj_teacher": ((1, 0),),
            "first_subj_type": ((0, 1),),
            "first_subj_theme": ((0, 2),),
            "second_subj_name": ((2, 0),),
            "second_subj_auditory": ((2, 2), (2, 1))
        }
        keys_4 = {
            "second_subj_teacher": ((3, 0),),
            "second_subj_type": ((2, 1),),
            "second_subj_theme": ((2, 2),),
            "second_subj_auditory": ((3, 2), (3, 1)),
        }

        for attr_name, location in keys_3.items():
            self._set_attr(df, attr_name, location)

        if len(df) == 4:
            for attr_name, location in keys_4.items():
                self._set_attr(df, attr_name, location)

    def _set_attr(self, df, attr_name, location):
        first_value = location[0]
        try:
            second_value = location[1]
        except IndexError:
            second_value = first_value

        try:
            data = df.iloc[first_value[0], first_value[1]] or df.iloc[
                second_value[0], second_value[1]]
            if data:
                setattr(self, attr_name, data)
        except IndexError:
            pass

    @property
    def message_text(self):
        blocks = []

        if first_subj_name := getattr(self, "first_subj_name", None):
            blocks.append(f"<b>{first_subj_name}</b>")

        if first_subj_auditory := getattr(self, "first_subj_auditory", None):
            blocks.append(f" - аудитория {first_subj_auditory}")

        if first_subj_theme := getattr(self, "first_subj_theme", None):
            blocks.append(f"\nтема № {first_subj_theme}")

        if first_subj_type := getattr(self, "first_subj_type", None):
            blocks.append(f" ({first_subj_type})")

        if first_subj_teacher := getattr(self, "first_subj_teacher", None):
            blocks.append(f" - {first_subj_teacher}")

        if second_subj_name := getattr(self, "second_subj_name", None):
            blocks.append(f"\n<b>{second_subj_name}</b>")

        if second_subj_auditory := getattr(self, "second_subj_auditory", None):
            blocks.append(f" - аудитория {second_subj_auditory}")

        if second_subj_theme := getattr(self, "second_subj_theme", None):
            blocks.append(f"\nтема № {second_subj_theme}")

        if second_subj_type := getattr(self, "second_subj_type", None):
            blocks.append(f" ({second_subj_type})")

        if second_subj_teacher := getattr(self, "second_subj_teacher", None):
            blocks.append(f" - {second_subj_teacher}")

        return "".join(blocks)

    def __bool__(self):
        return True


if __name__ == '__main__':
    async def main():
        from orm.base import create_database
        await create_database()
        # async with Session() as session:
        #     async with session.begin():
        #         res = await session.execute(select(
        #             Week
        #         ).filter(
        #             Week.id == 6
        #         ))
        #         w = res.scalars().one()
        #         await session.delete(w)
        try:
            result = await Week.get_actual_weeks()
            return result
        except ImportError:
            pass


    try:
        import asyncio

        r = asyncio.run(main())
    except ImportError as ex:
        import logging

        logging.error(msg="IMPORT ERROR", exc_info=ex)
