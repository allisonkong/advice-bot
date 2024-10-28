from absl import logging
import datetime
import discord
import enum
import random

from advice_bot.commands.common import Command, CommandResult, CommandStatus
from advice_bot.database import storage
from advice_bot.util import discord_util


def _GetLastParticipationMicros(discord_user_id: int) -> int | None:
    cnx = storage.Connect()
    cursor = cnx.cursor(named_tuple=True)
    try:
        query = """
            SELECT last_participation_micros
            FROM monthly_lottery
            WHERE discord_user_id = %(discord_user_id)s
        """
        cursor.execute(query, {
            "discord_user_id": discord_user_id,
        })
        results = cursor.fetchall()
        if len(results) == 0:
            return None
        row = results[0]
        return row.last_participation_micros
    finally:
        cursor.close()
        cnx.close()


def _UpdateLastParticipationMicros(discord_user: discord.Member |
                                   discord.abc.User, timestamp_micros: int):
    cnx = storage.Connect()
    cnx.start_transaction()
    cursor = cnx.cursor()
    try:
        discord_util.UpdateDiscordUserInTransaction(discord_user, cursor)
        query = """
            INSERT INTO monthly_lottery
                (discord_user_id, last_participation_micros)
            VALUES
                (%(discord_user_id)s, %(timestamp_micros)s)
            ON DUPLICATE KEY UPDATE
                last_participation_micros = %(timestamp_micros)s
        """
        cursor.execute(
            query, {
                "discord_user_id": discord_user.id,
                "timestamp_micros": timestamp_micros,
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
    allison = 262055165392191488
    if discord_user.id == allison and ("-f" in argv or "--force" in argv):
        return True

    last_participation_micros = _GetLastParticipationMicros(discord_user.id)
    if last_participation_micros is None:
        return True

    last_date = _DateFromMicros(last_participation_micros)
    now_date = _DateFromMicros(timestamp_micros)
    start_of_month = now_date.replace(day=1)
    return last_date < start_of_month


class Prize(enum.IntEnum):
    GOODYBAG = 1
    CASH = 2
    CUSTOM_RANK = 3
    CUSTOM_RANK_PLUS = 4


_ROLLS = 4
_PRIZE_RATE = 0.0625
_PRIZE_TABLE = [
    (Prize.GOODYBAG, 0.3),
    (Prize.CASH, 0.3),
    (Prize.CUSTOM_RANK, 0.3),
    (Prize.CUSTOM_RANK_PLUS, 0.1),
]
_EVIL_KERMIT = "<:evil_Kermit:626526532256661524>"


def Participate():
    prizes = []
    for i in range(_ROLLS):
        roll = random.SystemRandom().random()
        if roll >= _PRIZE_RATE:
            prizes.append(None)
            continue
        prize_roll = random.SystemRandom().random()
        for prize, prize_rate in _PRIZE_TABLE:
            if prize_roll < prize_rate:
                prizes.append(prize)
                break
            prize_roll -= prize_rate
    return prizes


class MonthlyLotteryCommand(Command):

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        if not _IsEligible(message.author, timestamp_micros, argv):
            return CommandResult(
                CommandStatus.PERMISSION_DENIED,
                f"I'm sorry {message.author.mention}, I'm afraid I can't do that.\n\n(You've already participated this month!)"
            )

        prizes = Participate()
        logging.info(prizes)

        today_str = _DateFromMicros(timestamp_micros).strftime("%B %Y")
        result_message = f"{message.author.mention} is participating in the lottery for {today_str}!\n\n"
        for i in range(len(prizes)):
            prize = prizes[i]
            result_message += f"**Roll #{i + 1}**: "
            if prize is None:
                result_message += "Sorry, better luck next time."
            elif prize == Prize.GOODYBAG:
                result_message += "Congratulations, you win a goodybag draw!"
            elif prize == Prize.CASH:
                result_message += "Congratulations, you win 2M gold. Nice!"
            elif prize == Prize.CUSTOM_RANK:
                result_message += "Congratulations, you win a custom rank for a week!"
            elif prize == Prize.CUSTOM_RANK_PLUS:
                result_message += f"Congratulations, you win a super-special custom rank for a week! It's like the normal custom rank, but you may also choose who receives it {_EVIL_KERMIT}\n\n(Note: the recipient is allowed to opt-out, and you can choose yourself.)"
            else:
                logging.warning(f"Unexpected prize: {prize}")
                result_message += "Sorry, better luck next time!"

            result_message += "\n\n"

        _UpdateLastParticipationMicros(message.author, timestamp_micros)
        return CommandResult(CommandStatus.OK, result_message)
