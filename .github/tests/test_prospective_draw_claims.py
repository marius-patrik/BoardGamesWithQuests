"""Prove read-only canonical intended-move claims through shipped rule definitions.

References: FIDE 9.2.1/9.2.2 (https://handbook.fide.com/chapter/E012023)
and WCDF 2025 1.32.1/1.32.2
(https://nccheckers.org/NCCA/WCDF%20Checker%20-%20Draughts%20-%20English%20Rules.htm).
"""

from __future__ import annotations

from importlib import resources
import json
import random

import pytest

from model.definition import validate_definition
from model.manager import GameManager, TransitionError
from model.move import Move
from model.session import DesktopSession


def chess_square(name):
    return [8 - int(name[1]), ord(name[0]) - ord("a")]


def chess_move(session, uci):
    before = session.snapshot()
    start, end = chess_square(uci[:2]), chess_square(uci[2:4])
    candidates = [
        move
        for move in session.legal_actions()
        if move["start"] == start and move["hops"][-1] == end
    ]
    assert len(candidates) == 1
    session.submit(
        before["participants"][str(before["active_side"])],
        before["revision"],
        {"type": "move", "move": candidates[0]},
        action_id="chess-" + str(before["revision"]),
    )
    return candidates[0]


def checkers_reference():
    data = json.loads(resources.files("games").joinpath("checkers", "config.json").read_text())
    data["board"]["starting_pieces"] = [
        {"piece": "king", "color": "black", "squares": [[2, 1]]},
        {"piece": "king", "color": "white", "squares": [[5, 6]]},
    ]
    return GameManager(validate_definition(data), "prospective-wcdf", ("white", "black"), 0)


def checkers_cycle(index):
    return (
        Move((2, 1), (3, 2)),
        Move((5, 6), (4, 5)),
        Move((3, 2), (2, 1)),
        Move((4, 5), (5, 6)),
    )[index % 4]


def advance_checkers(manager, turns):
    for index in range(turns):
        state = manager.get_state()
        move = checkers_cycle(index)
        assert move in manager.get_valid_moves()
        manager.submit_action(
            state["participants"][str(state["active_side"])],
            state["revision"],
            f"checkers-move-{index}",
            {"type": "move", "move": move.to_json()},
            index + 1,
        )


def test_fide_prospective_repetition_is_projected_from_real_moves_without_commit():
    session = DesktopSession("chess")
    for uci in ("g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1"):
        chess_move(session, uci)
    before = session.snapshot()
    options = session.draw_claim_candidates("threefold")
    assert options["current"] is False
    intended = {"start": chess_square("f6"), "hops": [chess_square("g8")], "promotion": None}
    assert intended in options["intended_moves"]
    assert session.snapshot() == before
    result = session.submit(
        "black",
        before["revision"],
        {"type": "claim_draw", "claim": "threefold", "intended_move": intended},
        action_id="fide-prospective",
    )
    assert result["state"]["outcome"]["cause"] == "threefold"
    assert result["state"]["board"] == before["board"]
    assert result["state"]["quest_scores"] == before["quest_scores"]
    assert DesktopSession.recover(result["state"]).snapshot() == result["state"]


def test_fide_claim_from_current_position_is_distinct_from_intended_claim():
    session = DesktopSession("chess")
    for uci in ("g1f3", "g8f6", "f3g1", "f6g8") * 2:
        chess_move(session, uci)
    before = session.snapshot()
    options = session.draw_claim_candidates("threefold")
    assert options["current"] is True
    assert session.snapshot() == before
    state = session.submit(
        "white",
        before["revision"],
        {"type": "claim_draw", "claim": "threefold", "intended_move": None},
        action_id="fide-current",
    )["state"]
    assert state["outcome"]["cause"] == "threefold"
    assert state["board"] == before["board"]


def test_wcdf_third_repetition_claim_requires_complete_prospective_move():
    manager = checkers_reference()
    advance_checkers(manager, 7)
    before = manager.get_state()
    candidates = manager.draw_claim_candidates("threefold")
    assert candidates["current"] is False
    assert candidates["intended_moves"] == [checkers_cycle(3).to_json()]
    assert manager.get_state() == before
    action = {
        "type": "claim_draw",
        "claim": "threefold",
        "intended_move": checkers_cycle(3).to_json(),
    }
    event = manager.submit_action("white", 7, "wcdf-prospective", action, 8)
    assert event["outcome"]["cause"] == "threefold"
    assert manager.get_state()["board"] == before["board"]
    assert manager.get_state()["quest_progress"] == before["quest_progress"]
    assert GameManager.from_snapshot(manager.get_state()).get_state() == manager.get_state()


