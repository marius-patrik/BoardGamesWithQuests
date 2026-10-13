"""Targeted G1 schema probes; not the permanent gameplay test suite."""

import json
from pathlib import Path

from engine.model.game.conditions import ConditionEvaluator, QueryResolutionError
from engine.model.game.configuration import board_from_definition, load_definition
from engine.model.game.hooks import HookInterpreter
from engine.model.game.quest import Quest
from engine.model.game.schema import condition, validate_hooks
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

fixture = json.loads((Path(__file__).parent / "fixtures/g1_hooks.json").read_text("utf-8"))
rules = fixture["rules"]
quests = fixture["quests"]
when = rules[0]["when"]
queries = {
    "capture_paths": lambda params: params["player"] == "active",
    "capture_count": lambda params: 2 if params["candidate"] == "move" else 0,
}
engine_queries = ConditionEvaluator(queries)
assert engine_queries.evaluate(when)
assert not engine_queries.evaluate({"op": "not", "arg": when})
assert engine_queries.evaluate({"op": "any", "args": [{"op": "false"}, when]})
try:
    ConditionEvaluator({}).evaluate(when)
except QueryResolutionError:
    pass
else:
    raise AssertionError("missing condition primitive must fail closed")

validate_hooks(rules, quests)
matched = HookInterpreter(rules, queries).evaluate("permits_move")
assert matched.matched_rule_ids == ("capture",)
assert [effect.op for effect in matched.effects] == ["deny"]
assert HookInterpreter(rules, queries).evaluate("outcome").effects == ()

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
