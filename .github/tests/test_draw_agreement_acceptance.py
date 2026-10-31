"""Authoritative two-party draw agreement acceptance, including replay and clocks.

Published rules: FIDE Laws of Chess (2023), 9.1.2.1;
https://handbook.fide.com/chapter/E012023
WCDF English Draughts Rules (2025), 1.32 and 4.7;
https://nccheckers.org/NCCA/WCDF%20Checker%20-%20Draughts%20-%20English%20Rules.htm

Tests use the shipped game definitions and the public action/snapshot boundary.
"""

from __future__ import annotations

import copy

import pytest

from model.definition import load_bundled_definition
from model.manager import GameManager, TransitionError


def game(name: str) -> GameManager:
    return GameManager(load_bundled_definition(name), "draw-" + name, ("white", "black"), 0)


def take_turn(manager: GameManager, *, at: int = 1000) -> tuple[str, str]:
    state = manager.get_state()
    actor = state["participants"][str(state["active_side"])]
    opponent = next(identity for identity in state["participants"].values() if identity != actor)
    move = manager.get_valid_moves()[0].to_json()
    manager.submit_action(
        actor, state["revision"], "first-move", {"type": "move", "move": move}, at
    )
    return actor, opponent


def send(manager: GameManager, actor: str, kind: str, *, at: int, action_id: str):
    return manager.submit_action(
        actor, manager.get_state()["revision"], action_id, {"type": kind}, at
    )


def denied(manager: GameManager, actor: str, action: dict, *, at: int = 1200):
    before = manager.get_state()
    with pytest.raises(TransitionError):
        manager.submit_action(actor, before["revision"], "invalid-" + str(at), action, at)
    assert manager.get_state() == before


@pytest.mark.parametrize("name", ["chess", "checkers"])
def test_version_one_snapshots_remain_identical_until_draw_lifecycle_is_used(name):
    manager = game(name)
    initial = manager.get_state()
    assert "pending_draw_offer" not in initial
    assert GameManager.from_snapshot(initial).get_state() == initial
    take_turn(manager)
    moved = manager.get_state()
    assert "pending_draw_offer" not in moved
    assert GameManager.from_snapshot(moved).get_state() == moved


@pytest.mark.parametrize("name", ["chess", "checkers"])
def test_agreement_is_an_authoritative_nonmoving_result_and_replays(name):
    manager = game(name)
    mover, respondent = take_turn(manager)
    if name == "chess":
        # FIDE 5.2.3: both participants must make a move before agreement.
        state = manager.get_state()
        manager.submit_action(
            respondent,
            state["revision"],
            "second-move",
            {"type": "move", "move": manager.get_valid_moves()[0].to_json()},
            1100,
        )
        mover, respondent = respondent, mover
    prior = manager.get_state()
    offer = send(manager, mover, "offer_draw", at=1200, action_id="offer")
    pending = manager.get_state()
    assert pending["pending_draw_offer"] == {"actor": mover, "revision": prior["revision"] + 1}
    assert pending["active_side"] == prior["active_side"]
    assert pending["board"] == prior["board"]
    assert pending["position_history"] == prior["position_history"]
    assert pending["quest_progress"] == prior["quest_progress"]
    assert pending["quest_scores"] == prior["quest_scores"]
    assert pending["clocks"] == prior["clocks"]
    assert offer["outcome"] is None and offer["action"] == {"type": "offer_draw"}
    assert GameManager.from_snapshot(pending).get_state() == pending
    assert (
        manager.submit_action(mover, prior["revision"], "offer", {"type": "offer_draw"}, 99000)
        == offer
    )
    assert manager.get_state() == pending

    accepted = send(manager, respondent, "accept_draw", at=2300, action_id="accept")
    final = manager.get_state()
    assert final["outcome"] == {
        "kind": "draw",
        "cause": "agreement",
        "winner": None,
        "priority": 1000,
    }
    assert accepted["outcome"] == final["outcome"]
    assert final["pending_draw_offer"] is None
    assert final["active_side"] == prior["active_side"]
    assert final["board"] == prior["board"]
    assert final["position_history"] == prior["position_history"]
    assert final["quest_scores"] == prior["quest_scores"]
    assert final["quest_progress"] == prior["quest_progress"]
    assert final["clocks"]["anchor_ms"] == 2300
    active = str(prior["active_side"])
    assert final["clocks"]["remaining_ms"][active] == (
        prior["clocks"]["remaining_ms"][active] - (2300 - prior["clocks"]["anchor_ms"])
    )
    assert GameManager.from_snapshot(final).get_state() == final
    assert (
        manager.submit_action(
            respondent, prior["revision"] + 1, "accept", {"type": "accept_draw"}, 99999
        )
        == accepted
    )
    denied(manager, mover, {"type": "offer_draw"}, at=2400)
    denied(manager, respondent, {"type": "reject_draw"}, at=2401)


