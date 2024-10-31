from absl import logging
import random
import typing


class DropTable():
    """Implements a drop table.

    Members:
        outcomes: list of (outcome, probability) tuples. If an output value is
        itself an instance of DropTable, we will recurse into that sub-table.
    """

    def __init__(self, outcomes: list[tuple[float, typing.Any]]):
        self.outcomes = outcomes

        # Check sum of probabilities.
        net_probability = 0
        for outcome, p in self.outcomes:
            if p <= 0:
                logging.fatal("Probabilities must be positive.")
            net_probability += p
        epsilon = 1e-9
        if abs(net_probability - 1.0) > epsilon:
            logging.fatal("Probabilities must total 1.")

    def Roll(self, rng=None):
        """Rolls the drop table once.

        The option to use a custom RNG is intended for testing only - otherwise
        uses SystemRandom (/dev/urandom). If a custom RNG is provided, must
        implement random().
        """
        if rng is None:
            rng = random.SystemRandom()

        roll = rng.random()
        for outcome, p in self.outcomes:
            if roll >= p:
                roll -= p
                continue
            # Recurse for sub-table.
            if isinstance(outcome, DropTable):
                return outcome.Roll(rng)
            return outcome
        logging.fatal("Failed to choose outcome - this should never happen.")
