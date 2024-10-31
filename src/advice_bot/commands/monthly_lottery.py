from absl import logging
import datetime
import discord
import enum
import random

from advice_bot.commands.common import Command, CommandResult, CommandStatus
from advice_bot.database import storage
from advice_bot.util import discord_util, drop_table

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
        _LAST_PARTICIPATION_CACHE[
            discord_user_id] = row.last_participation_micros
        return _LAST_PARTICIPATION_CACHE[discord_user_id]
    finally:
        cursor.close()
        cnx.close()


def _UpdateLastParticipationMicros(discord_user: discord.Member |
                                   discord.abc.User, timestamp_micros: int):
    # Invalidate cache.
    _LAST_PARTICIPATION_CACHE = {}
    try:
        del _LAST_PARTICIPATION_CACHE[discord_user.id]
    except Exception:
        pass

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


def _GetAlreadyParticipatedResponse(discord_user: discord.Member |
                                    discord.abc.User, timestamp_micros: int):
    suffix = "You have already participated in this month's lottery."

    choice = random.randint(1, 12)
    if choice == 1:
        # 2001
        return f"I'm sorry {discord_user.mention}, I'm afraid I can't do that.\n\n({suffix})"
    elif choice == 2:
        # Matrix
        return f"Do not try and bend the spoon. That's impossible. Instead... only try to realize the truth.\n\nWhat truth?\n\nThat {suffix.lower()}"
    elif choice == 3:
        # (not a quote)
        return f"Beep beep boop?\n\n({suffix})"
    elif choice == 4:
        # Wizard of Oz
        return f"Toto, I have a feeling that {suffix.lower()}"
    elif choice == 5:
        # War Games
        f"A strange game. The only winning move is not to play.\n\n({suffix})"
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
        return f"It's been ~~84 years~~ {days_str}.\n\n({suffix})"
    elif choice == 7:
        # LOTR
        return f"We've had one, yes. What about second lottery roll?\n\n({suffix})"
    elif choice == 8:
        # Star wars
        return f"How can you do this? This is outrageous! It's unfair!\n\n({suffix})"
    elif choice == 9:
        # Mean girls
        return f"{discord_user.mention}, stop trying to make fetch happen. It's not going to happen.\n\n({suffix})"
    elif choice == 10:
        # Princess Bride
        return f"Hello. My name is Inigo Montoya. You have already participated in this month's lottery. Prepare to die."
    elif choice == 11 and random.random() < 0.10:
        # Barbie (this one's special so keep it rare)
        return f"It is literally impossible to be a woman. You are so beautiful and so smart, and it kills me that you don't think you're good enough. Like, we have to always be extraordinary, but somehow we're always doing it wrong. You have to be thin, but not too thin. And you can never say you want to be thin. You have to say you want to be healthy, but also you have to be thin. You have to have money, but you can't ask for money because that's crass. You have to be a boss, but you can't be mean. You have to lead, but you can't squash other people's ideas. You're supposed to love being a mother but don't talk about your kids all the damn time. You have to be a career woman, but also always be looking out for other people. You have to answer for men's bad behavior, which is insane, but if you point that out, you're accused of complaining. You're supposed to stay pretty for men, but not so pretty that you tempt them too much or that you threaten other women because you're supposed to be a part of the sisterhood. But always stand out and always be grateful. But never forget that the system is rigged. So find a way to acknowledge that but also always be grateful. You have to never get old, never be rude, never show off, never be selfish, never fall down, never fail, never show fear, never get out of line. It's too hard! It's too contradictory and nobody gives you a medal or says thank you! And it turns out in fact that not only are you doing everything wrong, but also everything is your fault. I'm just so tired of watching myself and every single other woman tie herself into knots so that people will like us. And if all of that is also true for a doll just representing women, then I don't even know.\n\n({suffix})"
    elif choice == 12:
        # Avatar the Last Airbender
        return f"It's time for you to look inward, and start asking yourself the big questions. Who are you? And have you already participated in the lottery this month?\n\n(Yes, yes you have.)"
    else:
        return f"I'm sorry {discord_user.mention}, I'm afraid I can't do that.\n\n({suffix})"


class Prize(enum.IntEnum):
    NO_PRIZE = 0
    GOODYBAG = 1
    CASH_2M = 2
    CUSTOM_RANK = 3
    CUSTOM_RANK_PLUS = 4


_PRIZE_TABLE = drop_table.DropTable([
    (Prize.NO_PRIZE, 0.9375),
    (drop_table.DropTable([
        (Prize.GOODYBAG, 0.3),
        (Prize.CASH_2M, 0.3),
        (Prize.CUSTOM_RANK, 0.3),
        (Prize.CUSTOM_RANK_PLUS, 0.1),
    ]), 0.0625),
])

_ROLLS = 4
_EVIL_KERMIT = "<:evil_Kermit:626526532256661524>"


def _Participate():
    prizes = []
    for i in range(_ROLLS):
        prizes.append(_PRIZE_TABLE.Roll())
    return prizes


class MonthlyLotteryCommand(Command):

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        if not _IsEligible(message.author, timestamp_micros, argv):
            return CommandResult(
                CommandStatus.PERMISSION_DENIED,
                _GetAlreadyParticipatedResponse(message.author,
                                                timestamp_micros))

        prizes = _Participate()
        logging.info(prizes)

        today_str = _DateFromMicros(timestamp_micros).strftime("%B %Y")
        result_message = f"{message.author.mention} is participating in the lottery for {today_str}!\n\n"
        for i in range(len(prizes)):
            prize = prizes[i]
            result_message += f"**Roll #{i + 1}**: "
            if prize == Prize.NO_PRIZE:
                result_message += "Sorry, better luck next time."
            elif prize == Prize.GOODYBAG:
                result_message += "Congratulations, you win a goodybag draw!"
            elif prize == Prize.CASH_2M:
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
