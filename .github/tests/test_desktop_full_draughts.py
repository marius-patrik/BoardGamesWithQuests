"""Complete independent 1981 English-draughts match, via the player action interface.

World Championship Match Game 37: M. Tinsley (Black) versus A. Long (White).
Reference game: https://en.wikipedia.org/wiki/English_draughts#Notation
No alternate move generator or capture implementation is used.
"""

from __future__ import annotations

import re

from model.game.notation import render_notation
from model.game.session import DesktopSession

RECORDED_MOVES = """
9-14 23-18 14x23 27x18 5-9 26-23 12-16 30-26
16-19 24x15 10x19 23x16 11x20 22-17 7-11 18-15
11x18 28-24 20x27 32x5 8-11 26-23 4-8 25-22
11-15 17-13 8-11 21-17 11-16 23-18 15-19 17-14
19-24 14-10 6x15 18x11 24-28 22-17 28-32 17-14
32-28 31-27 16-19 27-24 19-23 24-20 23-26 29-25
26-30 25-21 30-26 14-9 26-23 20-16 23-18 16-12
18-14 11-8 28-24 8-4 24-19 4-8 19-16 9-6
1x10 5-1 10-15 1-6 2x9 13x6 16-11 8-4
15-18 6-1 18-22 1-6 22-26 6-1 26-30 1-6
30-26 6-1 26-22 1-6 22-18 6-1 14-9 1-5
9-6 21-17 18-22
""".split()


def _square(number: int) -> tuple[int, int]:
    if not 1 <= number <= 32:
        raise AssertionError(f"invalid published dark square: {number}")
    row, offset = divmod(number - 1, 4)
    return row, 2 * offset + (1 if row % 2 == 0 else 0)


def test_recorded_full_tournament_game_through_actual_draughts_actions():
    session = DesktopSession("checkers")
    assert len(RECORDED_MOVES) == 91
    for index, token in enumerate(RECORDED_MOVES, 1):
        match = re.fullmatch(r"(\d+)([-x])(\d+)", token)
        assert match, f"invalid published move {token}"
        start = _square(int(match.group(1)))
        end = _square(int(match.group(3)))
        capture = match.group(2) == "x"
        offered = [
            move for move in session.legal_actions()
            if tuple(move["start"]) == start
            and tuple(move["hops"][-1]) == end
            and (
                any(abs(hop[0] - src[0]) > 1 for src, hop in zip(
                    [move["start"], *move["hops"][:-1]], move["hops"]
                )) == capture
            )
        ]
        assert len(offered) == 1, (
            f"published move {index}: {token} unavailable or ambiguous;"
            f" offered={session.legal_actions()}"
        )
        before = session.snapshot()
        actor = before["participants"][str(before["active_side"])]
        session.submit(
            actor, before["revision"],
            {"type": "move", "move": offered[0]},
            action_id=f"recorded-1981-game37-{index}",
        )
    state = session.snapshot()
    assert state["revision"] == len(RECORDED_MOVES)
    assert state["active_side"] == 1, "Black played the last recorded move"
    assert state["outcome"] is None, "The original tournament game ended by resignation"
    final = session.submit(
        "white", state["revision"], {"type": "resign"},
        action_id="recorded-1981-game37-resignation",
    )["state"]
    assert final["outcome"]["kind"] == "win"
    assert final["outcome"]["winner"] == "black"
    assert final["outcome"]["cause"] == "resignation"
    assert len(final["events"]) == 92
    assert DesktopSession.recover(final).snapshot() == final
    ext, pdn = render_notation(final)
    assert ext == ".pdn"
    assert '[Result "0-1"]' in pdn
    assert "1. 9-14 23-18 2. 14x23 27x18" in pdn
    assert "46. 18-22 0-1" in pdn
