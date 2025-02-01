from absl import flags
from absl import logging
import datetime
import discord
import enum
import random

from advice_bot.commands.common import Command, CommandResult, CommandStatus
from advice_bot.database import storage
from advice_bot.util import discord_util
from advice_bot.util.drop_table import DropTable

FLAGS = flags.FLAGS


class Prize(enum.IntEnum):
    # Next ID: 7
    NO_PRIZE = 0
    GOODYBAG = 1
    GP_2M = 2
    GP_5M = 5
    GP_10M = 6
    CUSTOM_RANK = 3
    CUSTOM_RANK_PLUSPLUS = 4


# yapf: disable
_PRIZE_TABLE = DropTable([
    (0.95, Prize.NO_PRIZE),
    # Prize sub-table
    (0.05, DropTable([
        # Goodybag
        (0.33, Prize.GOODYBAG),
        # GP prize
        (0.33, DropTable([
             (0.80, Prize.GP_2M),
             (0.18, Prize.GP_5M),
             (0.02, Prize.GP_10M),
         ])),
        # Custom rank
        (0.34, DropTable([
             (0.90, Prize.CUSTOM_RANK),
             (0.10, Prize.CUSTOM_RANK_PLUSPLUS),
         ])),
    ])),
])
# yapf: enable

_ROLLS = 4


# Custom emojis need to be fully qualified. Look them up with \:emoji_name:
class Emojis(enum.StrEnum):
    # Default
    PARTYING_FACE = ":partying_face:"
    TADA = ":tada:"
    SUNGLASSES = ":sunglasses:"
    FACE_WITH_MONOCLE = ":face_with_monocle:"
    # Custom, static
    EVIL_KERMIT = "<:evil_Kermit:626526532256661524>"
    NOOT_LIKE_THIS = "<:nootLikeThis:748245017679888484>"
    ANGRY_SNOOT = "<:angrySnoot:697276982018179102>"
    NOT_LIKE_DUCK = "<:notlikeduck:631902811579219973>"
    # Custom, animated
    DOG_DANCE = "<a:dogdance:628401377508458516>"
    PENGUIN_DANCE = "<a:penguin_dance:760257825737408573>"
    KANKAN = "<a:KanKan:755671122451890237>"
    CRAB_RAVE = "<a:crab_rave:628404069718949892>"
    BLUE_LIGHT = "<a:blue_light:760254835202850839>"
    RED_LIGHT = "<a:red_light:760254836016676894>"


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
                timestamp_micros: int,
                force: bool = False) -> bool:
    # For ease of testing.
    if force:
        return True

    last_participation_micros = _GetLastParticipationMicros(discord_user.id)
    if last_participation_micros is None:
        return True

    last_date = _DateFromMicros(last_participation_micros)
    now_date = _DateFromMicros(timestamp_micros)
    start_of_month = now_date.replace(day=1)
    return last_date < start_of_month


_NUM_ALREADY_PARTICIPATED_RESPONSES = 13


def _GetAlreadyParticipatedResponse(discord_user: discord.Member |
                                    discord.abc.User,
                                    timestamp_micros: int,
                                    choice=None):
    suffix = "You have already participated in this month's giveaway"

    if choice is None:
        choice = random.randint(1, _NUM_ALREADY_PARTICIPATED_RESPONSES)

    if choice == 1:
        # 2001
        return f"I'm sorry {discord_user.mention}, I'm afraid I can't do that.\n\n({suffix})"
    elif choice == 2:
        # Matrix
        return f"Do not try and bend the spoon. That's impossible. Instead... only try to realize the truth.\n\nWhat truth?\n\nThat {suffix.lower()} {discord_user.mention}."
    elif choice == 3:
        # (not a quote)
        return f"Beep beep boop? {Emojis.FACE_WITH_MONOCLE}\n\n({suffix} {discord_user.mention})"
    elif choice == 4:
        # Wizard of Oz
        return f"Toto, I've a feeling that {discord_user.mention} has already participated in this month's giveaway."
    elif choice == 5:
        # War Games
        return f"A strange game. The only winning move is not to play.\n\n({suffix} {discord_user.mention})"
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
        return f"It's been ~~84 years~~ {days_str}.\n\n({suffix} {discord_user.mention})"
    elif choice == 7:
        # LOTR
        return f"We've had one, yes. What about second dice roll?\n\n({suffix} {discord_user.mention})"
    elif choice == 8:
        # LOTR
        return f"Ha ha ha ha ha ha. You have no power here.\n\n({suffix} {discord_user.mention})"
    elif choice == 9:
        # Star wars
        return f"How can you do this? This is outrageous! It's unfair!\n\n({suffix} {discord_user.mention})"
    elif choice == 10:
        # Mean girls
        return f"{discord_user.mention}, stop trying to make ~~fetch~~ second dice roll happen. It's not going to happen.\n\n({suffix})"
    elif choice == 11:
        # Princess Bride
        return f"Hello. My name is Inigo Montoya. You have already participated in this month's giveaway. Prepare to die.\n\n({discord_user.mention})"
    elif choice == 12:
        # Avatar the Last Airbender
        return f"It's time for you to look inward, and start asking yourself the big questions. Who are you? And have you already participated in the giveaway this month?\n\n(Yes, yes you have {discord_user.mention})"
    elif choice == 13:
        # Avatar the Last Airbender
        return f"That's rough buddy.\n\n({suffix} {discord_user.mention})"
    else:
        # Should never happen.
        logging.error(
            "Failed to choose a participation response, falling back to default response."
        )
        return f"I'm sorry {discord_user.mention}, I'm afraid I can't do that.\n\n({suffix})"


