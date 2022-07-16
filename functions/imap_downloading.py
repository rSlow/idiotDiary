import asyncio
import base64
import email
import logging
import os
import quopri
import re
from datetime import datetime
from io import BytesIO

import aioimaplib
from orm.schedules import File

import constants


class IMAPDownloader:
    LOGIN = "kursdvf.spb@mail.ru"
    PASSWORD = "Aq12sw23"
    DOMAIN = "imap.mail.ru"

    def __init__(self, host=None):
        self.host = host or os.getenv("IMAP_HOST")
        self.client = aioimaplib.IMAP4_SSL(host=self.host)

    async def authorize(self, login=None, password=None):
        await self.client.wait_hello_from_server()
        await self.client.login(
            user=login or os.getenv("IMAP_LOGIN"),
            password=password or os.getenv("IMAP_PASSWORD")
        )

    def delete_attrs(self, *attrs):
        for attr in attrs:
            if getattr(self, attr):
                delattr(self, attr)

    @staticmethod
    def get_payload_bytes_io(message):
        payload = message.get_payload()[1]
        encoded_attachment = payload.get_payload()
        decoded_attachment_bytes = base64.b64decode(encoded_attachment)
        return BytesIO(decoded_attachment_bytes)

    @staticmethod
    def decode_message_field(string: str, replace=True):
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

    async def get_messages_list(self):
        await self.client.select("INBOX")
        list_mails_bytes = await self.client.uid_search("ALL", charset=None)
        list_mails = list_mails_bytes.lines[0].decode().split()
        return list_mails

    async def get_data_from_mail(self, num: str):
        fetch = await self.client.uid("fetch", num, "(RFC822)")
        return fetch

    @staticmethod
    def get_datetime_from_message(message):
        message_date = message["Date"]
        datetime_obj = datetime.strptime(
            message_date[message_date.find(",") + 2:],
            "%d %b %Y %H:%M:%S %z"
        ).astimezone(constants.TIMEZONE)
        return datetime_obj

    def get_normal_message(self, lines):
        raw_email: bytearray = lines[1]
        message = email.message_from_bytes(raw_email)
        message["Subject"] = self.decode_message_field(message["Subject"] or "").strip()
        return message

    async def get_timestamp_and_file_io(self, message):
        pass

    async def download_cycle(self):
        now = datetime.now().astimezone(constants.TIMEZONE)
        err = 0
        max_timestamp = await File.get_max_timestamp()

        list_mails = await self.get_messages_list()

        for mail in reversed(list_mails):
            try:
                _, lines = await self.get_data_from_mail(mail)
                message = self.get_normal_message(lines)
                datetime_obj = self.get_datetime_from_message(message)

                if (now - datetime_obj).days > 7:  # limit days within today and message day
                    break

                if ~message["Subject"].find("Расписание МЧС"):
                    if int(datetime_obj.timestamp()) > max_timestamp:
                        file_io = self.get_payload_bytes_io(message=message)

                    else:
                        break

            except Exception as ex:
                err += 1
                logging.error(msg="[ERROR DECODING EMAIL]", exc_info=ex)
                if err > 5:
                    raise ex


if __name__ == '__main__':
    asyncio.run()
