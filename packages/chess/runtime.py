"""The chess configuration: the default game, shipped with the package.

`board.py` declares the rows, columns and starting placement; `pieces/`, `rules/`,
`quests/`, `clocks/` and `export/` hold one file per entry. It is the default configuration
and cannot be edited or deleted: a variant starts by duplicating it.

Composition is explicit. `build_configuration()` below is the whole list of what chess is —
there is no registry, nothing is discovered by name, and a rule that is not named here is
not in force.
"""

from typing import List

from engine.model.game.runtime_configuration import Configuration
from engine.model.game.games import DEFAULT_GAME
from engine.model.game.quest import Quest
from engine.model.game.rule import Rule
from chess.board import DIMENSIONS, build_board
from chess.rules import build_rules


def build_configuration() -> Configuration:
    """Assemble the chess configuration.

    Returns:
        Configuration: The chess board, and the rules, quests, clocks and exporters chess
        brings with it.
    """
    return Configuration(
        name=DEFAULT_GAME,
        path="",
        board=build_board(),
        pieces=[],
        rules=build_rules(),
        quests=build_quests(),
        clocks=[],
        exporters=[],
    )


def build_quests() -> List[Quest]:
    """Build the quests chess offers by default.

    Returns:
        List[Quest]: A small starter set, all of them switchable from the settings form.
    """
    from engine.model.game.quests import CaptureN, FirstBlood, MakeCheckN, WonBy

    return [
        FirstBlood(reward=25),
        CaptureN(count=5, reward=50),
        MakeCheckN(count=3, reward=40),
        WonBy(color=1, reward=75),
    ]
