"""The chess rules, composed explicitly.

There is no registry and nothing is discovered by name. `build_rules()` below is the whole
list of what chess is, written out, so the set of rules in force is closed and greppable
and a rule that is not named here is not in force.
"""

from typing import Any, List

from engine.model.game.rule import Rule
from chess.rules.bishop_colour import BishopColourRule
from chess.rules.castling import CastlingRule
from chess.rules.check import CheckRule, CheckmateRule, StalemateRule
from chess.rules.draws import (
    FiftyMoveRule,
    InsufficientMaterialRule,
    MutualAgreementRule,
    ThreefoldRepetitionRule,
)
from chess.rules.en_passant import EnPassantRule
from chess.rules.flag import FlagFallRule
from chess.rules.promotion import PromotionRule
from chess.rules.royal import RoyalPieceKind

#: Every rule orthodox chess plays by, in the order they are declared.
RULES = (
    RoyalPieceKind,
    CastlingRule,
    EnPassantRule,
    PromotionRule,
    BishopColourRule,
    CheckRule,
    CheckmateRule,
    StalemateRule,
    InsufficientMaterialRule,
    FiftyMoveRule,
    ThreefoldRepetitionRule,
    MutualAgreementRule,
    FlagFallRule,
)


def build_rules() -> List[Rule]:
    """Build one instance of every chess rule, at its orthodox value.

    Returns:
        List[Rule]: The rules in force, in declaration order. That order is also the tie
        break when two propose an outcome at once.
    """
    return [rule() for rule in RULES]