def _GetPrizeDescriptions(prizes: list[Prize]):
    num_prizes = sum(1 if prize != Prize.NO_PRIZE else 0 for prize in prizes)

    text = ""
    for i in range(len(prizes)):
        prize = prizes[i]
        text += f"**Roll #{i + 1}**: "
        if prize == Prize.NO_PRIZE:
            text += f"Sorry, better luck next time."
            if i == len(prizes) - 1 and num_prizes == 0:
                text += " " + random.choice([
                    Emojis.NOOT_LIKE_THIS,
                    Emojis.NOT_LIKE_DUCK,
                ])
        elif prize == Prize.GOODYBAG:
            text += f"Congratulations, you win a goodybag draw! {Emojis.PARTYING_FACE}\n\n(Please DM a mod to claim.)"
        elif prize == Prize.GP_2M:
            text += f"Congratulations, you win 2M gold. Nice! {Emojis.TADA}\n\n(Please DM a mod to claim.)"
        elif prize == Prize.GP_5M:
            text += f"Congratulations, you win 5M gold. Very nice! {Emojis.DOG_DANCE}\n\n(Please DM a mod to claim.)"
        elif prize == Prize.GP_10M:
            text += f"Congratulations, you win 10M gold. Incredible! {Emojis.CRAB_RAVE}\n\n(Please DM a mod to claim.)"
        elif prize == Prize.CUSTOM_RANK:
            text += f"Congratulations, you win a custom rank for a week :sunglasses:\n\n(Please DM a deputy owner+ to claim.)"
        elif prize == Prize.CUSTOM_RANK_PLUSPLUS:
            text += f"Congratulations, you win a super-special custom rank for a week! It's just like the normal custom rank, but you also get to choose who receives it {Emojis.EVIL_KERMIT}\n\n(Note: the recipient may opt-out, and you may choose yourself if you wish. Please DM a deputy owner+ to claim.)"
        else:
            logging.error(f"Unexpected prize: {prize}")
            text += "Sorry, better luck next time. {Emojis.NOOT_LIKE_THIS}"
        text += "\n\n"
    return text


def _Participate():
    prizes = []
    for i in range(_ROLLS):
        prizes.append(_PRIZE_TABLE.Roll())
    return prizes


