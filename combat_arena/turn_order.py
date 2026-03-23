"""
turn_order.py — Turn-order strategy implementations.
"""

from __future__ import annotations

from typing import List

from combat_arena.interfaces import Combatant, TurnOrderStrategy


class SpeedBasedTurnOrder(TurnOrderStrategy):
    """Combatants act in descending order of their Speed stat."""

    def determine_order(self, combatants: List[Combatant]) -> List[Combatant]:
        return sorted(combatants, key=lambda c: c.speed, reverse=True)
