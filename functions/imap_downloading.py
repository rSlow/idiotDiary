import base64
import email
import logging
import os
import quopri
import re
from datetime import datetime as dt
from io import BytesIO

from aioimaplib import aioimaplib

import constants
from orm.schedules import File

HOST = os.getenv("IMAP_HOST")
LOGIN = os.getenv("IMAP_LOGIN")
PASSWORD = os.getenv("IMAP_PASSWORD")


class IMAPDownloader:
    def __init__(self, host):
        self.host = host
        self.client = aioimaplib.IMAP4_SSL(host=self.host, timeout=30)

    @staticmethod
    def get_payload_bytes_io(message):
        payload = message.get_payload()[1]
        encoded_attachment = payload.get_payload()
        decoded_attachment_bytes = base64.b64decode(encoded_attachment)
        return BytesIO(decoded_attachment_bytes)

    @staticmethod
    def decode_message_field(string: str, replace=True):
        pattern = re.compile(r"[=?]\S*[?]\w[?]\S+[?=]")

        try:
            while match := re.search(pattern, string):
                x, y = match.span()
                match_data = string[x:y][2:-2]
                encoding_last, encoding_first, data = match_data.split("?")
                if encoding_first.upper() == "B":
                    decoded_data = base64.b64decode(data).decode(encoding_last)
                    string = string.replace(string[x:y], decoded_data)
                elif encoding_first.upper() == "Q":
                    decoded_data = quopri.decodestring(data).decode(encoding_last)
                    string = string.replace(string[x:y], decoded_data)
        except ValueError:
            return string

        if replace:
            string = string.replace("\r", "").replace("\n", "").replace("\t", "")
        return string

    async def authorize(self, login=None, password=None):
        await self.client.wait_hello_from_server()
        await self.client.login(
            user=login or os.getenv("IMAP_LOGIN"),
            password=password or os.getenv("IMAP_PASSWORD")
        )

    async def get_messages_list(self):
        since_date = f"{dt.now().astimezone(constants.TIMEZONE):%d-%b-%Y}"
        await self.client.select("INBOX")
        list_mails_bytes = await self.client.uid_search("SINCE", since_date, charset=None)
        list_mails = list_mails_bytes.lines[0].decode().split()
        return list_mails

    async def get_data_from_mail(self, num: str):
        fetch = await self.client.uid("fetch", num, "(RFC822)")
        return fetch

    @staticmethod
    def get_datetime_from_message(message):
        message_date = message["Date"]
        datetime_obj = dt.strptime(
            message_date[message_date.find(",") + 2:],
            "%d %b %Y %H:%M:%S %z"
        ).astimezone(constants.TIMEZONE)
        return datetime_obj

    def get_normal_message(self, lines):
        raw_email = lines[1].decode("utf-8")
        message = email.message_from_string(raw_email)
        decoded_subject = self.decode_message_field(message["Subject"] or "[NO THEME]").strip()
        message.replace_header("Subject", decoded_subject)
        return message

    async def download_cycle(self):
        err = 0
        max_timestamp = await File.get_last_timestamp()

        list_mails = await self.get_messages_list()

        for mail in reversed(list_mails):
            try:
                _, lines = await self.get_data_from_mail(mail)
                message = self.get_normal_message(lines)
                datetime_obj = self.get_datetime_from_message(message)

                if ~message["Subject"].find("Расписание МЧС"):
                    if (msg_timestamp := int(datetime_obj.timestamp())) > max_timestamp:
                        file_io = self.get_payload_bytes_io(message=message)
                        await File.from_file(
                            file_io_or_name=file_io,
                            timestamp=msg_timestamp
                        ).to_db()

                    else:
                        break

            except aioimaplib.CommandTimeout:
                logging.warning(msg=f"[ERROR FETCH] Update is not available.")
                break

            except Exception as ex:
                err += 1
                logging.error(msg="[ERROR DECODING EMAIL]", exc_info=ex)
                if err > 5:
                    raise ex

    @classmethod
    async def update(cls):
        downloader = cls(host=HOST)
        await downloader.authorize(
            login=LOGIN,
            password=PASSWORD,
        )
        await downloader.download_cycle()


if __name__ == '__main__':
    try:
        import asyncio

        asyncio.run(IMAPDownloader.update())
    except ImportError as iex:
        raise iex
