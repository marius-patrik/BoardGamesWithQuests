"""Targeted G1 schema probes; not the permanent gameplay test suite."""

from engine.model.game.configuration import board_from_definition, load_definition
from engine.model.game.schema import condition, validate_hooks
from engine.model.game.quest import Quest
from engine.model.misc.quest_manager import QuestManager

for name, count in (
    ("chess", 32),
    ("english_draughts", 24),
    ("international_checkers", 40),
):
    definition = load_definition(name)
    assert not definition.playable
    assert not definition.rules and not definition.quests
    board = board_from_definition(definition)
    placed = 0
    for row in range(board.rows):
        for col in range(board.cols):
            placed += board.get_piece_at((row, col)) is not None
    assert placed == count

when = {
    "op": "all",
    "args": [
        {"op": "test", "query": "capture_paths", "params": {"player": "active"}},
        {
            "op": "compare",
            "relation": "gte",
            "left": {"query": "capture_count", "params": {"candidate": "move"}},
            "right": 1,
        },
    ],
}
validate_hooks(
    [
        {
            "id": "capture",
            "hook": "permits_move",
            "when": when,
            "effects": [{"op": "deny", "params": {"reason": "capture_required"}}],
        }
    ],
    [{"id": "capture_quest", "description": "Capture a piece", "when": when, "reward": 10}],
)

for invalid in (
    {"op": "__import__", "args": []},
    {"op": "test", "query": [], "params": {}},
    {"op": "compare", "relation": ["eq"], "left": 1, "right": 1},
    {"op": "all", "args": []},
):
    try:
        condition(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(f"accepted invalid declarative operation {invalid!r}")

quest = Quest("capture", "Capture", {"op": "true"}, 5)
progress = QuestManager([quest])
progress.complete("game1", "player1", quest.name)
assert progress.get_completed_quests("game1", "player2") == []
assert progress.get_completed_quests("game2", "player1") == []
assert progress.get_completed_quests("game1", "player1") == [quest]
print("G1 JSON schema/definitions and per-participant quest isolation probes passed")
