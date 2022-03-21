import aioimaplib
import email
import base64
import quopri
from datetime import datetime, date, timedelta
import pytz
import os
import pandas
import re
import json
import asyncio

from functions import parsing_schedule

login = "kursdvf.spb@mail.ru"
password = "Aq12sw23"
domain = "imap.mail.ru"

temp = "data/temp"


async def main():
    async def get_data_from_mail(num: str, client):
        fetch = await client.uid("fetch", num, "(RFC822)")
        return fetch

    def decode_msg_field(string: str, replace=True):
        pattern = re.compile(r"[=?]\S*[?]\w[?]\S+[?=]")

        match = re.search(pattern, string)
        while match:
            x, y = match.span()
            match_data = string[x:y][2:-2]
            encoding_last, encoding_first, data = match_data.split("?")
            if encoding_first.upper() == "B":
                decoded_data = base64.b64decode(data).decode(encoding_last)
                string = string.replace(string[x:y], decoded_data)
            elif encoding_first.upper() == "Q":
                decoded_data = quopri.decodestring(data).decode(encoding_last)
                string = string.replace(string[x:y], decoded_data)
            match = re.search(pattern, string)

        if replace:
            string = string.replace("\r\n ", "")
        return string

    def get_start_xl_date(name) -> date:
        xl = pandas.read_excel(f"{temp}/{name}", sheet_name=0)
        ts = xl.iloc[0, 0]
        dt = date.fromtimestamp(ts.value / 1e9)
        return dt

    def register(file_ts, file_dt):
        file_dt = file_dt.strftime("%d/%m/%y")
        if file_dt not in registry:
            registry[file_dt] = []
        registry[file_dt].append(file_ts)

    def check_in_registry(msg_ts) -> bool:
        for week_date in registry:
            if msg_ts in registry[week_date]:
                return True
        return False

    async def async_main():

        client = aioimaplib.IMAP4_SSL(domain)
        await client.wait_hello_from_server()

        await client.login(user=login, password=password)

        await client.select("INBOX")

        list_mails_bytes = await client.uid_search("ALL", charset=None)
        list_mails = list_mails_bytes.lines[0].decode().split()

        errors = 0
        for mail in reversed(list_mails):
            try:
                result, lines = await get_data_from_mail(mail, client)
                raw_email: bytearray = lines[1]
                raw_email_string = raw_email.decode(encoding="UTF-8", errors="ignore")
                msg = email.message_from_string(raw_email_string)
                msg_subj: str = decode_msg_field(msg["Subject"] or "").strip()
                date_msg: str = msg["Date"]
                datetime_obj = datetime.strptime(
                    date_msg[date_msg.find(",") + 2:],
                    "%d %b %Y %H:%M:%S %z"
                ).astimezone(pytz.timezone("Asia/Vladivostok"))

                delta = now - datetime_obj
                if delta.days > 0:
                    break
                if ~msg_subj.find("Расписание МЧС"):

                    msg_ts = int(datetime_obj.timestamp())
                    if check_in_registry(msg_ts):
                        continue

                    payload = msg.get_payload()[1]
                    filename_obj = payload["Content-Disposition"]
                    encoded_filename = filename_obj[filename_obj.find("=?UTF-8?"):-1]
                    decoded_filename = str(msg_ts) + "-" + decode_msg_field(encoded_filename)

                    encoded_attachment = payload.get_payload()
                    decoded_attachment_bytes = base64.b64decode(encoded_attachment)

                    with open(f"{temp}/{decoded_filename}", "wb") as file:
                        file.write(decoded_attachment_bytes)

            except Exception as ex:
                errors += 1
                print("[ERROR]", ex)
                if errors > 5:
                    raise ex

    def handle_temp_files():
        filenames = os.listdir(temp)
        for filename in filenames:
            xl_dt = get_start_xl_date(filename)

            xl_ts = int(filename.split("-")[0])

            os.rename(f"{temp}/{filename}", f"{temp}/{xl_ts}.xlsx")
            os.replace(f"{temp}/{xl_ts}.xlsx", f"data/schedules/{xl_ts}.xlsx")

            register(xl_ts, xl_dt)

    try:
        with open(f"data/schedules/schedules_registry.json", encoding="utf-8-sig") as reg_file:
            registry = json.load(reg_file)
    except FileNotFoundError:
        registry = {}

    now = datetime.now().astimezone(pytz.timezone("Asia/Vladivostok"))

    if not os.path.exists(temp):
        os.makedirs(temp, exist_ok=True)

    await async_main()

    handle_temp_files()

    with open(f"data/schedules/schedules_registry.json", "w", encoding="utf-8-sig") as j_file:
        json.dump(registry, j_file, indent=4, ensure_ascii=False)

    if now.isoweekday() > 6 or (now.isoweekday() == 6 and now.hour >= 14):
        actual_day = now - timedelta(days=now.weekday() - 7)
    else:
        actual_day = now - timedelta(days=now.weekday())
    actual_filename = f"{max(registry[actual_day.strftime('%d/%m/%y')])}.xlsx"

    return actual_filename


async def checking_schedule():
    actual_filename = await main()

    data_by_group = parsing_schedule.parser_by_group(actual_filename)

    with open(f"data/schedules/schedule_data_group.json", "w", encoding='utf-8-sig') as j_file:
        json.dump(data_by_group, j_file, indent=4, ensure_ascii=False)

    data_by_teachers = parsing_schedule.parser_by_teacher(data_by_group)

    with open(f"data/schedules/schedule_data_teacher.json", "w", encoding='utf-8-sig') as j_file:
        json.dump(data_by_teachers, j_file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    asyncio.run(main())
