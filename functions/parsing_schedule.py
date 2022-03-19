import re
import typing as t

import pandas as pd


def n_nan(obj):
    if repr(obj).lower() in ("nan", "nat"):
        return None
    return obj


def parse_to_days(loc: pd.DataFrame, days_and_pairs_block: pd.DataFrame):
    full_loc = days_and_pairs_block.join(loc)

    loc_days = {}
    start_day_index = 0
    for index, date, _ in days_and_pairs_block.itertuples():
        if n_nan(date):
            if index == 0:
                continue
            else:
                end_day_index = index
                loc_days[full_loc.iloc[start_day_index, 0]] = full_loc.iloc[start_day_index:end_day_index, 1:]
                start_day_index = index
    loc_days[full_loc.iloc[start_day_index, 0]] = full_loc.iloc[start_day_index:full_loc.shape[0] + 1, 1:]

    return loc_days


def parse_to_groups(xl) -> t.List[pd.DataFrame]:
    groups_data = []
    for col, loc in enumerate(xl):
        if re.match(r"\w+-\d{2}", loc):
            groups_data.append(xl.iloc[:, col:col + 3])
    return groups_data


def parse_to_pairs(loc: pd.DataFrame):
    reset_loc = loc.reset_index(drop=True)

    loc_pairs = {}
    start_pair_index = 0
    for index, pair, _, _, _ in reset_loc.itertuples():
        if n_nan(pair):
            if index == 0:
                continue
            else:
                end_pair_index = index
                loc_pairs[reset_loc.iloc[start_pair_index, 0]] = reset_loc.iloc[start_pair_index:end_pair_index, 1:]
                start_pair_index = index
    loc_pairs[reset_loc.iloc[start_pair_index, 0]] = reset_loc.iloc[start_pair_index:reset_loc.shape[0] + 1, 1:]

    return loc_pairs


def parser_by_group(filename):
    data = {}
    xl = pd.read_excel(f"data/schedules/{filename}", sheet_name=0)
    days_and_pairs_block: pd.DataFrame = xl.iloc[:, :2]

    groups = parse_to_groups(xl)
    for group in groups[:]:
        group_name = group.columns[0]
        data[group_name] = {}

        group_days = parse_to_days(group, days_and_pairs_block)
        for day, group_day_data in group_days.items():
            day = day.date().strftime("%d/%m/%y")
            data[group_name][day] = {}

            group_day_pairs = parse_to_pairs(group_day_data)
            for pair, group_day_pair_data in group_day_pairs.items():
                pair = int(float(pair))
                data[group_name][day][pair] = {}

                f_subject = n_nan(group_day_pair_data.iloc[0, 0])  # первый предмет
                f_teacher = n_nan(group_day_pair_data.iloc[1, 0])  # первый препод
                f_type = n_nan(group_day_pair_data.iloc[0, 1])  # первый тип занятия
                f_theme = n_nan(group_day_pair_data.iloc[0, 2])  # первая тема
                f_auditory = n_nan(group_day_pair_data.iloc[1, 2]) or n_nan(
                    group_day_pair_data.iloc[1, 1])  # первая аудитория

                data[group_name][day][pair]["f_subject"] = f_subject
                data[group_name][day][pair]["f_teacher"] = f_teacher
                data[group_name][day][pair]["f_type"] = f_type
                data[group_name][day][pair]["f_theme"] = f_theme
                data[group_name][day][pair]["f_auditory"] = f_auditory. \
                    replace("(ДВ)", "") if f_auditory is not None else f_auditory

                try:
                    s_subject = n_nan(group_day_pair_data.iloc[2, 0])  # второй предмет
                    s_auditory = n_nan(group_day_pair_data.iloc[2, 2]) or n_nan(
                        group_day_pair_data.iloc[2, 1])  # вторая аудитория

                    data[group_name][day][pair]["s_subject"] = s_subject
                    data[group_name][day][pair]["s_auditory"] = s_auditory

                except IndexError:
                    pass

                if group_day_pair_data.shape[0] == 4:
                    s_teacher = n_nan(group_day_pair_data.iloc[3, 0])  # второй препод
                    s_type = n_nan(group_day_pair_data.iloc[2, 1])  # второй тип занятия
                    s_theme = n_nan(group_day_pair_data.iloc[2, 2])  # вторая тема
                    s_auditory = n_nan(group_day_pair_data.iloc[3, 2]) or n_nan(
                        group_day_pair_data.iloc[3, 1])  # вторая аудитория

                    data[group_name][day][pair]["s_teacher"] = s_teacher
                    data[group_name][day][pair]["s_type"] = s_type
                    data[group_name][day][pair]["s_theme"] = s_theme
                    data[group_name][day][pair]["s_auditory"] = s_auditory. \
                        replace("(ДВ)", "") if f_auditory is not None else f_auditory
    return data


def parser_by_teacher(data_by_group: dict):
    data_by_teachers = dict()
    for group, data_in_date in data_by_group.items():
        for date, data_in_pair in data_in_date.items():
            for pair, old_pair_data in data_in_pair.items():
                try:
                    teacher = old_pair_data["f_teacher"]
                    if teacher:
                        if ~teacher.find("командир"):
                            continue

                        teacher = " ".join(teacher.split()[-2:])

                        teacher_data = data_by_teachers.setdefault(teacher, {})
                        date_data = teacher_data.setdefault(date, {})
                        pair_data = date_data.setdefault(pair, {})

                        pair_data["group"] = group
                        pair_data["subject"] = old_pair_data["f_subject"]
                        pair_data["subject_type"] = old_pair_data["f_type"]
                        pair_data["theme"] = old_pair_data["f_theme"]
                        pair_data["auditory"] = old_pair_data["f_auditory"]

                except (IndexError, KeyError):
                    pass

                try:
                    teacher = old_pair_data["s_teacher"]
                    if teacher:
                        if ~teacher.find("командир"):
                            continue

                        teacher = " ".join(teacher.split()[-2:])

                        teacher_data = data_by_teachers.setdefault(teacher, {})
                        date_data = teacher_data.setdefault(date, {})
                        pair_data = date_data.setdefault(pair, {})

                        pair_data["group"] = group
                        pair_data["subject"] = old_pair_data["s_subject"]
                        pair_data["subject_type"] = old_pair_data["s_type"]
                        pair_data["theme"] = old_pair_data["s_theme"]
                        pair_data["auditory"] = old_pair_data["s_auditory"]

                except (IndexError, KeyError):
                    pass

    return data_by_teachers