class MonthlyGiveawayCommand(Command):

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        # Handle flags for testing.
        if "--print_responses" in argv:
            if not discord_util.IsAdmin(message.author):
                return CommandResult(
                    CommandStatus.PERMISSION_DENIED,
                    f"I'm sorry {message.author.mention}, I'm afraid I can't do that.\n\n(You are not authorized to use that flag.)"
                )
            # Print all possible rejection responses.
            full_response = "All possible responses:"
            for i in range(1, _NUM_ALREADY_PARTICIPATED_RESPONSES + 1):
                response = _GetAlreadyParticipatedResponse(message.author,
                                                           timestamp_micros,
                                                           choice=i)
                full_response += f"\n\n{i}: {response}"
            return CommandResult(CommandStatus.OK, full_response)
        elif "--print_table" in argv:
            if not discord_util.IsAdmin(message.author):
                return CommandResult(
                    CommandStatus.PERMISSION_DENIED,
                    f"I'm sorry {message.author.mention}, I'm afraid I can't do that.\n\n(You are not authorized to use that flag.)"
                )
            # Print the current prize table with weights.
            return CommandResult(CommandStatus.OK,
                                 f"\n```\n{str(_PRIZE_TABLE)}\n```")
        elif "--print_prizes" in argv:
            if not discord_util.IsAdmin(message.author):
                return CommandResult(
                    CommandStatus.PERMISSION_DENIED,
                    f"I'm sorry {message.author.mention}, I'm afraid I can't do that.\n\n(You are not authorized to use that flag.)"
                )
            # Print the descriptions of every prize.
            prizes = [
                Prize.NO_PRIZE, Prize.GOODYBAG, Prize.GP_2M, Prize.GP_5M,
                Prize.GP_10M, Prize.CUSTOM_RANK, Prize.CUSTOM_RANK_PLUSPLUS
            ]
            return CommandResult(CommandStatus.OK,
                                 _GetPrizeDescriptions(prizes))
        elif "--print_no_prizes" in argv:
            if not discord_util.IsAdmin(message.author):
                return CommandResult(
                    CommandStatus.PERMISSION_DENIED,
                    f"I'm sorry {message.author.mention}, I'm afraid I can't do that.\n\n(You are not authorized to use that flag.)"
                )
            # Print the response if user gets exactly 0 prizes.
            prizes = [
                Prize.NO_PRIZE, Prize.NO_PRIZE, Prize.NO_PRIZE, Prize.NO_PRIZE
            ]
            return CommandResult(CommandStatus.OK,
                                 _GetPrizeDescriptions(prizes))

        # If users want to post good luck messages, that's fine. But catch any
        # flags in case it's me making a typo testing something.
        force = False
        for arg in argv[1:]:
            if arg == "--force":
                if FLAGS.env == "prod" or not discord_util.IsAdmin(
                        message.author):
                    return CommandResult(
                        CommandStatus.PERMISSION_DENIED,
                        f"I'm sorry {message.author.mention}, I'm afraid I can't do that.\n\n(You are not authorized to use that flag.)"
                    )
                force = True
            elif arg.startswith("--"):
                return CommandResult(CommandStatus.INVALID_ARGUMENT,
                                     f"Unrecognized flag: {arg}")
            else:
                pass

        # Main flow: participate in giveaway.

        if not _IsEligible(message.author, timestamp_micros, force):
            return CommandResult(
                CommandStatus.PERMISSION_DENIED,
                _GetAlreadyParticipatedResponse(message.author,
                                                timestamp_micros))

        prizes = _Participate()
        logging.info(prizes)

        today_str = _DateFromMicros(timestamp_micros).strftime("%B %Y")
        result_message = f"{message.author.mention} is participating in the giveaway for {today_str}!\n\n"
        result_message += _GetPrizeDescriptions(prizes)

        _RecordGiveawayOutcome(message.author, timestamp_micros, prizes)
        return CommandResult(CommandStatus.OK, result_message)


def IsMod(user: discord.Member):
    if discord_util.IsAdmin(user):
        return True
    for role in user.roles:
        if role.name.lower() in [
                "mod team", "mod +", "moderator", "officer", "commander",
                "brigadier", "deputy owner", "leader"
        ]:
            return True
    return False


def FunnyModResponse(message: discord.Message):
    """Returns a funny message if a mod tries to do something silly with the giveaway.
    """
    if not IsMod(message.author):
        return f"Hello. My name is Inigo Montoya. You are not authorized to use that command. Prepare to die.\n\n({message.author.mention})"

    NO_POWER = f"Ha ha ha ha ha ha. You have no power here {message.author.mention}."
    MOD_ABUSE = f"{Emojis.BLUE_LIGHT} {Emojis.RED_LIGHT} MOD ABUSE MOD ABUSE {Emojis.BLUE_LIGHT} {Emojis.RED_LIGHT}\n\n({message.author.mention})"
    OVERFLOW = f"""Sure, why not. You're such a good mod, you can have a free roll.

**Roll #1**: Congratulations, you win 1,000,000,000 gold. Incredible!

**Roll #2**: Congratulations, you win 1,000,000,000 gold. Wow!

**Roll #3**: Congratulations, you win 147,483,647 gold. Amazing!

**Roll #4** Congratulations, you win 1 gold. Outstanding!

Total winnings: -2,147,483,648 gold. Please report to the Corrupted Gauntlet immediately to repay your debt {message.author.mention}."""

    response_table = DropTable([
        (0.6, NO_POWER),
        (0.2, MOD_ABUSE),
        (0.2, OVERFLOW),
    ])
    return response_table.Roll()
