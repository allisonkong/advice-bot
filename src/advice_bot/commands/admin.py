from absl import flags
from absl import logging
import datetime
import discord
import socket
import uuid

from advice_bot.commands.common import Command, CommandResult, CommandStatus
from advice_bot import params
from advice_bot.proto import params_pb2
from advice_bot.util import discord_util

FLAGS = flags.FLAGS

# Initialized at import time.
_HOSTNAME: str = None
_INSTANCE_ID: str = None
_INSTANCE_START_TIME: str = None


def _Initialize():
    global _HOSTNAME
    global _INSTANCE_ID
    global _INSTANCE_START_TIME

    _HOSTNAME = socket.gethostname()
    _INSTANCE_ID = str(uuid.uuid4())
    _INSTANCE_START_TIME = datetime.datetime.now(
        datetime.UTC).isoformat(sep=" ")


class AdminCommand(Command):

    def Usage(self) -> CommandResult:
        return CommandResult(
            CommandStatus.OK, """
Usage:
  `!admin list-instances`
  `!admin kill <instance_id>`
""")

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        if not discord_util.IsAdmin(message.author):
            return CommandResult(CommandStatus.PERMISSION_DENIED,
                                 "You are not authorized to use this command.")

        if len(argv) == 1:
            return self.Usage()

        if argv[1] == "list-instances":
            # All instances will report their self details.
            response = (f"Advice Bot instance details:" +
                        f"\nEnv: `{FLAGS.env}`" + f"\nID: `{_INSTANCE_ID}`" +
                        f"\nHostname: `{_HOSTNAME}`" +
                        f"\nStart time: `{_INSTANCE_START_TIME}`")
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
