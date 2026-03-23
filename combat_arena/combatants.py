"""
combatants.py — Concrete Combatant implementations.

Player characters delegate action choice to the CLI.
Enemy characters always use BasicAttack on the player.
"""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from combat_arena.interfaces import Combatant, Action, ActionDecision, BattleContext
from combat_arena.actions import BasicAttack
from combat_arena.skills import ShieldBash, ArcaneBlast

if TYPE_CHECKING:
    from combat_arena.interfaces import Item


# ═══════════════════════════════════════════════════════════════════════════
#  Player Combatants
# ═══════════════════════════════════════════════════════════════════════════

class PlayerCombatant(Combatant):
    """
    Base for all player-controlled characters.  Holds an inventory,
    a special skill, and a cooldown counter.

    Action selection is delegated to an external callback (the CLI) which
    is injected via set_action_callback().
    """

    COOLDOWN_TURNS = 3

    def __init__(self, name: str, max_hp: int, attack: int, defense: int,
                 speed: int, special_skill: Action) -> None:
        super().__init__(name, max_hp, attack, defense, speed)
        self.special_skill = special_skill
        self._cooldown: int = 0          # 0 = ready
        self._items: List["Item"] = []
        self._action_callback = None     # set by CLI

    # --- item management -----------------------------------------------------
    @property
    def items(self) -> List["Item"]:
        return list(self._items)

    def add_item(self, item: "Item") -> None:
        self._items.append(item)

    def remove_item(self, item: "Item") -> None:
        self._items.remove(item)

    # --- cooldown management -------------------------------------------------
    @property
    def cooldown(self) -> int:
        return self._cooldown

    @property
    def skill_ready(self) -> bool:
        return self._cooldown == 0

    def start_cooldown(self) -> None:
        self._cooldown = self.COOLDOWN_TURNS

    def tick_cooldown(self) -> None:
        if self._cooldown > 0:
            self._cooldown -= 1

    # --- callback for action choice ------------------------------------------
    def set_action_callback(self, callback) -> None:
        """
        Inject the CLI callback.  Signature:
            callback(player, allies, enemies, battle_ctx) -> ActionDecision
        """
        self._action_callback = callback

    def choose_action(self, allies: List[Combatant], enemies: List[Combatant],
                      battle_ctx: BattleContext) -> ActionDecision:
        if self._action_callback is None:
            raise RuntimeError("No action callback set for player!")
        return self._action_callback(self, allies, enemies, battle_ctx)

    def __repr__(self) -> str:
        cd_str = f" CD:{self._cooldown}" if self._cooldown > 0 else ""
        return f"{self._name}(HP={self._hp}/{self._max_hp}{cd_str})"


class Warrior(PlayerCombatant):
    """Sturdy melee fighter with Shield Bash."""

    def __init__(self) -> None:
        super().__init__(
            name="Warrior",
            max_hp=260, attack=40, defense=20, speed=30,
            special_skill=ShieldBash(),
        )


class Wizard(PlayerCombatant):
    """Glass-cannon caster with Arcane Blast (AoE)."""

    def __init__(self) -> None:
        super().__init__(
            name="Wizard",
            max_hp=200, attack=50, defense=10, speed=20,
            special_skill=ArcaneBlast(),
        )

    @property
    def attack(self) -> int:
        """Wizard's attack can be boosted by Arcane Blast kills."""
        return self._base_attack


# ═══════════════════════════════════════════════════════════════════════════
#  Enemy Combatants
# ═══════════════════════════════════════════════════════════════════════════

class EnemyCombatant(Combatant):
    """
    Base for all AI-controlled enemies.  AI always uses BasicAttack on
    the player (first alive ally).
    """

    def choose_action(self, allies: List[Combatant], enemies: List[Combatant],
                      battle_ctx: BattleContext) -> ActionDecision:
        # 'allies' from this enemy's perspective are other enemies,
        # 'enemies' from this enemy's perspective are players.
        target = next((e for e in enemies if e.is_alive), None)
        if target is None:
            target = enemies[0]  # fallback, shouldn't happen
        return ActionDecision(action=BasicAttack(), targets=[target])


class Goblin(EnemyCombatant):
    """Sneaky little creature."""

    _instance_count = 0

    def __init__(self) -> None:
        Goblin._instance_count += 1
        suffix = f" {Goblin._instance_count}" if Goblin._instance_count > 1 else ""
        super().__init__(
            name=f"Goblin{suffix}",
            max_hp=55, attack=35, defense=15, speed=25,
        )

    @classmethod
    def reset_count(cls) -> None:
        cls._instance_count = 0


class Wolf(EnemyCombatant):
    """Fast and ferocious beast."""

    _instance_count = 0

    def __init__(self) -> None:
        Wolf._instance_count += 1
        suffix = f" {Wolf._instance_count}" if Wolf._instance_count > 1 else ""
        super().__init__(
            name=f"Wolf{suffix}",
            max_hp=40, attack=45, defense=5, speed=35,
        )

    @classmethod
    def reset_count(cls) -> None:
        cls._instance_count = 0
