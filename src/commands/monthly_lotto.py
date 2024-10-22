import datetime
import discord
import random

from commands.common import Command, CommandResult, CommandStatus
from database import storage
from util import discord_util


def _GetLastParticipationMicros(discord_user_id: int) -> int | None:
    cnx = storage.Connect()
    cursor = cnx.cursor(named_tuple=True)
    try:
        query = """
            SELECT last_participation_micros
            FROM monthly_lotto
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
            INSERT INTO monthly_lotto
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
                timestamp_micros: int) -> bool:
    last_participation_micros = _GetLastParticipationMicros(discord_user.id)
    if last_participation_micros is None:
        return True

    last_date = _DateFromMicros(last_participation_micros)
    now_date = _DateFromMicros(timestamp_micros)
    start_of_month = now_date.replace(day=1)
    return last_date < start_of_month


class MonthlyLottoCommand(Command):

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        if not _IsEligible(message.author, timestamp_micros):
            return CommandResult(
                CommandStatus.PERMISSION_DENIED,
                f"I'm sorry {message.author.mention}, I'm afraid I can't do that."
            )

        _UpdateLastParticipationMicros(message.author, timestamp_micros)
        return CommandResult(CommandStatus.OK, "Wooooo!")
