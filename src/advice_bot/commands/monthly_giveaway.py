from absl import logging
import datetime
import discord
import enum
import random

from advice_bot.commands.common import Command, CommandResult, CommandStatus
from advice_bot.database import storage
from advice_bot.util import discord_util
from advice_bot.util.drop_table import DropTable


class Prize(enum.IntEnum):
    # Next ID: 7
    NO_PRIZE = 0
    GOODYBAG = 1
    GP_2M = 2
    GP_5M = 5
    GP_10M = 6
    CUSTOM_RANK = 3
    CUSTOM_RANK_SPECIAL = 4


# yapf: disable
_PRIZE_TABLE = DropTable([
    (0.95, Prize.NO_PRIZE),
    # Prize sub-table
    (0.05, DropTable([
        # Goodybag
        (0.33, Prize.GOODYBAG),
        # Cash
        (0.33, DropTable([
             (0.90, Prize.GP_2M),
             (0.09, Prize.GP_5M),
             (0.01, Prize.GP_10M),
         ])),
        # Custom rank
        (0.34, DropTable([
             (0.90, Prize.CUSTOM_RANK),
             (0.10, Prize.CUSTOM_RANK_SPECIAL),
         ])),
    ])),
])
# yapf: enable

_ROLLS = 4
_EVIL_KERMIT = "<:evil_Kermit:626526532256661524>"

_LAST_PARTICIPATION_CACHE = {}


def _GetLastParticipationMicros(discord_user_id: int) -> int | None:
    global _LAST_PARTICIPATION_CACHE
    if discord_user_id in _LAST_PARTICIPATION_CACHE:
        return _LAST_PARTICIPATION_CACHE[discord_user_id]

    cnx = storage.Connect()
    cursor = cnx.cursor(named_tuple=True)
    try:
        query = """
            SELECT last_participation_micros
            FROM monthly_giveaway
            WHERE discord_user_id = %(discord_user_id)s
        """
        cursor.execute(query, {
            "discord_user_id": discord_user_id,
        })
        results = cursor.fetchall()
        if len(results) == 0:
            return None
        row = results[0]
        _LAST_PARTICIPATION_CACHE[
            discord_user_id] = row.last_participation_micros
        return _LAST_PARTICIPATION_CACHE[discord_user_id]
    finally:
        cursor.close()
        cnx.close()


def _RecordGiveawayOutcome(discord_user: discord.Member | discord.abc.User,
                           timestamp_micros: int, prizes: list[Prize]):
    global _LAST_PARTICIPATION_CACHE
    # Invalidate cache.
    try:
        del _LAST_PARTICIPATION_CACHE[discord_user.id]
    except KeyError:
        pass

    cnx = storage.Connect()
    cnx.start_transaction()
    cursor = cnx.cursor()
    try:
        discord_util.UpdateDiscordUserInTransaction(discord_user, cursor)
        for i in range(len(prizes)):
            query = """
                INSERT INTO monthly_giveaway_rolls
                    (
                        discord_user_id,
                        timestamp_micros,
                        sequence_index,
                        prize
                    )
                VALUES
                    (
                        %(discord_user_id)s,
                        %(timestamp_micros)s,
                        %(sequence_index)s,
                        %(prize)s
                    )
                ON DUPLICATE KEY UPDATE
                    prize = %(prize)s
            """
            cursor.execute(
                query, {
                    "discord_user_id": discord_user.id,
                    "timestamp_micros": timestamp_micros,
                    "sequence_index": i,
                    "prize": prizes[i],
                })
        cnx.commit()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cursor.close()
        cnx.close()


def _DateFromMicros(timestamp_micros: int):
    timestamp_s = timestamp_micros / 1e6
    return datetime.datetime.fromtimestamp(timestamp_s, datetime.UTC).date()


def _IsEligible(discord_user: discord.Member | discord.abc.User,
                timestamp_micros: int, argv: list[str]) -> bool:
    # For ease of testing.
    if discord_util.IsAdmin(discord_user) and ("-f" in argv or
                                               "--force" in argv):
        return True

    last_participation_micros = _GetLastParticipationMicros(discord_user.id)
    if last_participation_micros is None:
        return True

    last_date = _DateFromMicros(last_participation_micros)
    now_date = _DateFromMicros(timestamp_micros)
    start_of_month = now_date.replace(day=1)
    return last_date < start_of_month


_NUM_ALREADY_PARTICIPATED_RESPONSES = 11


