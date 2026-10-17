"""Chess clock and countdown timer tracking elapsed and remaining time for each player."""

from typing import List, Union


class Timer:
    """Manages player turn clocks, increments, countdown ticks, and expiration."""

    def __init__(self, initial_time: int, increment_seconds: int = 0):
        """Initialize game timers.

        Args:
            initial_time: Initial time per player in seconds.
        """
        if type(initial_time) is not int or initial_time < 0:
            raise ValueError("initial_time must be a non-negative integer")
        if type(increment_seconds) is not int or increment_seconds < 0:
            raise ValueError("increment_seconds must be a non-negative integer")
        self.increment_seconds = increment_seconds
        self.initial_time = initial_time
        self.player_times: List[int] = [initial_time, initial_time]

    def _get_player_index(self, player: Union[int, str]) -> int:
        """Resolve player identifier to clock array index.

        Args:
            player: 1/"white" for index 0, or -1/"black" for index 1.

        Returns:
            0 or 1 index.
        """
        if type(player) is int and player == 1 or player == "white":
            return 0
        if type(player) is int and player == -1 or player == "black":
            return 1
        raise ValueError(f"unknown player identifier: {player!r}")

    def reset_time(self) -> None:
        """Reset both player clocks to the initial time."""
        self.player_times = [self.initial_time, self.initial_time]

    def tick(self, player: Union[int, str], elapsed_seconds: int = 1) -> None:
        """Deduct elapsed seconds from a player's clock.

        Args:
            player: Player identifier (1 for White, -1 for Black).
            elapsed_seconds: Number of seconds to deduct (default: 1).
        """
        idx = self._get_player_index(player)
        if type(elapsed_seconds) is not int or elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be a non-negative integer")
        self.player_times[idx] = max(0, self.player_times[idx] - elapsed_seconds)

<<<<<<< HEAD:packages/engine/model/game/timer.py
    def add_time(self, player: int, increment_seconds: int) -> None:
||||||| b45d2e0f:src/model/game/timer.py
    countdown = tick

    def add_time(self, player: int, increment_seconds: int) -> None:
=======
    def add_time(self, player: Union[int, str], increment_seconds: int) -> None:
>>>>>>> fix/independent-review-findings:src/model/game/timer.py
        """Add increment time to a player's clock.

        Args:
            player: Player identifier (1 for White, -1 for Black, or index).
            increment_seconds: Seconds to add to player's clock.
        """
        idx = self._get_player_index(player)
        if type(increment_seconds) is not int or increment_seconds < 0:
            raise ValueError("increment_seconds must be a non-negative integer")
        self.player_times[idx] += increment_seconds

    def get_time(self, player: Union[int, str]) -> int:
        """Get remaining time in seconds for a player.

        Args:
            player: Player identifier (1 for White, -1 for Black, or index).

        Returns:
            Remaining seconds.
        """
        idx = self._get_player_index(player)
        return self.player_times[idx]

    def is_expired(self, player: Union[int, str]) -> bool:
        """Check if a player's clock has run out of time.

        Args:
            player: Player identifier (1 for White, -1 for Black, or index).

        Returns:
            True if remaining time is 0 or less, False otherwise.
        """
        return self.get_time(player) <= 0
