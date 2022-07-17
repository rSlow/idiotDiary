import logging

Logger = logging.getLoggerClass()


class BotLogger(Logger):
    def __init__(self, *args, **kwargs):
        super(BotLogger, self).__init__(name="BotLogger", *args, **kwargs)
        self.level = logging.INFO

    def notification_on(self, username, user_id):
        self.info(f"[NOTIFICATION ON] {username}:{user_id}")

    def notification_off(self, username, user_id):
        self.info(f"[NOTIFICATION OFF] {username}:{user_id}")


logger = BotLogger()
