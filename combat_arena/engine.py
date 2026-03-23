"""
engine.py — The BattleEngine: core combat loop.

Depends ONLY on abstractions (Combatant, Action, TurnOrderStrategy) —
never on concrete implementations — satisfying DIP and OCP.
"""

from __future__ import annotations

from typing import List, Callable, Optional

from combat_arena.interfaces import Combatant, BattleContext, TurnOrderStrategy
from combat_arena.combatants import PlayerCombatant


class BattleEngine:
    """
    Runs rounds of combat until one side is eliminated.

    The engine is intentionally ignorant of the concrete combatant types,
    action implementations, and UI details.  All output is routed through
    a log_fn callback, keeping UI concerns separate (SRP).
    """

    def __init__(self, turn_strategy: TurnOrderStrategy,
                 log_fn: Callable[[str], None] = print) -> None:
        self._turn_strategy = turn_strategy
        self._log = log_fn

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------
    def run_battle(self, players: List[Combatant],
                   enemies: List[Combatant]) -> bool:
        """
        Execute the battle loop.

        Returns True if the players win, False if they lose.
        """
        round_num = 0

        while True:
            round_num += 1
            self._log(f"\n{'═' * 50}")
            self._log(f"  ⚔️  ROUND {round_num}")
            self._log(f"{'═' * 50}")
            self._print_status(players, enemies)

            # --- determine turn order for this round ----------------------
            all_alive = [c for c in players + enemies if c.is_alive]
            ordered = self._turn_strategy.determine_order(all_alive)

            for combatant in ordered:
                if not combatant.is_alive:
                    continue

                self._log(f"\n--- {combatant.name}'s Turn ---")

                # --- process start-of-turn effects ------------------------
                skip_turn = False
                for effect in combatant.status_effects:
                    msg = effect.on_turn_start(combatant)
                    if msg:
                        self._log(msg)
                    if effect.name == "Stun":
                        skip_turn = True

                if skip_turn:
                    # Tick effects and continue
                    self._tick_effects(combatant)
                    continue

                # --- combatant chooses and executes action -----------------
                allies = [c for c in (players if combatant in players else enemies) if c.is_alive]
                foes = [c for c in (enemies if combatant in players else players) if c.is_alive]

                ctx = BattleContext(
                    round_number=round_num,
                    allies=allies,
                    enemies=foes,
                    log_fn=self._log,
                )

                decision = combatant.choose_action(allies, foes, ctx)
                logs = decision.action.execute(combatant, decision.targets, ctx)
                for msg in logs:
                    self._log(msg)

                # --- handle cooldown for player special skills ------------
                if isinstance(combatant, PlayerCombatant):
                    from combat_arena.actions import SpecialSkillAction
                    if isinstance(decision.action, SpecialSkillAction):
                        combatant.start_cooldown()

                # --- tick effects at end of turn --------------------------
                self._tick_effects(combatant)

                # --- tick player cooldown ---------------------------------
                if isinstance(combatant, PlayerCombatant):
                    combatant.tick_cooldown()

                # --- check for battle end ---------------------------------
                if not any(p.is_alive for p in players):
                    self._log(f"\n{'💀' * 20}")
                    self._log("  DEFEAT — Your hero has fallen...")
                    self._log(f"{'💀' * 20}")
                    return False

                if not any(e.is_alive for e in enemies):
                    # Don't declare victory yet — caller handles backup waves
                    return True

        return True  # unreachable, keeps type-checkers happy

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------
    def _tick_effects(self, combatant: Combatant) -> None:
        """Tick all effects and remove expired ones."""
        for effect in combatant.status_effects:
            effect.tick()
            msg = effect.on_turn_end(combatant)
            if msg:
                self._log(msg)

        removal_msgs = combatant.remove_expired_effects()
        for msg in removal_msgs:
            self._log(msg)

    def _print_status(self, players: List[Combatant],
                      enemies: List[Combatant]) -> None:
        self._log("\n  📊 Status:")
        for p in players:
            effects_str = ""
            if p.status_effects:
                effects_str = " [" + ", ".join(e.name for e in p.status_effects) + "]"
            cd_str = ""
            if isinstance(p, PlayerCombatant) and p.cooldown > 0:
                cd_str = f" (Skill CD: {p.cooldown})"
            self._log(f"    🟢 {p.name}: {p.hp}/{p.max_hp} HP | ATK {p.attack} | DEF {p.defense} | SPD {p.speed}{cd_str}{effects_str}")

        for e in enemies:
            if e.is_alive:
                effects_str = ""
                if e.status_effects:
                    effects_str = " [" + ", ".join(ef.name for ef in e.status_effects) + "]"
                self._log(f"    🔴 {e.name}: {e.hp}/{e.max_hp} HP | ATK {e.attack} | DEF {e.defense} | SPD {e.speed}{effects_str}")
