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
            return self.SkillingCompetitionDiceRoll(message)

        if len(argv) != 2:
            return _USAGE

        match = _BOUNDS_RE.fullmatch(argv[1])
        if match is None:
            return _USAGE
        roll_min = int(match.group(1))
        roll_max = int(match.group(2))

        if roll_min > roll_max:
            return "You've gotta ask yourself one question: \"Do I feel lucky?\". Well do ya, punk?"

        roll = random.SystemRandom().randint(roll_min, roll_max)
        return f"{message.author.mention} is rolling [{roll_min}-{roll_max}] and gets: **{roll}**"

    def SkillingCompetitionDiceRoll(self, message):
        TASKS = {
            1: "50k Mastering Mixology Resin",
            2: "75 Giants Foundry Swords",
            3: "25k Buckets of Sand",
            4: "2 Hespori KC",
            5: "500 Ape Atoll laps",
            6: "350 Herbiboar KC",
            7: "Lucky genie! Pick any other task",
            8: "50 Guardians of the Rift KC",
            9: "50 Slayer tasks",
            10: "50 Tempoross KC",
            11: "80 Hunter rumours",
            12: "250 Mahogany Homes contracts",
            13: "3M xp in any 'buyable' skill",
            14: "400k Agility xp",
            15: "400k Mining xp",
            16: "300k Slayer xp",
            17: "1M Hunter xp",
            18: "1.5M Thieving xp",
            19: "600k Woodcutting xp",
            20: "400k Runecrafting xp",
        }

        article = {
            1: "a",
            2: "a",
            3: "a",
            4: "a",
            5: "a",
            6: "a",
            7: "a",
            8: "an",
            9: "a",
            10: "a",
            11: "an",
            12: "a",
            13: "a",
            14: "a",
            15: "a",
            16: "a",
            17: "a",
            18: "an",
            19: "a",
            20: "a",
        }

        roll = random.SystemRandom().randint(1, 20)
        chosen_task = TASKS[roll]
        return f"{message.author.mention} rolls {article[roll]} **{roll}**. Your task is: {chosen_task}.\n\nPlease check the [spreadsheet](https://docs.google.com/spreadsheets/d/1CQEidoPPE3YnQxOCR48zM2wW0zaaeA7bqdnbc0xw3lA/edit?gid=1727437871#gid=1727437871) for detailed task and screenshot requirements."
