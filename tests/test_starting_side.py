"""FR-10/54/63: configured starting color owns the first legal turn and clock."""

import pytest

from engine.model.game.configuration import ConfigurationError, validate_definition
from engine.model.game.manager import GameManager, TransitionError
from engine.model.game.move import Move
from test_special_actions import config, place


def configuration():
    return config(
        [place("sentinel", "white", (0, 0)), place("sentinel", "black", (4, 0))], rows=5, columns=7
    )


@pytest.mark.parametrize(
    "starting_side,actor,row,clock", [(-1, "bob", 4, "-1"), (1, "alice", 0, "1")]
)
def test_configured_first_side_controls_moves_clock_and_reconstruction(
    starting_side, actor, row, clock
):
    data = configuration()
    data["starting_side"] = starting_side
    session = GameManager(validate_definition(data), "first", ("alice", "bob"), 0)
    before = session.get_state()
    assert before["active_side"] == starting_side
    legal = session.get_valid_moves()
    assert Move((row, 0), (row, 1)) in legal
    assert all(move.start_pos == (row, 0) for move in legal)
    wrong_actor = "alice" if actor == "bob" else "bob"
    with pytest.raises(TransitionError):
        session.submit(wrong_actor, 0, "wrong", Move((row, 0), (row, 1)), 7)
    assert session.get_state() == before
    session.submit(actor, 0, "first", Move((row, 0), (row, 1)), 7)
    after = session.get_state()
    assert after["active_side"] == -starting_side
    assert after["clocks"]["remaining_ms"][clock] == 600993
    assert after["clocks"]["remaining_ms"][str(-starting_side)] == 600000
    assert GameManager.from_snapshot(after).get_state() == after


def test_missing_default_starting_side_preserves_pinned_configuration_and_replay():
    session = GameManager(validate_definition(configuration()), "first", ("alice", "bob"), 0)
    assert session.get_state()["active_side"] == 1
    assert "starting_side" not in session.get_state()["config"]
    session.submit("alice", 0, "first", Move((0, 0), (0, 1)), 1)
    after = session.get_state()
    assert GameManager.from_snapshot(after).get_state() == after


@pytest.mark.parametrize("value", [True, False, 0, 2, -2, "black", None])
def test_invalid_starting_side_cannot_create_an_authoritative_session(value):
    data = configuration()
    data["starting_side"] = value
    with pytest.raises(ConfigurationError):
        validate_definition(data)
