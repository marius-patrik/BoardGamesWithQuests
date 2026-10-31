"""Full shipped Chess rulebook acceptance against independent FIDE evidence.

FIDE Laws of Chess (2023): https://handbook.fide.com/chapter/E012023
Full game reference: .github/tests/fixtures/chess_opera_game_1858.json
Test positions substitute only placement/turn/rights, never prune JSON rules.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

import pytest

from model.definition import validate_definition
from model.manager import GameManager, TransitionError
from model.session import DesktopSession
from model.resources import bundled_games_root

OPERA = json.loads(
    (Path(__file__).parent / "fixtures" / "chess_opera_game_1858.json").read_text(encoding="utf-8")
)
FIDE_START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
PIECES = {"pawn": "p", "rook": "r", "knight": "n", "bishop": "b", "queen": "q", "king": "k"}


def square(name: str) -> list[int]:
    assert len(name) == 2 and name[0] in "abcdefgh" and name[1] in "12345678"
    return [8 - int(name[1]), ord(name[0]) - ord("a")]


def fen_placement(state: dict) -> str:
    squares = {}
    for piece in state["board"]:
        symbol = PIECES[piece["kind"]]
        squares[tuple(piece["square"])] = symbol.upper() if piece["side"] == 1 else symbol
    ranks = []
    for row in range(8):
        rank, blanks = "", 0
        for col in range(8):
            symbol = squares.get((row, col))
            if symbol is None:
                blanks += 1
            else:
                if blanks:
                    rank += str(blanks)
                    blanks = 0
                rank += symbol
        if blanks:
            rank += str(blanks)
        ranks.append(rank)
    return "/".join(ranks)


def choice(session: DesktopSession, uci: str) -> dict:
    source, destination = square(uci[:2]), square(uci[2:4])
    promotion = {"q": "queen", "r": "rook", "b": "bishop", "n": "knight"}.get(uci[4:])
    matches = [
        item
        for item in session.legal_actions()
        if item["start"] == source
        and item["hops"][-1] == destination
        and item["promotion"] == promotion
    ]
    assert len(matches) == 1, f"published legal move {uci} unavailable: {matches!r}"
    return matches[0]


def play(session: DesktopSession, uci: str) -> dict:
    state = session.snapshot()
    actor = state["participants"][str(state["active_side"])]
    result = session.submit(
        actor,
        state["revision"],
        {"type": "move", "move": choice(session, uci)},
        action_id=f"fide-{state['revision']}-{uci}",
    )
    assert result["state"]["revision"] == state["revision"] + 1
    assert result["state"]["active_side"] == -state["active_side"]
    return result


def reject(session: DesktopSession, action: dict, *, actor: str | None = None) -> None:
    before = session.snapshot()
    identity = actor or before["participants"][str(before["active_side"])]
    with pytest.raises(TransitionError):
        session.submit(identity, before["revision"], action)
    assert session.snapshot() == before


def reference_position(
    fen: str,
    *,
    to_move: str = "white",
    en_passant: str | None = None,
    castling: str = "",
    clock_seconds: int = 600,
) -> GameManager:
    """Construct a FEN-defined position under *all* shipped Chess rules.

    The fixture is a position input, not a reduced or alternative rulebook.
    """
    data = json.loads(bundled_games_root().joinpath("chess", "config.json").read_text())
    grouped: dict[tuple[str, str], list[list[int]]] = {}
    ranks = fen.split("/")
    assert len(ranks) == 8
    for row, rank in enumerate(ranks):
        col = 0
        for symbol in rank:
            if symbol.isdigit():
                col += int(symbol)
                continue
            kind = next(k for k, v in PIECES.items() if v == symbol.lower())
            color = "white" if symbol.isupper() else "black"
            grouped.setdefault((kind, color), []).append([row, col])
            col += 1
        assert col == 8
    data["board"]["starting_pieces"] = [
        {"piece": kind, "color": color, "squares": positions}
        for (kind, color), positions in grouped.items()
    ]
    data["starting_side"] = 1 if to_move == "white" else -1
    data["initial_state"]["special_rights"] = {
        "white_short": "K" in castling,
        "white_long": "Q" in castling,
        "black_short": "k" in castling,
        "black_long": "q" in castling,
    }
    data["initial_state"]["temporary_targets"]["en_passant"] = (
        square(en_passant) if en_passant else None
    )
    data["clock"]["initial_seconds"] = clock_seconds
    return GameManager(validate_definition(data), "fide-reference", ("white", "black"), 0)


def reference_move(game: GameManager, uci: str) -> dict:
    state = game.get_state()
    actor = state["participants"][str(state["active_side"])]
    promotion = {"q": "queen", "r": "rook", "b": "bishop", "n": "knight"}.get(uci[4:])
    matches = [
        item
        for item in game.get_valid_moves()
        if list(item.start_pos) == square(uci[:2])
        and list(item.end_pos) == square(uci[2:4])
        and item.promotion == promotion
    ]
    assert len(matches) == 1, f"FIDE reference move {uci} unavailable"
    return game.submit(
        actor,
        state["revision"],
        f"reference-{state['revision']}",
        matches[0],
        state["revision"] + 1,
    )


def test_full_initial_position_and_exact_legal_move_set():
    session = DesktopSession("chess")
    assert fen_placement(session.snapshot()) == FIDE_START
    actual = {
        chr(m["start"][1] + ord("a"))
        + str(8 - m["start"][0])
        + chr(m["hops"][-1][1] + ord("a"))
        + str(8 - m["hops"][-1][0])
        for m in session.legal_actions()
    }
    expected = {f"{file}2{file}{rank}" for file in "abcdefgh" for rank in ("3", "4")}
    expected.update({"b1a3", "b1c3", "g1f3", "g1h3"})
    assert actual == expected and len(actual) == 20


def test_published_morphy_opera_game_reaches_exact_checkmate_and_replays():
    """33 external PGN plies: captures, long castle, queen sacrifice and Rd8#."""
    session = DesktopSession("chess")
    for index, uci in enumerate(OPERA["uci"]):
        result = play(session, uci)
        if index < len(OPERA["uci"]) - 1:
            assert result["event"]["outcome"] is None, f"premature outcome at {uci}"
        if index % 4 == 0 or index == len(OPERA["uci"]) - 1:
            assert DesktopSession.recover(result["state"]).snapshot() == result["state"]
    state = session.snapshot()
    assert fen_placement(state) == OPERA["final_placement_fen"]
    assert state["active_side"] == -1
    assert state["outcome"]["kind"] == "win"
    assert state["outcome"]["cause"] == "checkmate"
    assert state["outcome"]["winner"] == "white"
    assert state["revision"] == len(OPERA["uci"]) == len(state["events"]) == 33
    assert session.legal_actions() == []
    reject(session, {"type": "resign"}, actor="black")


