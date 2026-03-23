"""
cli.py — Command-Line Interface for the Combat Arena.

All user I/O is isolated here (SRP).  The CLI knows about the domain
model but the domain model never imports the CLI.
"""

from __future__ import annotations

import os
from typing import List, Optional, TYPE_CHECKING

from combat_arena.interfaces import Combatant, ActionDecision, BattleContext
from combat_arena.combatants import PlayerCombatant, Warrior, Wizard
from combat_arena.actions import BasicAttack, Defend, UseItem, SpecialSkillAction
from combat_arena.items import Potion, PowerStone, SmokeBomb
from combat_arena.skills import ArcaneBlast

if TYPE_CHECKING:
    from combat_arena.interfaces import Item


# ═══════════════════════════════════════════════════════════════════════════
#  Utility helpers
# ═══════════════════════════════════════════════════════════════════════════

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_banner(text: str, width: int = 50) -> None:
    print()
    print("╔" + "═" * width + "╗")
    print("║" + text.center(width) + "║")
    print("╚" + "═" * width + "╝")


def prompt_int(prompt: str, lo: int, hi: int) -> int:
    """Prompt for an integer in [lo, hi], re-asking on bad input."""
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if lo <= val <= hi:
                return val
        except ValueError:
            pass
        print(f"  ⚠️  Please enter a number between {lo} and {hi}.")


# ═══════════════════════════════════════════════════════════════════════════
#  Character selection
# ═══════════════════════════════════════════════════════════════════════════

def select_character() -> PlayerCombatant:
    print_banner("⚔️  TURN-BASED COMBAT ARENA  ⚔️")
    print("\n  Choose your hero:\n")
    print("  1) 🗡️  Warrior — HP 260 | ATK 40 | DEF 20 | SPD 30")
    print("        Skill: Shield Bash (damage + stun)")
    print()
    print("  2) 🔮 Wizard  — HP 200 | ATK 50 | DEF 10 | SPD 20")
    print("        Skill: Arcane Blast (AoE + ATK bonus per kill)")
    print()

    choice = prompt_int("  ➤ Enter 1 or 2: ", 1, 2)
    player = Warrior() if choice == 1 else Wizard()
    print(f"\n  ✅ You selected {player.name}!")
    return player


# ═══════════════════════════════════════════════════════════════════════════
#  Item selection
# ═══════════════════════════════════════════════════════════════════════════

AVAILABLE_ITEMS = [
    ("Potion", "Restores 100 HP.", Potion),
    ("Power Stone", "Fires your Special Skill for free (no cooldown cost).", PowerStone),
    ("Smoke Bomb", "Enemies deal 0 damage for 2 turns.", SmokeBomb),
]


def select_item() -> "Item":
    print("\n  Choose one item to bring into battle:\n")
    for i, (name, desc, _) in enumerate(AVAILABLE_ITEMS, start=1):
        print(f"  {i}) {name} — {desc}")
    print()

    choice = prompt_int("  ➤ Pick an item (1-3): ", 1, len(AVAILABLE_ITEMS))
    _, _, item_cls = AVAILABLE_ITEMS[choice - 1]
    item = item_cls()
    print(f"\n  ✅ You packed a {item.name}!")
    return item


# ═══════════════════════════════════════════════════════════════════════════
#  Action selection callback  (injected into PlayerCombatant)
# ═══════════════════════════════════════════════════════════════════════════

