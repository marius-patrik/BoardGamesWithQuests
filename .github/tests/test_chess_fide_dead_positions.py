"""FIDE dead-position and flag-fall material reference positions.

FIDE 2023 Laws 5.2.2 and 6.9: possible mate means *some sequence
of legal moves*, not how many material points remain. Same-square-color
bishops never control opposite-colour king escapes, regardless of how
many promoted bishops exist. This file uses real bundled Chess rules.
https://handbook.fide.com/chapter/E012023
"""

from __future__ import annotations

from model.game.manager import GameManager
from test_chess_fide_full_definition import reference_move, reference_position

SAME_COLOUR_PROMOTED_BISHOPS = "4k3/8/8/8/8/2B1B1B1/8/4K3"
OPPOSITE_COLOUR_BISHOPS = "4k3/8/8/8/8/2BB4/8/4K3"


def test_three_promoted_same_square_colour_bishops_cannot_create_mate():
    # FIDE 5.2.2: three bishops attacking only one colour are no more
    # capable of mating the bare king than one such bishop.
    game = reference_position(SAME_COLOUR_PROMOTED_BISHOPS)
    result = reference_move(game, "e1d1")
    assert result["outcome"] is not None
    assert result["outcome"]["kind"] == "draw"
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_flag_fall_is_draw_when_three_same_colour_bishops_cannot_mate():
    # FIDE 6.9: even if Black's flag falls, White's bishop army cannot mate.
    game = reference_position(SAME_COLOUR_PROMOTED_BISHOPS, to_move="black", clock_seconds=0)
    event = game.submit_action("black", 0, "fide-dead-timeout", {"type": "timeout"}, 0)
    assert event["outcome"]["kind"] == "draw"
    assert GameManager.from_snapshot(game.get_state()).get_state() == game.get_state()


def test_two_opposite_square_colour_bishops_are_not_dead_material():
    # With bishops on both colours a mating sequence is possible.
    game = reference_position(OPPOSITE_COLOUR_BISHOPS)
    event = reference_move(game, "e1d1")
    assert event["outcome"] is None