def test_live_en_passant_captures_correct_pawn():
    session = DesktopSession("chess")
    for uci in ("e2e4", "a7a6", "e4e5", "d7d5"):
        play(session, uci)
    result = play(session, "e5d6")
    assert fen_placement(result["state"]).split("/")[2] == "p2P4"
    assert all(p["square"] != square("d5") for p in result["state"]["board"])
    assert result["state"]["temporary_targets"]["en_passant"] is None
    assert DesktopSession.recover(result["state"]).snapshot() == result["state"]


def test_en_passant_right_expires_after_any_intervening_move():
    session = DesktopSession("chess")
    for uci in ("e2e4", "a7a6", "e4e5", "d7d5", "g1f3", "g8f6"):
        play(session, uci)
    assert not any(
        m["start"] == square("e5") and m["hops"][-1] == square("d6")
        for m in session.legal_actions()
    )
    reject(
        session,
        {
            "type": "move",
            "move": {
                "start": square("e5"),
                "hops": [square("d6")],
                "promotion": None,
            },
        },
    )


def test_live_kingside_castling_moves_rook_and_consumes_rights():
    session = DesktopSession("chess")
    # A legal Italian-game development, FIDE Article 3.8.2.
    for uci in ("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "e1g1"):
        play(session, uci)
    state = session.snapshot()
    by_square = {tuple(p["square"]): p for p in state["board"]}
    assert by_square[tuple(square("g1"))]["kind"] == "king"
    assert by_square[tuple(square("f1"))]["kind"] == "rook"
    assert state["special_rights"]["white_short"] is False
    assert state["special_rights"]["white_long"] is False
    assert DesktopSession.recover(state).snapshot() == state


def test_castling_blocked_from_initial_position():
    session = DesktopSession("chess")
    before = session.snapshot()
    assert not any(
        m["start"] == square("e1") and m["hops"][-1] == square("g1")
        for m in session.legal_actions()
    )
    assert session.snapshot() == before


def test_en_passant_discovered_check_is_illegal_with_full_rulebook():
    # FIDE 3.9: c5xd6 e.p. exposes Ka5 to Rh5 along the fifth rank.
    game = reference_position("k7/8/8/K1Pp3r/8/8/8/8", en_passant="d6")
    before = game.get_state()
    assert not any(
        list(m.start_pos) == square("c5") and list(m.end_pos) == square("d6")
        for m in game.get_valid_moves()
    )
    assert game.get_state() == before


def test_pinned_rook_cannot_expose_own_king():
    game = reference_position("k3r3/8/8/8/8/8/4R3/4K3")
    before = game.get_state()
    assert not any(
        list(m.start_pos) == square("e2") and list(m.end_pos) == square("f2")
        for m in game.get_valid_moves()
    )
    assert game.get_state() == before


@pytest.mark.parametrize("promote", ["q", "r", "b", "n"])
def test_all_four_promotions_with_full_rules_and_deterministic_replay(promote):
    game = reference_position("7k/P7/8/8/8/8/8/7K")
    actual = {
        m.promotion
        for m in game.get_valid_moves()
        if list(m.start_pos) == square("a7") and list(m.end_pos) == square("a8")
    }
    assert actual == {"queen", "rook", "bishop", "knight"}
    reference_move(game, "a7a8" + promote)
    promoted = next(p for p in game.get_state()["board"] if p["square"] == square("a8"))
    assert PIECES[promoted["kind"]] == promote
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_threefold_claim_rejected_at_two_appearances_and_accepted_at_three():
    # FIDE 9.2: same arrangement, player to move and legal rights.
    session = DesktopSession("chess")
    cycle = ("g1f3", "g8f6", "f3g1", "f6g8")
    for uci in cycle:
        play(session, uci)
    reject(session, {"type": "claim_draw", "claim": "threefold", "intended_move": None})
    for uci in cycle:
        play(session, uci)
    before = session.snapshot()
    assert before["outcome"] is None
    result = session.submit(
        "white",
        before["revision"],
        {"type": "claim_draw", "claim": "threefold", "intended_move": None},
        action_id="claim-threefold",
    )
    assert result["state"]["outcome"]["kind"] == "draw"
    assert result["state"]["outcome"]["cause"] == "threefold"
    assert fen_placement(result["state"]) == FIDE_START
    assert DesktopSession.recover(result["state"]).snapshot() == result["state"]


def test_fivefold_repetition_automatically_ends_real_game():
    # FIDE 9.6.1: the fifth identical position is automatically drawn.
    session = DesktopSession("chess")
    cycle = ("g1f3", "g8f6", "f3g1", "f6g8")
    for index in range(16):
        result = play(session, cycle[index % 4])
        if index != 15:
            assert result["state"]["outcome"] is None
    assert result["state"]["outcome"]["kind"] == "draw"
    assert result["state"]["outcome"]["cause"] == "fivefold"
    assert DesktopSession.recover(result["state"]).snapshot() == result["state"]


@pytest.mark.parametrize("minor", [None, "n", "b"])
def test_dead_king_only_and_single_minor_positions_end_as_draw(minor):
    # FIDE 5.2.2: K vs K, K+N vs K, K+B vs K are dead positions.
    fen = "4k3/8/8/8/8/8/8/4K3" if minor is None else f"4k3/8/8/8/8/8/{minor.upper()}7/4K3"
    game = reference_position(fen)
    event = reference_move(game, "e1f1")
    assert event["outcome"]["kind"] == "draw"
    assert event["outcome"]["cause"] == "dead-material"


def test_resignation_against_king_without_mating_possibility_is_draw():
    # FIDE 5.1.2: a player who resigns against a bare opposing king does not lose.
    game = reference_position("4k3/8/8/8/8/8/8/3QK3")
    event = game.submit_action("white", 0, "resign", {"type": "resign"}, 1)
    assert event["outcome"]["kind"] == "draw"
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_timeout_with_mating_material_awards_other_participant():
    # FIDE 6.9: white expires at time zero, with black's full army available.
    game = reference_position(FIDE_START, castling="KQkq", clock_seconds=0)
    event = game.submit_action("white", 0, "timeout", {"type": "timeout"}, 0)
    assert event["outcome"]["kind"] == "win"
    assert event["outcome"]["winner"] == "black"
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_fifty_move_claim_from_opening_is_rejected_atomically():
    session = DesktopSession("chess")
    reject(session, {"type": "claim_draw", "claim": "fifty-move", "intended_move": None})


def test_full_rulebook_stalemate_after_queen_move_is_not_checkmate():
    # FIDE 5.2.1: Ka8, Kc6, Qd6-c7 leaves black with no move but not in check.
    game = reference_position("k7/8/2KQ4/8/8/8/8/8")
    event = reference_move(game, "d6c7")
    assert event["outcome"]["kind"] == "draw"
    assert event["outcome"]["cause"] == "stalemate"
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


@pytest.mark.parametrize("attacking_file", ["e", "f", "g"])
def test_castling_out_of_through_or_into_check_is_forbidden(attacking_file):
    # FIDE 3.8.2.2: white short castle may not start, pass, or land in attack.
    fen = (
        "k3r3/8/8/8/8/8/8/4K2R"
        if attacking_file == "e"
        else ("k4r2/8/8/8/8/8/8/4K2R" if attacking_file == "f" else "k5r1/8/8/8/8/8/8/4K2R")
    )
    game = reference_position(fen, castling="K")
    before = game.get_state()
    assert not any(
        list(m.start_pos) == square("e1") and list(m.end_pos) == square("g1")
        for m in game.get_valid_moves()
    )
    assert game.get_state() == before


def test_promotion_capture_replaces_pawn_and_removes_captured_rook():
    # FIDE 3.7.3: capture and promotion are one complete legal move.
    game = reference_position("r6k/1P6/8/8/8/8/8/7K")
    event = reference_move(game, "b7a8q")
    assert event["captured"] == [square("a8")]
    assert (
        next(p for p in game.get_state()["board"] if p["square"] == square("a8"))["kind"] == "queen"
    )
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_intended_move_threefold_claim_does_not_commit_proposed_move():
    # FIDE 9.2.1: black can claim before f6-g8 recreates the initial position.
    session = DesktopSession("chess")
    for uci in ("g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1"):
        play(session, uci)
    before = session.snapshot()
    assert before["active_side"] == -1
    intended = choice(session, "f6g8")
    result = session.submit(
        "black",
        before["revision"],
        {"type": "claim_draw", "claim": "threefold", "intended_move": intended},
        action_id="intended-threefold",
    )
    assert result["state"]["outcome"]["kind"] == "draw"
    assert result["state"]["outcome"]["cause"] == "threefold"
    assert result["event"]["move"] is None
    assert result["state"]["board"] == before["board"]
    assert DesktopSession.recover(result["state"]).snapshot() == result["state"]
