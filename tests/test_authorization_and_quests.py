"""Verify identity, participant, clock and achievement behavior."""

from types import SimpleNamespace

import pytest

from engine.model.game.quest import Quest
from engine.model.game.timer import Timer
from engine.model.misc.quest_manager import QuestManager
from engine.model.users.manager import UserManager


def test_duplicate_users_are_rejected_without_overwriting_identity() -> None:
    users = UserManager()
    first = SimpleNamespace(username="first")
    second = SimpleNamespace(username="second")
    assert users.register_user(first, 5) == 5
    assert users.register_user(second) == 6
    with pytest.raises(ValueError, match="already registered"):
        users.register_user(second, 5)
    assert users.get_user(5) is first


def test_untrusted_registry_cannot_authorize_gameplay_or_share_player() -> None:
    users = UserManager()
    user1 = users.register_user(SimpleNamespace(username="u1"))
    user2 = users.register_user(SimpleNamespace(username="u2"))
    token = object()
    with pytest.raises(ValueError, match="unregistered"):
        users.link_player(999, token)
    users.link_player(user1, token)
    with pytest.raises(ValueError, match="different user"):
        users.link_player(user2, token)
    with pytest.raises(PermissionError):
        users.execute_move(object(), object())


def test_invalid_clock_actions_never_deduct_from_another_participant() -> None:
    clock = Timer(15, 2)
    with pytest.raises(ValueError):
        clock.tick(99, 3)
    with pytest.raises(ValueError):
        clock.tick(1, -1)
    with pytest.raises(ValueError):
        clock.add_time(-1, -4)
    assert clock.get_time(1) == 15 and clock.get_time(-1) == 15
    clock.tick(1, 17)
    assert clock.is_expired(1)
    assert clock.get_time(-1) == 15


def test_quest_rewards_are_isolated_by_game_and_participant() -> None:
    objective = Quest("capture", "Capture a piece", {"op": "true"}, 5)
    manager = QuestManager([objective])
    result = manager.complete("matchA", "alice", "capture")
    assert result.reward_points == 5
    assert manager.get_completed_quests("matchA", "alice") == [objective]
    assert manager.get_completed_quests("matchA", "bob") == []
    assert manager.get_completed_quests("matchB", "alice") == []
    with pytest.raises(ValueError, match="already completed"):
        manager.complete("matchA", "alice", "capture")
    assert manager.complete("matchA", "bob", "capture").reward_points == 5
