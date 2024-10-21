from commands.common import Command, CommandStatus, CommandOutcome
from database import storage

import random
import datetime


def _GetLastParticipationMicros(discord_user_id: int) -> int:
    cnx = storage.Connect()
    cursor = cnx.cursor(named_tuple=True)
    try:
        query = """
    SELECT last_participation_micros
    FROM monthly_lotto
    WHERE discord_user_id = %s
    """
        cursor.execute(query, (discord_user_id,))
        results = cursor.fetchall()
        if len(results) == 0:
            return None
        row = results[0]
        return row.last_participation_micros
    finally:
        cursor.close()
        cnx.close()


def _IsEligible(discord_user_id: int) -> bool:
    last_micros = _GetLastParticipationMicros(discord_user_id)
    if last_participation_micros is None:
        return True

    last_s = last_participation_micros / 1e6
    last_dt = datetime.datetime.fromtimestamp(last_s, datetime.UTC)
    now_dt = datetime.datetime.now(datetime.UTC)
    start_of_month = now_dt.date().replace(day=1)
    return last_dt < start_of_month


class MonthlyLottoCommand(Command):

    def Execute(self, message: discord.Message, timestamp_micros: int,
                args: list[str]) -> CommandResult:
        discord_user_id = message.author.id
        if not _IsEligible(discord_user_id):
            return CommandResult(
                CommandStatus.PERMISSION_DENIED,
                "I'm sorry @{}, I'm afraid I can't do that.".format(
                    discord_user_id))
        return CommandResult(CommandStatus.OK, "Wooooo!")
