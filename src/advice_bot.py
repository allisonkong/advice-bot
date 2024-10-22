from absl import logging
import asyncio
import discord
import re
import shlex
import time

from commands.common import Command, CommandResult, CommandStatus
from commands import monthly_lotto
import params
from util import discord_util

_COMMAND_PREFIX = "!"
_COMMAND_REGEX = re.compile(_COMMAND_PREFIX + r'(\w+)\b.*')
_COMMAND_REGISTRY = {
    "lotto": monthly_lotto.MonthlyLottoCommand(),
}
_MAX_MESSAGE_LENGTH = 255


class AdviceBot(discord.Client):

    @classmethod
    def CreateInstance(cls):
        intents = discord.Intents.default()
        intents.message_content = True

        application_id = params.GetParams(
        ).discord_params.discord_application_id

        return cls(application_id=application_id, intents=intents)

    async def on_ready(self):
        logging.info("Logged on as {}".format(self.user))

    async def on_message(self, message: discord.Message):
        timestamp_micros: int = time.time_ns() // 1000

        if message.author.id == self.user.id:
            return

        match = _COMMAND_REGEX.fullmatch(message.content)
        if match is None:
            return

        command = match.group(1)
        argv: list[str] = shlex.split(message.content)
        await self.ProcessCommand(command, message, timestamp_micros, argv)

    async def ProcessCommand(self, command: str, message: discord.Message,
                             timestamp_micros: int, argv: list[str]):
        if command not in _COMMAND_REGISTRY:
            await message.channel.send(f"Unrecognized command: {command}")

        if len(message.content) > _MAX_MESSAGE_LENGTH:
            await message.channel.send(
                "Message rejected: too long (max 255 chars)")

        result: CommandResult = _COMMAND_REGISTRY[command].Execute(
            message, timestamp_micros, argv)

        discord_util.LogCommand(message, timestamp_micros, result)
        await message.channel.send(result.message)
