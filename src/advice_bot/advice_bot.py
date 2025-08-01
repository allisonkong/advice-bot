from absl import flags
from absl import logging
import asyncio
import discord
import re
import shlex
import time

from advice_bot.commands.common import Command, CommandResult, CommandStatus
from advice_bot.commands import admin, diceroll, monthly_giveaway
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
    "giveaway": params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND,
    "gimmegimmegimme": params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND,
    "gimme": params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND,
    "diceroll": params_pb2.Command.DICEROLL_COMMAND,
}
_MAX_MESSAGE_LENGTH = 255
_ENV_FLAG_REGEX = re.compile(r"--env=(\w+)")
_COMMAND_REGISTRY = None


def _InitializeRegistry():
    global _COMMAND_REGISTRY
    _COMMAND_REGISTRY = {
        params_pb2.Command.ADMIN_COMMAND:
            admin.AdminCommand(),
        params_pb2.Command.HELP_COMMAND:
            HelpCommand(),
        params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND:
            monthly_giveaway.MonthlyGiveawayCommand(),
        params_pb2.Command.DICEROLL_COMMAND:
            diceroll.DiceRollCommand(),
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
        help_msg = "Available commands:"
        show_help_msg = False

        # List the commands available in the current channel.
        if _IsCommandEnabled(params_pb2.Command.ADMIN_COMMAND, message):
            help_msg += "\n* `!admin`: Manage bot instance(s)."
            show_help_msg = True
        if _IsCommandEnabled(params_pb2.Command.HELP_COMMAND, message):
            help_msg += "\n* `!help`: List available commands."
            show_help_msg = True
        if _IsCommandEnabled(params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND,
                             message):
            help_msg += "\n* `!roll`, `!participate`, or `!giveaway`: Participate in the monthly giveaway. See pin for details: https://discord.com/channels/480809905138171924/1302165779336396860/1302165889931546644."
            show_help_msg = True

        if not show_help_msg:
            return ""
        return help_msg


_g_last_rickroll_time = None
_g_rickroll_state = 0
_RICKROLL_LINES = [
    "We're no strangers to love",
    "You know the rules and so do I",
    "A full commitment's what I'm thinkin' of",
    "You wouldn't get this from any other guy",
    "I just wanna tell you how I'm feeling",
    "Gotta make you understand",
    "Never gonna give you up, never gonna let you down",
    "Never gonna run around and desert you",
    "Never gonna make you cry, never gonna say goodbye",
    "Never gonna tell a lie and hurt you",
    "We've known each other for so long",
    "Your heart's been aching, but you're too shy to say it",
    "Inside, we both know what's been going on",
    "We know the game and we're gonna play it",
    "And if you ask me how I'm feeling",
    "Don't tell me you're too blind to see",
    "Never gonna give you up, never gonna let you down",
    "Never gonna run around and desert you",
    "Never gonna make you cry, never gonna say goodbye",
    "Never gonna tell a lie and hurt you",
    "Never gonna give you up, never gonna let you down",
    "Never gonna run around and desert you",
    "Never gonna make you cry, never gonna say goodbye",
    "Never gonna tell a lie and hurt you",
    "(Ooh, give you up)",
    "(Ooh, give you up)",
    "(Ooh) never gonna give, never gonna give (give you up)",
    "(Ooh) never gonna give, never gonna give (give you up)",
    "We've known each other for so long",
    "Your heart's been aching, but you're too shy to say it",
    "Inside, we both know what's been going on",
    "We know the game and we're gonna play it",
    "I just wanna tell you how I'm feeling",
    "Gotta make you understand",
    "Never gonna give you up, never gonna let you down",
    "Never gonna run around and desert you",
    "Never gonna make you cry, never gonna say goodbye",
    "Never gonna tell a lie and hurt you",
    "Never gonna give you up, never gonna let you down",
    "Never gonna run around and desert you",
    "Never gonna make you cry, never gonna say goodbye",
    "Never gonna tell a lie and hurt you",
    "Never gonna give you up, never gonna let you down",
    "Never gonna run around and desert you",
    "Never gonna make you cry, never gonna say goodbye",
    "Never gonna tell a lie and hurt you",
]


def MaybeHandleEasterEgg(message: discord.Message):

    def _SpecialModRoll(message):
        return all([
            ("roll" in content or "participate" in content or
             "giveaway" in content or "gimmegimmegimme" in content) and
            ("mod" in content or "special" in content or "admin" in content) and
            (_IsCommandEnabled(params_pb2.Command.MONTHLY_GIVEAWAY_COMMAND,
                               message))
        ])

    def _RickRoll():
        global _g_last_rickroll_time
        global _g_rickroll_state

        if not 0 <= _g_rickroll_state < len(_RICKROLL_LINES):
            _g_rickroll_state = 0

        # Reset state if >1hr since last interaction.
        now = time.time()
        if _g_last_rickroll_time is None or now - _g_last_rickroll_time > 3600:
            _g_rickroll_state = 0
            _g_last_rickroll_time = now
        line = _RICKROLL_LINES[_g_rickroll_state]
        _g_rickroll_state += 1
        return f"🎵 {line} 🎵"

    content = message.content.lower()
    if content.startswith("!make me a sandwich"):
        return "What? Make it yourself."
    elif content.startswith("!sudo make me a sandwich"):
        return "Okay."
    elif content == "!sudo" or content.startswith("!sudo "):
        return f"{message.author.mention} is not in the sudoers file. This incident will be reported."
    elif _SpecialModRoll(message):
        return monthly_giveaway.FunnyModResponse(message)
    elif content == "!ban" or content.startswith("!ban "):
        return f"Instructions unclear. {message.author.mention} is now banned."
    elif content == "!reroll":
        return f"Including results for `!rickroll`. Search only for `!reroll`?\n\n{_RickRoll()}"
    elif content.startswith("!reroll "):
        return f"Haha no."
    elif content.startswith("!rickroll"):
        return _RickRoll()
    return None


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

        command = match.group(1).lower()
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

        easter_egg = MaybeHandleEasterEgg(message)
        if easter_egg is not None:
            logging.info(f"PROCESSED message {message.id} as easter egg.")
            await self.SendResponse(message, easter_egg)
            return

        is_watched_channel = _IsChannelWatched(message)
        if not is_watched_channel:
            logging.info("IGNORING message {message.id}: unexpected channel.")
            return

        if command not in _COMMAND_ALIASES:
            logging.info(
                f"REJECTING message {message.id}: unrecognized command")
            await self.SendResponse(
                message, f"Unrecognized command: {_COMMAND_PREFIX}{command}")
            return

        command_enum = _COMMAND_ALIASES[command]
        # Dirty hack (since they use the same name) that we'll probably never clean up, oh well.
        if command == "roll" and _IsCommandEnabled(
                params_pb2.Command.DICEROLL_COMMAND, message):
            command_enum = params_pb2.Command.DICEROLL_COMMAND

        if not _IsCommandEnabled(command_enum, message):
            logging.info(f"REJECTING message {message.id}: not enabled")
            await self.SendResponse(
                message,
                f"You cannot use {_COMMAND_PREFIX}{command} in this channel.")
            return

        if len(message.content) > _MAX_MESSAGE_LENGTH:
            logging.info(f"REJECTING message {message.id}: too long")
            await self.SendResponse(
                message, "Message rejected: too long (max 255 chars)")
            return

        # If --env=<env> is passed, only instances for that env should respond.
        for arg in argv:
            match = _ENV_FLAG_REGEX.fullmatch(arg)
            if match is None:
                continue
            requested_env = match.group(1)
            if FLAGS.env != requested_env:
                logging.info("IGNORING message {message.id}: wrong env")
                return
            argv.remove(arg)
            # Must stop iteration.
            break

        result: CommandResult = _COMMAND_REGISTRY[command_enum].Execute(
            message, timestamp_micros, argv)

        discord_util.LogCommand(message, timestamp_micros, result)
        logging.info(f"PROCESSED message {message.id}: {result.response}")
        await self.SendResponse(message, result.response)


_InitializeRegistry()
