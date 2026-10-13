"""User registry managing profile persistence, player associations, and activity logs."""

from typing import Dict, Optional, Any

try:
    from engine.model.users.user import User
except ImportError:
    from .user import User


class UserManager:
    """Manages registered user accounts, player linkages, and audit logging."""

    def __init__(self):
        """Initialize an empty UserManager."""
        self.users: Dict[int, User] = {}
        self._next_id: int = 1
        self.user_log: str = ""
        self.user_history: str = ""
        self.player_map: Dict[int, Any] = {}

    def register_user(self, user: User, user_id: Optional[int] = None) -> int:
        """Register a user in the repository.

        Args:
            user: User instance to register.
            user_id: Optional explicit user ID (auto-incremented if omitted).

        Returns:
            Assigned user ID integer.
        """
        if user_id is not None and (type(user_id) is not int or user_id < 1):
            raise ValueError("user ID must be a positive integer")
        uid = user_id if user_id is not None else self._next_id
        if uid in self.users:
            raise ValueError(f"user ID {uid} is already registered")
        self._next_id = max(self._next_id, uid + 1)
        self.users[uid] = user
        self.log_action(f"User registered: {user.username} (id: {uid})")
        return uid

    def get_user(self, user_id: int) -> Optional[User]:
        """Fetch a registered user by ID.

        Args:
            user_id: User identifier.

        Returns:
            User instance if found, None otherwise.
        """
        return self.users.get(user_id)

    def link_player(self, user_id: int, player: Any) -> None:
        """Associate a User ID with a live Player game participant.

        Args:
            user_id: Registered user ID.
            player: Player instance to link.
        """
        if user_id not in self.users:
            raise ValueError("cannot link an unregistered user")
        if user_id in self.player_map and self.player_map[user_id] is not player:
            raise ValueError("user already linked to a different player")
        if any(linked is player for uid, linked in self.player_map.items() if uid != user_id):
            raise ValueError("player already linked to a different user")
        self.player_map[user_id] = player

    def log_action(self, message: str) -> None:
        """Append an audit log entry.

        Args:
            message: Text message describing the action.
        """
        self.user_log += message + "\n"

    def record_history(self, entry: str) -> None:
        """Append an entry to the user history string.

        Args:
            entry: History record string.
        """
        self.user_history += entry + "\n"

    def execute_move(self, move: Optional[Any] = None, board: Optional[Any] = None) -> bool:
        """Refuse gameplay mutations through the identity registry.

        Moves must be authorized and committed by the game session's single
        domain boundary; this registry cannot validate the active configuration,
        turn, or authenticated participant.
        """
        raise PermissionError("moves must be committed through GameManager")
