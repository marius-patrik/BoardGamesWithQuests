"""Keep the cleanroom source tree authoritative: no root-level shadow packages."""

from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[2]


def test_single_source_tree_for_model_view_controller():
    for package in ("model", "view", "controller"):
        assert not (ROOT / package).exists(), f"Obsolete root-level {package}/ shadows src/{package}/"
        assert (ROOT / "src" / package / "__init__.py").is_file()


def test_production_piece_module_not_shadowed_by_teacher_skeleton():
    spec = importlib.util.find_spec("model.piece")
    assert spec is not None and spec.origin is not None
    assert Path(spec.origin).resolve() == ROOT / "src" / "model" / "piece.py"
    assert importlib.util.find_spec("model.figurka") is None
