from absl import flags
from absl import logging
import asyncio
import discord
import re
import shlex
import time

from advice_bot.commands.common import Command, CommandResult, CommandStatus
from advice_bot.commands import admin, monthly_giveaway
from advice_bot import params
from advice_bot.proto import params_pb2
from advice_bot.util import discord_util

FLAGS = flags.FLAGS

_COMMAND_PREFIX = "!"
_COMMAND_REGEX = re.compile(_COMMAND_PREFIX + r'(\w+)\b.*')
_COMMAND_ALIASES = {
    "admin": params_pb2.Command.ADMIN_COMMAND,
    "help": params_pb2.Command.HELP_COMMAND,
    "roll": params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND,
    "participate": params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND,
}
_COMMAND_REGISTRY = None
_COMMAND_DESCRIPTIONS = {
    params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND:
        "`!roll`: Participate in the monthly giveaway. May the odds be ever in your favor :slight_smile:\n* `!participate` may be used as an alias for `!roll`",
    params_pb2.Command.HELP_COMMAND:
        "`!help`: Prints a list of available commands.",
}
_MAX_MESSAGE_LENGTH = 255


def _InitializeRegistry():
    global _COMMAND_REGISTRY
    _COMMAND_REGISTRY = {
        params_pb2.Command.ADMIN_COMMAND:
            admin.AdminCommand(),
        params_pb2.Command.HELP_COMMAND:
            HelpCommand(),
        params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND:
            monthly_giveaway.MonthlyGiveawayCommand(),
    }


def _IsCommandEnabled(command_enum: params_pb2.Command,
                      message: discord.Message):
    """Check if the command was enabled for the given channel."""

    # !help is special.
    if command_enum == params_pb2.Command.HELP_COMMAND:
        return _IsChannelWatched(message)

    if message.guild is None:
        return False
    guild_id = message.guild.id
    server_config_map = params.ServerConfigMap()
    if guild_id not in server_config_map:
        return False
    for command_config in server_config_map[guild_id].commands:
        # Expect low N so direct iteration should be faster + simpler than
        # making a set.
        if command_config.command != command_enum:
            continue
        if command_config.channels.all_channels:
            return True
        for channel_id in command_config.channels.specific_channels:
            if channel_id == message.channel.id:
                return True
    return False


def _IsChannelWatched(message: discord.Message):
    """Check if the message was sent in a channel that the bot is supposed
    to watch.

    This slightly differs from _IsCommandEnabled() because this is for deciding
    if we should respond to an invalid command, while _IsCommandEnabled() is
    for valid commands.
    """
    if message.guild is None:
        return False
    guild_id = message.guild.id
    server_config_map = params.ServerConfigMap()
    if guild_id not in server_config_map:
        return False
    for command_config in server_config_map[guild_id].commands:
        if command_config.channels.all_channels:
            return True
        for channel_id in command_config.channels.specific_channels:
            if channel_id == message.channel.id:
                return True
    return False


class HelpCommand(Command):

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        help_msg = self.GetHelpMsg(message)
        return CommandResult(CommandStatus.OK, help_msg)

    def GetHelpMsg(self, message: discord.Message):
        # List of commands available in the current channel.
        available_commands = []
        for command_enum in sorted(_COMMAND_DESCRIPTIONS):
            if _IsCommandEnabled(command_enum, message):
                available_commands.append(command_enum)

        if len(available_commands) == 0:
            return ""

        help_msg = "Available commands in this channel:"
        for command_enum in available_commands:
            help_msg += f"\n* {_COMMAND_DESCRIPTIONS[command_enum]}"
        return help_msg


class AdviceBot(discord.Client):

    @classmethod
    def CreateInstance(cls):
        intents = discord.Intents.default()
        intents.message_content = True

        application_id = params.Params().discord_params.discord_application_id

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

    async def SendResponse(self, message: discord.Message, response: str):
        if not response:
            return
        if FLAGS.env != "prod":
            response = f"[{FLAGS.env}]\n{response}"
        await message.channel.send(response)

    async def ProcessCommand(self, command: str, message: discord.Message,
                             timestamp_micros: int, argv: list[str]):
        """Handles a parsed command.

        Possible outcomes:
        - PROCESSED: responded to command.
        - REJECTED: responded to command with a rejection message.
        - IGNORED: silently ignore command.
        """

        logging.info(
            f"PROCESSING command {command}:" + f"\nmessage_id: {message.id}" +
            f"\nauthor: {message.author.name} ({message.author.id})" +
            (f"\nserver: {message.guild.name} ({message.guild.id})" if message.
             guild is not None else "") +
            f"\nchannel: {message.channel.name} ({message.channel.id})" +
            f"\ncontent: {message.content}")

        is_watched_channel = _IsChannelWatched(message)

        if command not in _COMMAND_ALIASES:
            if is_watched_channel:
                logging.info(
                    f"REJECTING message {message.id}: unrecognized command")
                await self.SendResponse(
                    message,
                    f"Unrecognized command: {_COMMAND_PREFIX}{command}")
            else:
                logging.info(
                    f"IGNORING message {message.id}: unrecognized command")
            return

        command_enum = _COMMAND_ALIASES[command]

        if not _IsCommandEnabled(command_enum, message):
            if is_watched_channel:
                logging.info(f"REJECTING message {message.id}: not enabled")
                await self.SendResponse(
                    message,
                    f"You cannot use {_COMMAND_PREFIX}{command} in this channel."
                )
            else:
                logging.info(f"IGNORING message {message.id}: not enabled")
            return

        if len(message.content) > _MAX_MESSAGE_LENGTH:
            logging.info(f"REJECTING message {message.id}: too long")
            await self.SendResponse(
                message, "Message rejected: too long (max 255 chars)")
            return

        result: CommandResult = _COMMAND_REGISTRY[command_enum].Execute(
            message, timestamp_micros, argv)

        discord_util.LogCommand(message, timestamp_micros, result)
        logging.info(f"PROCESSED message {message.id}: {result.response}")
        await self.SendResponse(message, result.response)


_InitializeRegistry()
