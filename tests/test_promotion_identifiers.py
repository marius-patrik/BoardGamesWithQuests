"""FR-3/16/34/69: configured piece identifiers survive promotion and replay."""

import pytest

from engine.model.game.configuration import ConfigurationError, validate_definition
from engine.model.game.manager import GameManager
from engine.model.game.move import Move


def definition_data(identifier: str) -> dict:
    """Create a neutral choice-promotion definition with an explicit identifier."""
    capabilities = {
        "symbols": {"white": "W", "black": "B"},
        "moves": [[-1, 1]],
        "attacks": [[-1, 1]],
        "jump": False,
        "repeat": False,
    }
    return {
        "schema_version": 2,
        "name": "identifier-boundary",
        "title": "Identifier boundary",
        "default": False,
        "playable": False,
        "board": {
            "rows": 6,
            "columns": 6,
            "starting_pieces": [
                {"piece": "runner", "color": "white", "squares": [[1, 1]]},
                {"piece": "runner", "color": "black", "squares": [[4, 4]]},
            ],
        },
        "pieces": {
            "runner": {
                **capabilities,
                "promotion": {
                    "rank": "far",
                    "options": [identifier],
                    "mode": "choice",
                    "stop_capture": False,
                },
            },
            identifier: dict(capabilities),
        },
        "clock": {"initial_seconds": 600, "increment_seconds": 0},
        "exports": [],
        "appearance": {},
        "rules": [
            {
                "id": "permission",
                "hook": "permits_move",
                "when": {"op": "true"},
                "effects": [{"op": "permit", "params": {}}],
            }
        ],
        "quests": [],
    }


@pytest.mark.parametrize("length", [100, 101, 128])
def test_configured_identifier_promotes_and_reconstructs_at_supported_boundaries(
    length: int,
) -> None:
    identifier = "p" * length
    session = GameManager(
        validate_definition(definition_data(identifier)), "identifier", ("alice", "bob"), 0
    )
    intent = Move((1, 1), (0, 2), promotion=identifier)
    assert session.get_valid_moves() == [intent]
    assert Move.from_json(intent.to_json()) == intent
    event = session.submit("alice", 0, "promote", intent, 1)
    snapshot = session.get_state()
    promoted = next(piece for piece in snapshot["board"] if piece["square"] == [0, 2])
    assert promoted["kind"] == identifier
    assert event["move"]["promotion"] == identifier
    reconstructed = GameManager.from_snapshot(snapshot)
    assert reconstructed.get_state() == snapshot
    assert reconstructed.submit("alice", 0, "promote", intent, 100) == event
    assert reconstructed.get_state() == snapshot


def test_oversized_configuration_and_intent_reject_without_changing_valid_session() -> None:
    session = GameManager(
        validate_definition(definition_data("p" * 128)), "identifier", ("alice", "bob"), 0
    )
    before = session.get_state()
    oversized = "p" * 129
    with pytest.raises(ConfigurationError):
        validate_definition(definition_data(oversized))
    with pytest.raises(ValueError):
        Move((1, 1), (0, 2), promotion=oversized)
    with pytest.raises(ValueError):
        Move.from_json({"start": [1, 1], "hops": [[0, 2]], "promotion": oversized})
    assert session.get_state() == before
