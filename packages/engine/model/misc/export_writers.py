"""Game-independent exporter interface; concrete writers belong to game packages."""

from abc import ABC, abstractmethod
from typing import Any, Tuple


class ExportWriter(ABC):
    """Interface implemented by a game-specific, validated serializer.

    The engine does not offer PGN, FEN or any other game-specific format.
    Only a game package that can produce a correct representation may advertise
    and register that format.
    """

    @abstractmethod
    def formats(self) -> Tuple[str, ...]:
        """Return the format identifiers implemented by this writer."""

    @abstractmethod
    def export(self, format_type: str, **kwargs: Any) -> str:
        """Serialize a game state or move history.

        Args:
            format_type: Format previously declared by `formats`.
            **kwargs: Format-specific state provided by the game implementation.

        Returns:
            Valid serialized output in the requested format.

        Raises:
            ValueError: If the format is unsupported or state cannot be serialized.
        """
