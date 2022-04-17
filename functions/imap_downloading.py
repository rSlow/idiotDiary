import asyncio
import base64
import email
import os
import quopri
import re
from datetime import datetime
import logging
from email.message import Message

import aioimaplib
import pandas as pd
import pytz

from bot import bot
from models import Schedule
from orm.schedules import Schedule as ORMSchedule
from orm.schedules import SchedulesSession

LOGIN_EMAIL = "kursdvf.spb@mail.ru"
PASSWORD_EMAIL = "Aq12sw23"
DOMAIN_IMAP = "imap.mail.ru"

TEMP = "data/temp"


async def download_from_email():
    async def get_data_from_mail(num: str, client):
        fetch = await client.uid("fetch", num, "(RFC822)")
        return fetch

    def decode_msg_field(string: str, replace=True):
        pattern = re.compile(r"[=?]\S*[?]\w[?]\S+[?=]")

        match = re.search(pattern, string)
        try:
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
        except ValueError:
            return string

        if replace:
            string = string.replace("\r\n ", "")
        return string

    async def download_files_to_temp():

        client = aioimaplib.IMAP4_SSL(DOMAIN_IMAP)
        await client.wait_hello_from_server()

        await client.login(user=LOGIN_EMAIL, password=PASSWORD_EMAIL)

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
                if delta.days > 0:  # limit days within today and message day
                    break
                if ~msg_subj.find("Расписание МЧС"):

                    msg_ts = int(datetime_obj.timestamp())
                    if msg_ts in loaded_timestamps:
                        break

                    payload = msg.get_payload()[1]
                    filename_obj = payload["Content-Disposition"]
                    encoded_filename = filename_obj[filename_obj.find("=?UTF-8?"):-1]
                    decoded_filename = str(msg_ts) + "-" + decode_msg_field(encoded_filename)

                    encoded_attachment = payload.get_payload()
                    decoded_attachment_bytes = base64.b64decode(encoded_attachment)

                    with open(f"{TEMP}/{decoded_filename}", "wb") as file:
                        file.write(decoded_attachment_bytes)

            except Exception as ex:
                errors += 1
                logging.error(msg="[ERROR DECODING EMAIL]", exc_info=ex)
                if errors > 5:
                    raise ex

    def get_start_xl_date(filename):
        df = pd.read_excel(f"data/temp/{filename}", sheet_name=0, header=0)
        date64 = df.iloc[0, 0]
        start_date = pd.Timestamp(date64).to_pydatetime().date()
        return start_date

    def get_loaded_timestamps():
        with SchedulesSession.begin() as session:
            return [i[0] for i in session.query(ORMSchedule.timestamp).all()]

    def handle_temp_files():
        filenames = os.listdir(TEMP)
        for filename in filenames:
            start_date = get_start_xl_date(filename)

            msg_timestamp = int(filename.split("-")[0])

            os.rename(f"{TEMP}/{filename}", f"{TEMP}/{msg_timestamp}.xlsx")
            os.replace(f"{TEMP}/{msg_timestamp}.xlsx", f"data/schedules/{msg_timestamp}.xlsx")

            with SchedulesSession.begin() as session:
                session.add(ORMSchedule(start_date=start_date, timestamp=msg_timestamp))

    now = datetime.now().astimezone(bot.TZ)
    loaded_timestamps = get_loaded_timestamps()

    if not os.path.exists(TEMP):
        os.makedirs(TEMP, exist_ok=True)
    await download_files_to_temp()
    handle_temp_files()


async def checking_schedule():
    await download_from_email()
    actual_dates_and_timestamps = ORMSchedule.get_actual_dates_and_timestamps()
    bot.schedule = Schedule(*actual_dates_and_timestamps)


if __name__ == '__main__':
    asyncio.run(download_from_email())
