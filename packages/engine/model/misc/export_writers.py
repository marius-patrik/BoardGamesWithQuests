"""Game-neutral interface for one trusted format-specific serializer."""

from abc import ABC, abstractmethod
from typing import Any


class ExportWriter(ABC):
    """Base class for a single format's game-owned serializer."""

    @abstractmethod
    def export(self, game_snapshot: Any) -> str:
        """Encode one validated game snapshot in this writer's format."""