@pytest.mark.parametrize("name", ["chess", "checkers"])
def test_declining_or_playing_a_legal_move_expires_offer_without_double_clock_charge(name):
    manager = game(name)
    mover, opponent = take_turn(manager)
    after_move = manager.get_state()
    send(manager, mover, "offer_draw", at=1100, action_id="offer")
    declined = send(manager, opponent, "reject_draw", at=1900, action_id="decline")
    state = manager.get_state()
    assert declined["action"] == {"type": "reject_draw"}
    assert state["outcome"] is None and state["pending_draw_offer"] is None
    assert state["board"] == after_move["board"]
    assert state["position_history"] == after_move["position_history"]
    assert state["clocks"] == after_move["clocks"]
    denied(manager, mover, {"type": "accept_draw"}, at=2000)
    assert GameManager.from_snapshot(state).get_state() == state

    fresh = game(name)
    original, replying = take_turn(fresh)
    send(fresh, original, "offer_draw", at=1100, action_id="new-offer")
    before = fresh.get_state()
    action = {"type": "move", "move": fresh.get_valid_moves()[0].to_json()}
    send_move = fresh.submit_action(replying, before["revision"], "reply-move", action, 2200)
    next_state = fresh.get_state()
    assert send_move["move"] == action["move"]
    assert next_state["pending_draw_offer"] is None
    assert next_state["clocks"]["remaining_ms"][str(before["active_side"])] == (
        before["clocks"]["remaining_ms"][str(before["active_side"])]
        - 1200
        + before["clocks"]["increment_ms"]
    )
    assert GameManager.from_snapshot(next_state).get_state() == next_state


def test_wcdf_draw_offer_only_after_own_completed_move_and_cannot_be_withdrawn():
    manager = game("checkers")
    denied(manager, "black", {"type": "offer_draw"}, at=1)
    denied(manager, "white", {"type": "offer_draw"}, at=2)
    mover, respondent = take_turn(manager)
    denied(manager, respondent, {"type": "offer_draw"}, at=1100)
    send(manager, mover, "offer_draw", at=1200, action_id="offer")
    denied(manager, mover, {"type": "reject_draw"}, at=1300)
    denied(manager, mover, {"type": "accept_draw"}, at=1301)
    denied(manager, mover, {"type": "offer_draw"}, at=1302)
    send(manager, respondent, "reject_draw", at=1400, action_id="reject")
    denied(manager, mover, {"type": "offer_draw"}, at=1500)


def test_fide_offers_are_valid_outside_preferred_post_move_window():
    # FIDE 9.1.2.1 validates out-of-window offers; 5.2.3 still requires
    # at least one move by BOTH players before a draw agreement can terminate.
    for offerer, accepter in (("white", "black"), ("black", "white")):
        manager = game("chess")
        send(manager, offerer, "offer_draw", at=100, action_id="offer")
        assert manager.get_state()["pending_draw_offer"]["actor"] == offerer
        denied(manager, accepter, {"type": "accept_draw"}, at=200)
        send(manager, accepter, "reject_draw", at=300, action_id="reject")
        assert GameManager.from_snapshot(manager.get_state()).get_state() == manager.get_state()
    manager = game("chess")
    first, second = take_turn(manager)
    state = manager.get_state()
    manager.submit_action(
        second,
        state["revision"],
        "second-move",
        {"type": "move", "move": manager.get_valid_moves()[0].to_json()},
        1100,
    )
    send(manager, first, "offer_draw", at=1200, action_id="offer-after-moves")
    result = send(manager, second, "accept_draw", at=1300, action_id="accept-after-moves")
    assert result["outcome"]["kind"] == "draw"
    assert GameManager.from_snapshot(manager.get_state()).get_state() == manager.get_state()


