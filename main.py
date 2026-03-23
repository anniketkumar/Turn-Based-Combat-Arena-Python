"""
main.py — Entry point for the Turn-Based Combat Arena.

Orchestrates character selection, item picking, and the level loop.
"""

import sys
import os

# Ensure the project root is on sys.path (handles directories with special chars)
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from combat_arena.cli import (
    clear_screen,
    select_character,
    select_item,
    show_level_intro,
    show_backup_wave,
    show_level_victory,
    show_game_victory,
    show_game_over,
    player_action_callback,
)
from combat_arena.engine import BattleEngine
from combat_arena.levels import get_levels
from combat_arena.turn_order import SpeedBasedTurnOrder


def main() -> None:
    clear_screen()

    # --- Character & item selection ----------------------------------------
    player = select_character()
    item = select_item()
    player.add_item(item)

    # Inject CLI action callback into the player
    player.set_action_callback(player_action_callback)

    # --- Engine setup (depends only on abstractions) -----------------------
    engine = BattleEngine(turn_strategy=SpeedBasedTurnOrder())

    # --- Level loop --------------------------------------------------------
    levels = get_levels()
    for level_def in levels:
        # Spawn initial wave
        enemies = level_def.initial_wave_factory()
        show_level_intro(level_def.number, level_def.name, enemies)

        # Run battle for initial wave
        won = engine.run_battle(players=[player], enemies=enemies)

        if not won:
            show_game_over()
            return

        # Backup wave?
        if level_def.backup_wave_factory is not None:
            backup = level_def.backup_wave_factory()
            show_backup_wave(backup)
            enemies.extend(backup)
            won = engine.run_battle(players=[player], enemies=backup)
            if not won:
                show_game_over()
                return

        show_level_victory(level_def.number)

    # --- All levels cleared ------------------------------------------------
    show_game_victory()


if __name__ == "__main__":
    main()
