from absl import flags
from absl import logging
import datetime
import discord
import time
import socket
import uuid
from zoneinfo import ZoneInfo

from advice_bot.commands.common import Command, CommandResult, CommandStatus
from advice_bot import params
from advice_bot.proto import params_pb2
from advice_bot.util import discord_util

FLAGS = flags.FLAGS

# Initialized at import time.
_HOSTNAME: str = None
_INSTANCE_ID: str = None
_INSTANCE_START_MICROS: int = None


def _Initialize():
    global _HOSTNAME
    global _INSTANCE_ID
    global _INSTANCE_START_MICROS

    _HOSTNAME = socket.gethostname()
    _INSTANCE_ID = str(uuid.uuid4())
    _INSTANCE_START_MICROS = time.time_ns() // 1000
    _INSTANCE_START_TIME = datetime.datetime.now(
        datetime.UTC).isoformat(sep=" ")


class AdminCommand(Command):

    def Usage(self) -> CommandResult:
        return CommandResult(
            CommandStatus.OK, """
Usage:
  `!admin status`
  `!admin kill <instance_id>`
""")

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        if not discord_util.IsAdmin(message.author):
            return CommandResult(
                CommandStatus.PERMISSION_DENIED,
                "You are not authorized to use this command, sorry.")

        if len(argv) == 1:
            return self.Usage()

        if argv[1] == "status":
            start_dt = datetime.datetime.fromtimestamp(
                _INSTANCE_START_MICROS / 1e6, datetime.UTC)
            now_dt = datetime.datetime.now(datetime.UTC)

            local_tz = ZoneInfo("America/Los_Angeles")
            local_tz_name = "PST" if local_tz.dst(now_dt) is None else "PDT"

            start_time_utc = start_dt.isoformat(sep=" ")
            start_time_pt = start_dt.astimezone(local_tz).isoformat(sep=" ")

            uptime = now_dt - start_dt
            uptime_days = uptime.days
            s = uptime.seconds
            uptime_hours = s // 3600
            s %= 3600
            uptime_minutes = s // 60
            s %= 60
            uptime_seconds = s

            # All instances will report their self details.
            response = f"""Instance details:
```
Env: {FLAGS.env}
ID: {_INSTANCE_ID}
Hostname: {_HOSTNAME}
Start time (UTC): {start_time_utc}
Start time ({local_tz_name}): {start_time_pt}
Uptime: {uptime_days} day(s) {uptime_hours} hour(s) {uptime_minutes} min(s) {uptime_seconds} sec(s)
```
"""
            return CommandResult(CommandStatus.OK, response)
        elif argv[1] == "kill":
            if len(argv) != 3:
                return self.Usage()

            if _INSTANCE_ID == argv[2]:
                logging.fatal("ENDING PROCESS: requested by admin")

            return CommandResult(CommandStatus.OK, "")
        else:
            return self.Usage()


_Initialize()
