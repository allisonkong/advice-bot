import discord
import mysql.connector

from database import storage
from commands.common import Command, CommandResult, CommandStatus


def UpdateDiscordUserInTransaction(discord_user: discord.Member |
                                   discord.abc.User,
                                   cursor: mysql.connector.cursor.MySQLCursor):
    """Updates the discord_user table.

    Caller is responsible for setting up the transaction.
    """
    query = """
        INSERT INTO discord_users
            (discord_user_id, discord_username)
        VALUES
            (%(discord_user_id)s, %(discord_username)s)
        ON DUPLICATE KEY UPDATE
            discord_username = %(discord_username)s
    """
    cursor.execute(query, {
        "discord_user_id": discord_user.id,
        "discord_username": discord_user.name,
    })


def LogCommand(message: discord.Message, timestamp_micros: int,
               result: CommandResult):
    cnx = storage.Connect()
    cnx.start_transaction()
    cursor = cnx.cursor()
    try:
        UpdateDiscordUserInTransaction(message.author, cursor)
        query = """
            INSERT INTO command_log
                (message_id, timestamp_micros, discord_user_id,
                 command, command_status)
            VALUES
                (%(message_id)s, %(timestamp_micros)s, %(discord_user_id)s,
                 %(command)s, %(command_status)s)
            ON DUPLICATE KEY UPDATE
                timestamp_micros = %(timestamp_micros)s
        """
        cursor.execute(
            query, {
                "message_id": message.id,
                "timestamp_micros": timestamp_micros,
                "discord_user_id": message.author.id,
                "command": message.content,
                "command_status": result.status,
            })
        cnx.commit()
    except Exception:
        cnx.rollback()
        raise
    finally:
        cursor.close()
        cnx.close()
