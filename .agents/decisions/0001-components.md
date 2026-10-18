---
status: accepted
---
# Shared Python game-state architecture

## Decision: Board, moves and rule evaluation are separate

`engine.model.game.board.Board` owns a rectangular matrix of optional piece objects, capture lists and placement/movement/replacement operations. Its built-in `setup_default_board` populates standard chess pieces on an 8×8 board. `engine.model.pieces` contains the concrete chess classes: Pawn, Rook, Horse, Bishop, Queen and King.

`engine.model.game.move.Move` stores origin, destination, move type, optional moving/captured/promoted pieces. `Move.validate` checks coordinate bounds (currently fixed at 8×8), origin occupancy and destination friendly-piece conflicts. `Move.execute` invokes `Board.move_piece` and optional destination replacement. Declared move types are metadata; execution is not a full general-purpose rules interpreter.

`MoveValidator` implements chess-oriented pseudo/legal moves, detection of king attacks/check, and checkmate/stalemate. `GameManager` owns `Board`, players with `1/-1` colors, active turn, `Timer`, `MoveValidator` and `GameLogger`. Its `make_move` validates the move and player, executes it, records it and changes the active side. Its state evaluation covers active-player timeout, checkmate, stalemate, check and in-progress. `save_log` remains a stub.

## Decision: supporting game state stays modular

`Timer` holds two time balances and exposes reset/tick/increment/expiry. `Quest` holds condition callback, completion flag and reward points; `engine.model.misc.quest_manager.QuestManager` stores/evaluates quests and may award completion to a `User`. `engine.model.users` holds identity/rating/history; `engine.model.misc` also implements coordinate notation, PGN-style metadata and chess export helpers; `GameLogger` tracks moves in memory with optional output.

## Data flow

`GameController.handle_square_click` → `GameManager.make_move` → `MoveValidator.is_valid_move` → `Move.execute` → `Board.move_piece` → `GameLogger.log_move` → change active player. The controller returns an action descriptor and current game state.

## Current limitation

The in-memory engine is chess-centric and its declarative checkers configuration does not itself provide complete English-draughts gameplay. No database or hosted service owns this state on #414.