def player_action_callback(player: PlayerCombatant,
                           allies: List[Combatant],
                           enemies: List[Combatant],
                           battle_ctx: BattleContext) -> ActionDecision:
    """
    Present the action menu to the human and return an ActionDecision.
    """
    alive_enemies = [e for e in enemies if e.is_alive]

    while True:
        print(f"\n  {player.name}'s turn!  Choose an action:")
        print("  1) ⚔️  Basic Attack")
        print("  2) 🛡️  Defend")

        has_items = len(player.items) > 0
        if has_items:
            items_str = ", ".join(i.name for i in player.items)
            print(f"  3) 🎒 Use Item  [{items_str}]")
        else:
            print("  3) 🎒 Use Item  [empty]")

        if player.skill_ready:
            print(f"  4) ✨ {player.special_skill.name}  [READY]")
        else:
            print(f"  4) ✨ {player.special_skill.name}  [CD: {player.cooldown} turns]")

        choice = prompt_int("  ➤ Action (1-4): ", 1, 4)

        # --- Basic Attack ---
        if choice == 1:
            target = _choose_target(alive_enemies)
            return ActionDecision(action=BasicAttack(), targets=[target])

        # --- Defend ---
        if choice == 2:
            return ActionDecision(action=Defend(), targets=[player])

        # --- Use Item ---
        if choice == 3:
            if not has_items:
                print("  ⚠️  You have no items left!")
                continue
            item = _choose_item(player)
            if item is None:
                continue  # player cancelled
            player.remove_item(item)
            return ActionDecision(action=UseItem(item), targets=[player])

        # --- Special Skill ---
        if choice == 4:
            if not player.skill_ready:
                print(f"  ⚠️  {player.special_skill.name} is on cooldown ({player.cooldown} turns remaining).")
                continue

            # Determine targets
            if isinstance(player.special_skill, ArcaneBlast):
                targets = alive_enemies
            else:
                targets = [_choose_target(alive_enemies)]

            return ActionDecision(
                action=SpecialSkillAction(player.special_skill),
                targets=targets,
            )


def _choose_target(enemies: List[Combatant]) -> Combatant:
    if len(enemies) == 1:
        print(f"  🎯 Target: {enemies[0].name}")
        return enemies[0]

    print("\n  Choose your target:")
    for i, e in enumerate(enemies, start=1):
        effects_str = ""
        if e.status_effects:
            effects_str = " [" + ", ".join(ef.name for ef in e.status_effects) + "]"
        print(f"    {i}) {e.name}  (HP: {e.hp}/{e.max_hp}){effects_str}")

    idx = prompt_int(f"  ➤ Target (1-{len(enemies)}): ", 1, len(enemies))
    return enemies[idx - 1]


def _choose_item(player: PlayerCombatant) -> Optional["Item"]:
    items = player.items
    print("\n  Choose an item to use:")
    for i, item in enumerate(items, start=1):
        print(f"    {i}) {item.name} — {item.description}")
    print(f"    0) Cancel")

    choice = prompt_int(f"  ➤ Item (0-{len(items)}): ", 0, len(items))
    if choice == 0:
        return None
    return items[choice - 1]


# ═══════════════════════════════════════════════════════════════════════════
#  Level transition message
# ═══════════════════════════════════════════════════════════════════════════

def show_level_intro(level_num: int, level_name: str,
                     enemies: List[Combatant]) -> None:
    print_banner(f"LEVEL {level_num} — {level_name}")
    print("\n  Enemies appear:")
    for e in enemies:
        print(f"    🔴 {e.name}  (HP: {e.hp} | ATK: {e.attack} | DEF: {e.defense} | SPD: {e.speed})")
    print()


def show_backup_wave(enemies: List[Combatant]) -> None:
    print()
    print("  🚨 BACKUP WAVE INCOMING! 🚨")
    print("  New enemies rush onto the battlefield:")
    for e in enemies:
        print(f"    🔴 {e.name}  (HP: {e.hp} | ATK: {e.attack} | DEF: {e.defense} | SPD: {e.speed})")
    print()


def show_level_victory(level_num: int) -> None:
    print(f"\n  🎉 Level {level_num} CLEAR!\n")


def show_game_victory() -> None:
    print_banner("🏆  VICTORY — YOU CONQUERED THE ARENA!  🏆")


def show_game_over() -> None:
    print_banner("💀  GAME OVER  💀")
    print("  Better luck next time, warrior.\n")
