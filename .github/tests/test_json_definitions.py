"""Acceptance of recovered, strictly JSON-only versioned built-in game definitions."""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from model.definition import ConfigurationError, load_bundled_definition, parse_definition_json
from model.schema import thaw_json


def test_bundled_chess_and_english_draughts_have_valid_version_two_definitions():
    chess = load_bundled_definition("chess")
    english = load_bundled_definition("checkers")
    assert chess.name == "chess"
    assert english.name == "english_draughts"
    assert chess.board["rows"] == english.board["rows"] == 8
    assert chess.board["columns"] == english.board["columns"] == 8
    assert chess.rules
    assert english.rules
    # Definitions are preserved from the archived schema and are not release-certified.
    assert chess.playable is False
    assert english.playable is False


def test_built_in_definition_is_immutable_and_has_detached_serialization():
    definition = load_bundled_definition("checkers")
    with pytest.raises(TypeError):
        definition.board["rows"] = 10
    first = thaw_json(definition.board)
    first["rows"] = 10
    assert definition.board["rows"] == 8
    assert thaw_json(definition.board)["rows"] == 8


def test_rejects_duplicate_json_properties_including_nested_objects():
    definition = load_bundled_definition("checkers")
    document = '{"schema_version":2,"schema_version":2}'
    with pytest.raises(ConfigurationError, match="duplicate JSON field"):
        parse_definition_json(document)
    assert definition.rules


@pytest.mark.parametrize(
    "bad",
    [
        "{not valid JSON",
        '{"rules":[]}',
        '{"schema_version": 2, "python": "exec(1)"}',
        '{"schema_version": NaN}',
    ],
)
def test_rejects_malformed_unknown_and_executable_json(bad):
    with pytest.raises(ConfigurationError):
        parse_definition_json(bad)


def test_rejects_unrecognized_python_rule_source_in_trusted_definition():
    config = load_bundled_definition("checkers")
    data = {
        "schema_version": 2,
        "name": config.name,
        "title": config.title,
        "default": config.default,
        "playable": config.playable,
        "board": thaw_json(config.board),
        "pieces": thaw_json(config.pieces),
        "clock": thaw_json(config.clock),
        "exports": list(config.exports),
        "appearance": thaw_json(config.appearance),
        "rules": thaw_json(config.rules),
        "quests": thaw_json(config.quests),
    }
    injection = deepcopy(data)
    injection["rules"][0]["python"] = "import os"
    with pytest.raises(ConfigurationError):
        parse_definition_json(json.dumps(injection))
    # The original and the next parse are unaffected by the attempted injection.
    assert parse_definition_json(json.dumps(data)).name == config.name


def test_capture_policy_validates_declared_bounded_geometry():
    from model.capture_policy import CapturePolicy
    from model.conditions import QueryResolutionError

    accepted = {
        "flying": False,
        "land_anywhere": False,
        "deferred_removal": False,
        "max_nodes": 4096,
    }
    assert CapturePolicy.from_json(accepted).max_nodes == 4096
    with pytest.raises(QueryResolutionError):
        CapturePolicy.from_json({**accepted, "max_nodes": 10001})
    with pytest.raises(QueryResolutionError):
        CapturePolicy.from_json({**accepted, "land_anywhere": True})


@pytest.mark.parametrize(
    "unsafe", ["../chess", "chess/__init__", ".", "__pycache__", "", "a" * 65, "CHECKERS"]
)
def test_bundled_game_selector_rejects_paths_and_executable_module_names(unsafe):
    with pytest.raises(ConfigurationError):
        load_bundled_definition(unsafe)


def test_loader_does_not_import_variant_python_package(monkeypatch):
    import importlib

    original = importlib.import_module

    def guarded_import(name, package=None):
        if name == "games.checkers":
            pytest.fail("reading JSON must not import executable game configuration")
        return original(name, package)

    monkeypatch.setattr(importlib, "import_module", guarded_import)
    game = load_bundled_definition("checkers")
    assert game.name == "english_draughts"
