from commands.outcome import Command, CommandResult, CommandStatus
from commands import monthly_lotto

_PREFIX = "!"

_REGISTRY: map[str, Command] = {
    "lotto": monthly_lotto.MonthlyLottoCommand,
}


def DispatchCommand(message):
    # TODO
    raise NotImplementedError
