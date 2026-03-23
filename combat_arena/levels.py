"""
levels.py — Level definitions with backup-wave spawning logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from combat_arena.interfaces import Combatant
from combat_arena.combatants import Goblin, Wolf


@dataclass
class LevelDefinition:
    """
    Describes the enemies for one level.

    initial_wave_factory:  callable that returns the first batch of enemies.
    backup_wave_factory:   callable that returns backup enemies (spawned after
                           the initial wave is fully eliminated).  May be None.
    """
    number: int
    name: str
    initial_wave_factory: Callable[[], List[Combatant]]
    backup_wave_factory: Callable[[], List[Combatant]] | None = None


def _reset_enemy_counters() -> None:
    """Reset instance counters so naming restarts each level."""
    Goblin.reset_count()
    Wolf.reset_count()


def get_levels() -> List[LevelDefinition]:
    """Return the three difficulty levels."""
    return [
        LevelDefinition(
            number=1,
            name="Easy — Goblin Raid",
            initial_wave_factory=lambda: (_reset_enemy_counters(), [Goblin(), Goblin(), Goblin()])[1],
            backup_wave_factory=None,
        ),
        LevelDefinition(
            number=2,
            name="Medium — Forest Ambush",
            initial_wave_factory=lambda: (_reset_enemy_counters(), [Goblin(), Wolf()])[1],
            backup_wave_factory=lambda: [Wolf(), Wolf()],
        ),
        LevelDefinition(
            number=3,
            name="Hard — The Gauntlet",
            initial_wave_factory=lambda: (_reset_enemy_counters(), [Goblin(), Goblin()])[1],
            backup_wave_factory=lambda: [Goblin(), Wolf(), Wolf()],
        ),
    ]
