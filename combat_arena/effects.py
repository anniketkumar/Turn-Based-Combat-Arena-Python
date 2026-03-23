"""
effects.py — Concrete StatusEffect implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from combat_arena.interfaces import StatusEffect

if TYPE_CHECKING:
    from combat_arena.interfaces import Combatant


class StunEffect(StatusEffect):
    """Prevents the target from acting for the duration."""

    def __init__(self, duration: int = 2) -> None:
        self._remaining = duration

    @property
    def name(self) -> str:
        return "Stun"

    @property
    def remaining_turns(self) -> int:
        return self._remaining

    def on_apply(self, target: "Combatant") -> str:
        return f"  ⚡ {target.name} is STUNNED for {self._remaining} turn(s)!"

    def on_turn_start(self, target: "Combatant") -> Optional[str]:
        return f"  💫 {target.name} is stunned and cannot act!"

    def on_turn_end(self, target: "Combatant") -> Optional[str]:
        return None

    def on_remove(self, target: "Combatant") -> Optional[str]:
        return f"  ✅ {target.name} is no longer stunned."

    def tick(self) -> None:
        self._remaining -= 1


class DefenseBoost(StatusEffect):
    """Temporarily increases the combatant's defense."""

    def __init__(self, bonus: int = 10, duration: int = 2) -> None:
        self._remaining = duration
        self.defense_bonus = bonus

    @property
    def name(self) -> str:
        return "DefenseBoost"

    @property
    def remaining_turns(self) -> int:
        return self._remaining

    def on_apply(self, target: "Combatant") -> str:
        return f"  🛡️  {target.name} raises their guard! Defense +{self.defense_bonus} for {self._remaining} turn(s)."

    def on_turn_start(self, target: "Combatant") -> Optional[str]:
        return None

    def on_turn_end(self, target: "Combatant") -> Optional[str]:
        return None

    def on_remove(self, target: "Combatant") -> Optional[str]:
        self.defense_bonus = 0
        return f"  🛡️  {target.name}'s defense boost fades."

    def tick(self) -> None:
        self._remaining -= 1


class SmokeBombEffect(StatusEffect):
    """
    Applied to the *player*.  While active, all incoming enemy damage is reduced
    to 0.  The damage check is handled in the damage formula (engine-side) by
    inspecting whether the defender has this effect.
    """

    def __init__(self, duration: int = 2) -> None:
        self._remaining = duration

    @property
    def name(self) -> str:
        return "SmokeBomb"

    @property
    def remaining_turns(self) -> int:
        return self._remaining

    def on_apply(self, target: "Combatant") -> str:
        return f"  💨 {target.name} is shrouded in smoke! Enemies deal 0 damage for {self._remaining} turn(s)."

    def on_turn_start(self, target: "Combatant") -> Optional[str]:
        return f"  💨 {target.name} is hidden in smoke — incoming attacks deal 0 damage."

    def on_turn_end(self, target: "Combatant") -> Optional[str]:
        return None

    def on_remove(self, target: "Combatant") -> Optional[str]:
        return f"  💨 The smoke around {target.name} dissipates."

    def tick(self) -> None:
        self._remaining -= 1
