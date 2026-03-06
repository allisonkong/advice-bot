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
            1: "25k Mastering Mixology resin",
            2: "40 Giants Foundry swords",
            3: "15k buckets of sand",
            4: "100 Gnome deliveries",
            5: "250 Ape Atoll laps",
            6: "150 Herbiboar KC",
            7: "Genie - lucky! Pick any task",
            8: "25 Guardians of the Rift KC",
            9: "50 Slayer tasks",
            10: "200 Tempoross reward permits",
            11: "200 Port tasks",
            12: "50 Hunter rumours",
            13: "125 Mahogany Homes contracts",
            14: "1.5m XP in a single 'buyable' skill",
            15: "200k Agility XP",
            16: "200k Mining XP",
            17: "150k Slayer XP",
            18: "500k Hunter XP",
            19: "750k Thieving XP",
            20: "300k Woodcutting XP",
            21: "200k Runecrafting XP",
            22: "500k Sailing XP",
            23: "Guthix's Rest - task complete! Rest and roll again in 4 hours",
            24: "Guthix's Balance - reroll and **double** the amount needed to complete task",
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
            21: "a",
            22: "a",
            23: "a",
            24: "a",
        }

        roll = random.SystemRandom().randint(1, 24)
        chosen_task = TASKS[roll]
        return f"{message.author.mention} rolls {article[roll]} **{roll}**. Your task is: {chosen_task}.\n\nPlease check the [spreadsheet](https://docs.google.com/spreadsheets/d/1h0O_IUxgzPokzMMu5UwHQQyd_be0zTFI-97-izvJsek/edit?gid=1727437871#gid=1727437871) for detailed task and screenshot requirements."
