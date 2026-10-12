"""Game-neutral piece movement capabilities and identity."""

from typing import Any, List, Optional, Tuple


class Piece:
    """A piece whose movement is declared by its game, not by the engine.

    Attributes:
        _type: Game-defined piece identity.
        _vectors: Offsets a piece may travel into an empty square.
        _attack_vectors: Offsets a piece may use to capture.
        _can_jump: Whether intermediate occupied squares are ignored.
        _repeat: Whether movement and attack offsets can repeat along rays.
    """

    def __init__(
        self,
        color: Any,
        piece_type: Any,
        vectors: Optional[List[Tuple[int, int]]] = None,
        attack_vectors: Optional[List[Tuple[int, int]]] = None,
        can_jump: bool = False,
        name: Optional[str] = None,
        repeat: bool = False,
        initial_vectors: Optional[List[Tuple[int, int]]] = None,
    ):
        """Define a piece using game-supplied movement capabilities.

        Args:
            color: Game-defined side identifier.
            piece_type: Game-defined piece kind.
            vectors: Quiet-move offsets; shared attack offsets also permit capturing.
            attack_vectors: Capture offsets (defaults to the move offsets).
            can_jump: Whether intermediate squares may be occupied.
            name: Display name (defaults to the kind).
            repeat: Whether vectors may repeat, as for a sliding piece.
            initial_vectors: Additional quiet offsets allowed only before its first move.
        """
        self.__color = color
        self._type = piece_type
        self._vectors = list(vectors or [])
        self._attack_vectors = (
            list(attack_vectors) if attack_vectors is not None else list(self._vectors)
        )
        self._can_jump = can_jump
        self._repeat = repeat
        self._initial_vectors = list(initial_vectors or [])
        self._has_moved = False
        self._name = name or str(piece_type)

    def getDirections(self) -> List[Tuple[int, int]]:
        """Return quiet-move vectors."""
        return list(self._vectors)

    def getAttackDirections(self) -> List[Tuple[int, int]]:
        """Return capture and attacked-square vectors."""
        return list(self._attack_vectors)

    def getInitialVectors(self) -> List[Tuple[int, int]]:
        """Return extra quiet moves available only before the first move."""
        return list(self._initial_vectors)

    def canJump(self) -> bool:
        """Return whether intermediate occupied squares can be ignored."""
        return self._can_jump

    def canRepeat(self) -> bool:
        """Return whether a vector repeats along a ray."""
        return self._repeat

    def hasMoved(self) -> bool:
        """Return whether the piece has moved."""
        return self._has_moved

    def setMoved(self, moved: bool = True) -> None:
        """Update the moved state.

        Args:
            moved: New moved-state value.
        """
        self._has_moved = moved

    def getColor(self) -> Any:
        """Return the piece's game-defined side identifier."""
        return self.__color

    def getType(self) -> Any:
        """Return the piece's game-defined kind."""
        return self._type

    def getName(self) -> str:
        """Return the piece's display name."""
        return self._name
