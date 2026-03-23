"""
actions.py — Concrete Action implementations for player turns.
"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from combat_arena.interfaces import Action, Combatant, BattleContext
from combat_arena.effects import DefenseBoost

if TYPE_CHECKING:
    pass


class BasicAttack(Action):
    """Standard melee attack against a single target."""

    @property
    def name(self) -> str:
        return "Basic Attack"

    def execute(self, user: Combatant, targets: List[Combatant],
                battle_ctx: BattleContext) -> List[str]:
        target = targets[0]
        if target.has_effect("SmokeBomb"):
            dmg = 0
        else:
            dmg = max(0, user.attack - target.defense)
        target.take_damage(dmg)
        logs = [f"  ⚔️  {user.name} attacks {target.name} for {dmg} damage! (HP: {target.hp}/{target.max_hp})"]
        if not target.is_alive:
            logs.append(f"  💀 {target.name} has been slain!")
        return logs


class Defend(Action):
    """Raise guard: +10 Defense for the current and next turn (2 turns)."""

    @property
    def name(self) -> str:
        return "Defend"

    def execute(self, user: Combatant, targets: List[Combatant],
                battle_ctx: BattleContext) -> List[str]:
        msg = user.add_status_effect(DefenseBoost(bonus=10, duration=2))
        return [msg]


class UseItem(Action):
    """
    Wrapper action that delegates to an Item's use() method.
    The item reference is set before execute() is called.
    """

    def __init__(self, item) -> None:
        self._item = item

    @property
    def name(self) -> str:
        return f"Use {self._item.name}"

    def execute(self, user: Combatant, targets: List[Combatant],
                battle_ctx: BattleContext) -> List[str]:
        return self._item.use(user, battle_ctx)


class SpecialSkillAction(Action):
    """
    Wrapper action that delegates to the combatant's special_skill.
    Manages the 3-turn cooldown timer.
    """

    def __init__(self, skill: Action) -> None:
        self._skill = skill

    @property
    def name(self) -> str:
        return self._skill.name

    def execute(self, user: Combatant, targets: List[Combatant],
                battle_ctx: BattleContext) -> List[str]:
        # Start the cooldown (handled by the combatant after this call)
        return self._skill.execute(user, targets, battle_ctx)
