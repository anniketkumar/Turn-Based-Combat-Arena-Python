"""
skills.py — Special Skill implementations (concrete Action subclasses).
"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from combat_arena.interfaces import Action, Combatant, BattleContext
from combat_arena.effects import StunEffect

if TYPE_CHECKING:
    pass


def _compute_damage(attacker: Combatant, defender: Combatant) -> int:
    """Standard damage formula shared by skills and basic attacks."""
    if defender.has_effect("SmokeBomb"):
        return 0
    return max(0, attacker.attack - defender.defense)


class ShieldBash(Action):
    """
    Warrior special: deals BasicAttack damage to a single target and
    stuns it for 2 turns (current + next).
    """

    @property
    def name(self) -> str:
        return "Shield Bash"

    def execute(self, user: Combatant, targets: List[Combatant],
                battle_ctx: BattleContext) -> List[str]:
        logs: List[str] = []
        target = targets[0]
        dmg = _compute_damage(user, target)
        target.take_damage(dmg)
        logs.append(f"  🛡️⚔️  {user.name} uses Shield Bash on {target.name} for {dmg} damage!")

        if target.is_alive and not target.has_effect("Stun"):
            msg = target.add_status_effect(StunEffect(duration=2))
            logs.append(msg)
        elif not target.is_alive:
            logs.append(f"  💀 {target.name} has been slain!")

        return logs


class ArcaneBlast(Action):
    """
    Wizard special: deals BasicAttack damage to ALL active enemies.
    Each enemy killed adds +10 to the Wizard's Attack for the rest of the level.
    """

    @property
    def name(self) -> str:
        return "Arcane Blast"

    def execute(self, user: Combatant, targets: List[Combatant],
                battle_ctx: BattleContext) -> List[str]:
        logs: List[str] = []
        logs.append(f"  🔮✨ {user.name} channels Arcane Blast!")
        kills = 0

        alive_enemies = [t for t in targets if t.is_alive]
        for enemy in alive_enemies:
            dmg = _compute_damage(user, enemy)
            enemy.take_damage(dmg)
            logs.append(f"     → {enemy.name} takes {dmg} damage! (HP: {enemy.hp}/{enemy.max_hp})")
            if not enemy.is_alive:
                logs.append(f"     💀 {enemy.name} has been slain!")
                kills += 1

        if kills > 0:
            bonus = kills * 10
            user._base_attack += bonus
            logs.append(f"  ⬆️  {user.name}'s Attack increased by {bonus}! (Now {user.attack})")

        return logs