def test_fide_offer_made_by_active_player_survives_own_legal_move():
    # Under FIDE 9.1.2.1, only an opponent's action can refuse an offer.
    # The offerer may offer before moving; that move does not withdraw it.
    manager = game("chess")
    white = "white"
    black = "black"
    initial = manager.get_state()
    send(manager, white, "offer_draw", at=100, action_id="white-offers-first")
    before = manager.get_state()
    assert before["pending_draw_offer"]["actor"] == white
    move = manager.get_valid_moves()[0]
    event = manager.submit_action(
        white,
        before["revision"],
        "offering-side-move",
        {"type": "move", "move": move.to_json()},
        200,
    )
    after = manager.get_state()
    assert event["outcome"] is None
    assert after["pending_draw_offer"]["actor"] == white
    assert GameManager.from_snapshot(after).get_state() == after
    denied(manager, black, {"type": "accept_draw"}, at=300)
    move = manager.get_valid_moves()[0]
    manager.submit_action(
        black,
        after["revision"],
        "opponent-declines-by-moving",
        {"type": "move", "move": move.to_json()},
        400,
    )
    finished = manager.get_state()
    assert finished["pending_draw_offer"] is None
    assert GameManager.from_snapshot(finished).get_state() == finished

    # Once each participant has moved, the opponent can accept a still-pending
    # offer even if the offering participant just played their next move.
    send(manager, white, "offer_draw", at=500, action_id="fresh-offer")
    before = manager.get_state()
    manager.submit_action(
        white,
        before["revision"],
        "white-third",
        {"type": "move", "move": manager.get_valid_moves()[0].to_json()},
        600,
    )
    assert manager.get_state()["pending_draw_offer"]["actor"] == white
    accepted = send(manager, black, "accept_draw", at=700, action_id="black-accepts")
    assert accepted["outcome"]["kind"] == "draw"
    assert GameManager.from_snapshot(manager.get_state()).get_state() == manager.get_state()


def test_fide_offer_does_not_survive_offering_players_checkmating_move():
    # FIDE 9.1.2.1: even an unrefused offer expires when play concludes.
    # The independent four-ply Fool's Mate establishes a real terminal move.
    manager = game("chess")

    def play(actor, start, end, at):
        state = manager.get_state()
        start_square = [8 - int(start[1]), ord(start[0]) - ord("a")]
        end_square = [8 - int(end[1]), ord(end[0]) - ord("a")]
        candidates = [
            move
            for move in manager.get_valid_moves()
            if list(move.start_pos) == start_square and list(move.end_pos) == end_square
        ]
        assert len(candidates) == 1
        return manager.submit_action(
            actor,
            state["revision"],
            f"mate-ply-{at}",
            {"type": "move", "move": candidates[0].to_json()},
            at,
        )

    play("white", "f2", "f3", 1)
    play("black", "e7", "e5", 2)
    play("white", "g2", "g4", 3)
    send(manager, "black", "offer_draw", at=4, action_id="black-mate-offer")
    assert manager.get_state()["pending_draw_offer"]["actor"] == "black"
    result = play("black", "d8", "h4", 5)
    assert result["outcome"]["cause"] == "checkmate"
    terminal = manager.get_state()
    assert terminal["pending_draw_offer"] is None
    assert GameManager.from_snapshot(terminal).get_state() == terminal


def test_strict_payload_auth_revision_and_replay_tampering_are_atomic():
    manager = game("chess")
    initial = manager.get_state()
    for bad in (
        {"type": "offer_draw", "actor": "white"},
        {"type": "accept_draw", "value": True},
        {"type": "reject_draw", "pending": True},
        {"type": "offer_draw", "move": None},
        {"type": 1},
    ):
        denied(manager, "white", bad, at=1)
    denied(manager, "intruder", {"type": "offer_draw"}, at=2)
    result = manager.submit_action("white", 0, "id", {"type": "offer_draw"}, 3)
    pending = manager.get_state()
    assert result["revision"] == 1
    with pytest.raises(TransitionError):
        manager.submit_action("black", 0, "stale", {"type": "accept_draw"}, 4)
    with pytest.raises(TransitionError):
        manager.submit_action("white", 0, "id", {"type": "reject_draw"}, 4)
    with pytest.raises(TransitionError):
        manager.submit_action("white", 1, "wrong", {"type": "accept_draw"}, 5)
    with pytest.raises(TransitionError):
        manager.submit_action("white", 1, "again", {"type": "offer_draw"}, 6)
    with pytest.raises(TransitionError):
        manager.submit_action("black", 1, "reverse-clock", {"type": "accept_draw"}, 2)
    assert manager.get_state() == pending
    for tamper in (
        {"pending_draw_offer": None},
        {"revision": 100},
        {"events": [dict(pending["events"][0], actor="black")]},
    ):
        hostile = copy.deepcopy(pending)
        hostile.update(tamper)
        with pytest.raises(TransitionError):
            GameManager.from_snapshot(hostile)
    assert initial["revision"] == 0


@pytest.mark.parametrize("name", ["chess", "checkers"])
def test_clock_expiry_rejects_pending_agreement_without_mutation(name):
    manager = game(name)
    mover, other = take_turn(manager)
    send(manager, mover, "offer_draw", at=1100, action_id="offer")
    state = manager.get_state()
    deadline = (
        state["clocks"]["anchor_ms"] + state["clocks"]["remaining_ms"][str(state["active_side"])]
    )
    denied(manager, other, {"type": "accept_draw"}, at=deadline)
    denied(manager, other, {"type": "reject_draw"}, at=deadline + 1)
    assert GameManager.from_snapshot(state).get_state() == state
