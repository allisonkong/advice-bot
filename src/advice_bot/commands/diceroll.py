import discord
import random
import re

from advice_bot.commands.common import Command, CommandResult, CommandStatus
from advice_bot.proto import params_pb2

_BOUNDS_RE = re.compile("(\d+)-(\d+)")
_USAGE = "Usage: `!roll` or `!roll MIN-MAX`."


class DiceRollCommand(Command):

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        return CommandResult(CommandStatus.OK, self.DiceRoll(argv, message))

    def DiceRoll(self, argv: list[str], message: discord.Message):
        """Implements the dice roll command. Returns a string to send."""
        if len(argv) == 1:
            # Default
            roll_min = 1
            roll_max = 20
        elif len(argv) == 2:
            match = _BOUNDS_RE.fullmatch(argv[1])
            if match is None:
                return _USAGE
            roll_min = int(match.group(1))
            roll_max = int(match.group(2))
        else:
            return _USAGE

        if roll_min > roll_max:
            return "You've gotta ask yourself one question: \"Do I feel lucky?\". Well do ya, punk?"

        roll = random.SystemRandom().randint(roll_min, roll_max)
        return f"{message.author.mention} is rolling between {roll_min} and {roll_max} and gets: **{roll}**"