def _GetAlreadyParticipatedResponse(discord_user: discord.Member |
                                    discord.abc.User,
                                    timestamp_micros: int,
                                    choice=None):
    suffix = "You have already participated in this month's giveaway"

    if choice is None:
        choice = random.randint(1, _NUM_ALREADY_PARTICIPATED_RESPONSES)

    if choice == 1:
        # 2001
        return f"I'm sorry {discord_user.mention}, I'm afraid I can't do that.\n\n({suffix}.)"
    elif choice == 2:
        # Matrix
        return f"Do not try and bend the spoon. That's impossible. Instead... only try to realize the truth.\n\nWhat truth?\n\nThat {suffix.lower()} {discord_user.mention}."
    elif choice == 3:
        # (not a quote)
        return f"Beep beep boop?\n\n({suffix} {discord_user.mention}.)"
    elif choice == 4:
        # Wizard of Oz
        return f"Toto, I've a feeling that {discord_user.mention} has already participated in this month's giveaway."
    elif choice == 5:
        # War Games
        return f"A strange game. The only winning move is not to play.\n\n({suffix} {discord_user.mention}.)"
    elif choice == 6:
        # Titanic
        last_participation_micros = _GetLastParticipationMicros(discord_user.id)
        if last_participation_micros is None:
            logging.error(
                "Last participation should be set if producing an error message."
            )
            last_participation_micros = 0
        last_date = _DateFromMicros(last_participation_micros)
        now_date = _DateFromMicros(timestamp_micros)
        days = (now_date - last_date).days
        days_str = "{} {}".format(days, "days" if days != 1 else "day")
        return f"It's been ~~84 years~~ {days_str}.\n\n({suffix} {discord_user.mention}.)"
    elif choice == 7:
        # LOTR
        return f"We've had one, yes. What about second dice roll?\n\n({suffix} {discord_user.mention})"
    elif choice == 8:
        # Star wars
        return f"How can you do this? This is outrageous! It's unfair!\n\n({suffix} {discord_user.mention}.)"
    elif choice == 9:
        # Mean girls
        return f"{discord_user.mention}, stop trying to make ~~fetch~~ second dice roll happen. It's not going to happen.\n\n({suffix}.)"
    elif choice == 10:
        # Princess Bride
        return f"Hello. My name is Inigo Montoya. You have already participated in this month's giveaway. Prepare to die.\n\n({discord_user.mention})"
    elif choice == 11:
        # Avatar the Last Airbender
        return f"It's time for you to look inward, and start asking yourself the big questions. Who are you? And have you already participated in the giveaway this month?\n\n(Yes, yes you have {discord_user.mention}.)"
    else:
        # Should never happen.
        logging.error(
            "Failed to choose a participation response, falling back to default response."
        )
        return f"I'm sorry {discord_user.mention}, I'm afraid I can't do that.\n\n({suffix}.)"


def _Participate():
    prizes = []
    for i in range(_ROLLS):
        prizes.append(_PRIZE_TABLE.Roll())
    return prizes


class MonthlyGiveawayCommand(Command):

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        # For testing.
        logging.info(argv)
        if discord_util.IsAdmin(message.author) and "--list_responses" in argv:
            full_response = "All possible responses:"
            for i in range(1, _NUM_ALREADY_PARTICIPATED_RESPONSES + 1):
                response = _GetAlreadyParticipatedResponse(message.author,
                                                           timestamp_micros,
                                                           choice=i)
                full_response += f"\n\n{i}: {response}"
            return CommandResult(CommandStatus.OK, full_response)

        if not _IsEligible(message.author, timestamp_micros, argv):
            return CommandResult(
                CommandStatus.PERMISSION_DENIED,
                _GetAlreadyParticipatedResponse(message.author,
                                                timestamp_micros))

        prizes = _Participate()
        logging.info(prizes)

        today_str = _DateFromMicros(timestamp_micros).strftime("%B %Y")
        result_message = f"{message.author.mention} is participating in the giveaway for {today_str}!\n\n"
        for i in range(len(prizes)):
            prize = prizes[i]
            result_message += f"**Roll #{i + 1}**: "
            if prize == Prize.NO_PRIZE:
                result_message += "Sorry, better luck next time."
            elif prize == Prize.GOODYBAG:
                result_message += "Congratulations, you win a goodybag draw!"
            elif prize == Prize.GP_2M:
                result_message += "Congratulations, you win 2M gold. Nice!"
            elif prize == Prize.GP_5M:
                result_message += "Congratulations, you win 5M gold. Very nice!"
            elif prize == Prize.GP_10M:
                result_message += "Congratulations, you win 10M gold. You absolute :spoon:!"
            elif prize == Prize.CUSTOM_RANK:
                result_message += "Congratulations, you win a custom rank for a week!"
            elif prize == Prize.CUSTOM_RANK_SPECIAL:
                result_message += f"Congratulations, you win a super-special custom rank for a week! It's like the normal custom rank, but you may also choose who receives it {_EVIL_KERMIT}\n\n(Note: the recipient is allowed to opt-out, and you can choose yourself.)"
            else:
                logging.error(f"Unexpected prize: {prize}")
                result_message += "Sorry, better luck next time!"

            result_message += "\n\n"

        _RecordGiveawayOutcome(message.author, timestamp_micros, prizes)
        return CommandResult(CommandStatus.OK, result_message)