def test_wcdf_forty_completed_moves_cannot_be_claimed_prospectively_at_79():
    manager = checkers_reference()
    advance_checkers(manager, 79)
    before = manager.get_state()
    current = manager.draw_claim_candidates("forty-move")
    assert current == {"current": False, "intended_moves": []}
    with pytest.raises(TransitionError):
        manager.submit_action(
            "white",
            79,
            "premature-forty",
            {
                "type": "claim_draw",
                "claim": "forty-move",
                "intended_move": checkers_cycle(3).to_json(),
            },
            80,
        )
    assert manager.get_state() == before
    advance = checkers_cycle(3)
    manager.submit_action(
        "white", 79, "move-eighty", {"type": "move", "move": advance.to_json()}, 80
    )
    mature = manager.draw_claim_candidates("forty-move")
    assert mature["current"] is True
    assert mature["intended_moves"] == []
    assert GameManager.from_snapshot(manager.get_state()).get_state() == manager.get_state()


def test_fide_prospective_fifty_move_threshold_from_ninety_nine_quiet_plies():
    # FIDE 9.3.1: 50 moves by each player without pawn motion/capture can be
    # declared before making the 100th half-move. Keep the shipped FIDE rules
    # intact and exercise 99 genuine accepted quiet legal moves in a small,
    # independently specified K+2N versus K+2N position.
    data = json.loads(resources.files("games").joinpath("chess", "config.json").read_text())
    data["board"]["starting_pieces"] = [
        {"piece": "king", "color": "white", "squares": [[7, 4]]},
        {"piece": "knight", "color": "white", "squares": [[7, 1], [7, 6]]},
        {"piece": "king", "color": "black", "squares": [[0, 4]]},
        {"piece": "knight", "color": "black", "squares": [[0, 1], [0, 6]]},
    ]
    manager = GameManager(
        validate_definition(data), "fide-fifty-prospective", ("white", "black"), 0
    )
    rng = random.Random(438)
    for number in range(99):
        current = manager.get_state()
        occupied = {tuple(piece["square"]) for piece in current["board"]}
        legal_quiet = [
            intent
            for intent in manager.get_valid_moves()
            if intent.end_pos not in occupied and intent.promotion is None
        ]
        assert legal_quiet, f"no quiet legal continuation at ply {number + 1}"
        choice = rng.choice(legal_quiet)
        result = manager.submit_action(
            current["participants"][str(current["active_side"])],
            current["revision"],
            f"fide-quiet-{number}",
            {"type": "move", "move": choice.to_json()},
            number + 1,
        )
        assert result["outcome"] is None, f"premature automatic result at ply {number + 1}"
    before = manager.get_state()
    assert before["halfmove_count"] == 99
    candidates = manager.draw_claim_candidates("fifty-move")
    assert candidates["current"] is False
    assert candidates["intended_moves"]
    assert manager.get_state() == before
    chosen = candidates["intended_moves"][0]
    assert chosen["hops"][-1] not in [piece["square"] for piece in before["board"]]
    result = manager.submit_action(
        before["participants"][str(before["active_side"])],
        99,
        "fide-claim-100",
        {"type": "claim_draw", "claim": "fifty-move", "intended_move": chosen},
        100,
    )
    assert result["outcome"]["kind"] == "draw"
    assert result["outcome"]["cause"] == "fifty-move"
    assert manager.get_state()["board"] == before["board"]
    assert GameManager.from_snapshot(manager.get_state()).get_state() == manager.get_state()


def test_invalid_claim_discovery_and_preview_are_atomic():
    manager = checkers_reference()
    before = manager.get_state()
    assert set(manager.configured_draw_claims()) == {"threefold", "forty-move"}
    with pytest.raises(TransitionError):
        manager.draw_claim_candidates("not-a-configured-claim")
    assert manager.draw_claim_candidates("threefold") == {"current": False, "intended_moves": []}
    assert manager.get_state() == before
