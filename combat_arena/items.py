"""
items.py — Concrete Item implementations.
"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from combat_arena.interfaces import Item, Combatant, BattleContext
from combat_arena.effects import SmokeBombEffect

if TYPE_CHECKING:
    pass


class Potion(Item):
    """Heals the owner for 100 HP (cannot exceed Max HP)."""

    @property
    def name(self) -> str:
        return "Potion"

    @property
    def description(self) -> str:
        return "Restores 100 HP."

    def use(self, owner: Combatant, battle_ctx: BattleContext) -> List[str]:
        healed = owner.heal(100)
        return [f"  🧪 {owner.name} drinks a Potion and recovers {healed} HP! (HP: {owner.hp}/{owner.max_hp})"]


class PowerStone(Item):
    """
    Triggers the owner's class Special Skill immediately for free,
    WITHOUT starting or altering the standard 3-turn cooldown timer.
    """

    @property
    def name(self) -> str:
        return "Power Stone"

    @property
    def description(self) -> str:
        return "Fires your Special Skill for free (no cooldown cost)."

    def use(self, owner: Combatant, battle_ctx: BattleContext) -> List[str]:
        logs: List[str] = [f"  💎 {owner.name} crushes a Power Stone!"]
        # Owner must have a special_skill attribute (PlayerCombatant does)
        skill = getattr(owner, "special_skill", None)
        if skill is None:
            logs.append("  ❌ No special skill available.")
            return logs

        # Determine targets for the skill
        from combat_arena.skills import ArcaneBlast
        if isinstance(skill, ArcaneBlast):
            targets = [e for e in battle_ctx.enemies if e.is_alive]
        else:
            # Single-target: pick the first alive enemy
            targets = [e for e in battle_ctx.enemies if e.is_alive][:1]

        skill_logs = skill.execute(owner, targets, battle_ctx)
        logs.extend(skill_logs)
        return logs


class SmokeBomb(Item):
    """Enemy attacks deal 0 damage for the current and next turn (2 turns)."""

    @property
    def name(self) -> str:
        return "Smoke Bomb"

    @property
    def description(self) -> str:
        return "Enemies deal 0 damage for 2 turns."

    def use(self, owner: Combatant, battle_ctx: BattleContext) -> List[str]:
        logs: List[str] = []
        msg = owner.add_status_effect(SmokeBombEffect(duration=2))
        logs.append(msg)
        return logs
