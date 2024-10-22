import discord
import enum


class CommandStatus(enum.IntEnum):
    # Based on absl::Status.
    OK = 0
    INVALID_ARGUMENT = 3
    NOT_FOUND = 5
    PERMISSION_DENIED = 7
    INTERNAL = 13


class CommandResult():

    def __init__(self, status: CommandStatus, message: str):
        self.status = status
        self.message = message


class Command():

    def Execute(self, message: discord.Message, timestamp_micros: int,
                argv: list[str]) -> CommandResult:
        raise NotImplementedError
