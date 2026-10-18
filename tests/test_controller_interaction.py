"""Controller behavior remains available after the server package migration."""

from server.engine.controller.controller import GameController
from server.engine.controller.window_controller import WindowController


def test_select_and_move_via_restored_game_controller():
    controller = GameController()

    # The first turn belongs to White, so selecting a Black piece is rejected.
    invalid = controller.handle_square_click((6, 4))
    assert invalid["action"] == "none"
    assert controller.selected_square is None

    selected = controller.handle_square_click((1, 4))
    assert selected["action"] == "selected"
    assert (2, 4) in selected["valid_moves"]
    assert controller.selected_square == (1, 4)

    # The retained controller still commits a legal move through GameManager.
    moved = controller.handle_square_click((2, 4))
    assert moved["action"] == "moved"
    assert moved["success"] is True
    assert controller.game_manager.board.get_piece_at((1, 4)) is None
    assert controller.game_manager.board.get_piece_at((2, 4)) is not None
    assert controller.game_manager.active_player == -1
    assert controller.selected_square is None


def test_legacy_window_controller_remains_separate_from_http_and_view():
    window = WindowController(GameController())
    assert not window.is_running
    window.start()
    assert window.is_running
    window.show_dialog("Test status")
    assert window.active_dialog == "Test status"
    window.close_dialog()
    assert window.active_dialog is None
    window.stop()
    assert not window.is_running
