"""Supplemental canonical move-intent serialization and validation contract."""

import pytest

from model.game.move import Move


def test_data_only_move_intent_round_trip_preserves_capture_landings_and_promotion():
    intent = Move.from_json(
        {
            "start": [5, 2],
            "hops": [[3, 4], [1, 6]],
            "promotion": "king",
        }
    )
    assert intent.start_pos == (5, 2)
    assert intent.end_pos == (1, 6)
    assert intent.hops == ((3, 4), (1, 6))
    assert intent.promotion == "king"
    assert Move.from_json(intent.to_json()) == intent
    assert {intent: "accepted"}[Move.from_json(intent.to_json())] == "accepted"
    assert intent.to_json()["hops"] == [[3, 4], [1, 6]]


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"start": [1, 2], "hops": [[2, 3]]},
        {"start": [1, 2], "hops": [], "promotion": None},
        {"start": [1, 2], "hops": [[1, 2]], "promotion": None},
        {"start": [True, 2], "hops": [[2, 3]], "promotion": None},
        {"start": [1, 2], "hops": [[257, 3]], "promotion": None},
        {"start": [1, 2], "hops": [[2, 3]], "promotion": ""},
        {"start": [1, 2], "hops": [[2, 3]], "promotion": None, "code": "exec"},
    ],
)
def test_move_intent_rejects_untrusted_or_ambiguous_json(bad):
    with pytest.raises(ValueError):
        Move.from_json(bad)


def test_legacy_move_fields_do_not_leak_into_authoritative_action_intent():
    move = Move((3, 3), (4, 3), move_type="normal")
    assert move.to_json() == {
        "start": [3, 3],
        "hops": [[4, 3]],
        "promotion": None,
    }
