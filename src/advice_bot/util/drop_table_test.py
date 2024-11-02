from advice_bot.util.drop_table import DropTable


class MockRandom():

    def __init__(self, mock_outcomes: list[float]):
        assert len(mock_outcomes) > 0
        self.mock_outcomes = mock_outcomes
        self.i = 0

    def random(self):
        """Returns the next mock value in the list."""
        assert self.i < len(self.mock_outcomes)
        result = self.mock_outcomes[self.i]
        self.i += 1
        return result


def test_drop_table():
    drop_table = DropTable([
        (0.5, "a"),
        (0.25, "b"),
        (0.125, "c"),
        (0.125,
         DropTable([
             (0.25, "d1"),
             (0.25, "d2"),
             (0.25, "d3"),
             (0.25, "d4"),
         ])),
    ])

    assert drop_table.Roll(MockRandom([0.3])) == "a"
    assert drop_table.Roll(MockRandom([0.6])) == "b"
    assert drop_table.Roll(MockRandom([0.8])) == "c"
    assert drop_table.Roll(MockRandom([0.9, 0.1])) == "d1"
    assert drop_table.Roll(MockRandom([0.9, 0.3])) == "d2"
    assert drop_table.Roll(MockRandom([0.9, 0.6])) == "d3"
    assert drop_table.Roll(MockRandom([0.9, 0.9])) == "d4"
