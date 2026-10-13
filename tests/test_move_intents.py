"""FR-13/FR-65: complete immutable move intents at the consumer boundary."""

from dataclasses import FrozenInstanceError

import pytest

from engine.model.game.move import Move


def test_capture_chain_roundtrip_preserves_order_without_editor_aliases() -> None:
    payload = {"start": [5, 0], "hops": [[3, 2], [1, 4]], "promotion": "crowned"}
    move = Move.from_json(payload)
    payload["hops"][0][0] = 7
    assert move.hops == ((3, 2), (1, 4))
    assert Move.from_json(move.to_json()) == move
    assert move.end_pos == (1, 4)
    result = move.to_json()
    result["start"][0] = 0
    assert move.start_pos == (5, 0)


@pytest.mark.parametrize(
    "payload",
    [
        {"start": [True, 0], "hops": [[1, 1]], "promotion": None},
        {"start": [-1, 0], "hops": [[1, 1]], "promotion": None},
        {"start": [1, 0], "hops": [], "promotion": None},
        {"start": [1, 0], "hops": [[1, 0]], "promotion": None},
        {"start": [1, 0], "hops": [[2, 1]], "promotion": ""},
        {"start": [1, 0], "hops": [[2, 1]], "promotion": None, "capture": [0, 0]},
        {"start": [1, 0], "hops": [[2, 1]] * 129, "promotion": None},
    ],
)
def test_malformed_or_forged_move_claims_are_rejected(payload: dict) -> None:
    with pytest.raises(ValueError):
        Move.from_json(payload)


def test_single_hop_is_immutable_and_cannot_bypass_game_manager() -> None:
    move = Move((2, 1), (1, 2))
    assert move.hops == ((1, 2),)
    with pytest.raises(FrozenInstanceError):
        move.end_pos = (0, 3)
    with pytest.raises(PermissionError):
        move.execute(object())
