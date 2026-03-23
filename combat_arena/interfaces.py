"""
interfaces.py — Abstract Base Classes for the Combat Arena.

Defines the core abstractions that the rest of the system depends on,
enabling the Open/Closed and Dependency Inversion principles.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from combat_arena.interfaces import Combatant


# ---------------------------------------------------------------------------
# Status Effect
# ---------------------------------------------------------------------------
class StatusEffect(ABC):
    """A temporary modifier applied to a Combatant."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the effect."""

    @property
    @abstractmethod
    def remaining_turns(self) -> int:
        """Number of turns the effect will still be active."""

    @property
    def is_expired(self) -> bool:
        return self.remaining_turns <= 0

    @abstractmethod
    def on_apply(self, target: "Combatant") -> str:
        """Called once when the effect is first applied.  Returns a log message."""

    @abstractmethod
    def on_turn_start(self, target: "Combatant") -> Optional[str]:
        """Called at the start of the target's turn.  Returns a log message or None."""

    @abstractmethod
    def on_turn_end(self, target: "Combatant") -> Optional[str]:
        """Called at the end of the target's turn.  Returns a log message or None."""

    @abstractmethod
    def on_remove(self, target: "Combatant") -> Optional[str]:
        """Called when the effect expires.  Returns a log message or None."""

    @abstractmethod
    def tick(self) -> None:
        """Decrease the remaining duration by one turn."""


# ---------------------------------------------------------------------------
# Combatant
# ---------------------------------------------------------------------------
class Combatant(ABC):
    """
    Abstract base for any entity that participates in combat.

    Both Player characters and Enemy characters derive from this,
    satisfying the Liskov Substitution Principle.
    """

    def __init__(self, name: str, max_hp: int, attack: int, defense: int, speed: int) -> None:
        self._name = name
        self._max_hp = max_hp
        self._hp = max_hp
        self._base_attack = attack
        self._base_defense = defense
        self._speed = speed
        self._status_effects: List[StatusEffect] = []

    # --- read-only properties ------------------------------------------------
    @property
    def name(self) -> str:
        return self._name

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def base_attack(self) -> int:
        return self._base_attack

    @property
    def attack(self) -> int:
        return self._base_attack

    @property
    def base_defense(self) -> int:
        return self._base_defense

    @property
    def defense(self) -> int:
        """Effective defense, accounting for status effects like DefenseBoost."""
        bonus = sum(
            getattr(e, "defense_bonus", 0) for e in self._status_effects
        )
        return self._base_defense + bonus

    @property
    def speed(self) -> int:
        return self._speed

    @property
    def status_effects(self) -> List[StatusEffect]:
        return list(self._status_effects)

    @property
    def is_alive(self) -> bool:
        return self._hp > 0

    # --- mutators ------------------------------------------------------------
    def take_damage(self, amount: int) -> int:
        """Apply *raw* damage (already computed).  Returns actual damage dealt."""
        actual = min(amount, self._hp)
        self._hp = max(0, self._hp - amount)
        return actual

    def heal(self, amount: int) -> int:
        """Restore HP up to max_hp.  Returns actual amount healed."""
        before = self._hp
        self._hp = min(self._max_hp, self._hp + amount)
        return self._hp - before

    def add_status_effect(self, effect: StatusEffect) -> str:
        """Attach a status effect and call its on_apply hook."""
        self._status_effects.append(effect)
        return effect.on_apply(self)

    def remove_expired_effects(self) -> List[str]:
        """Remove all expired effects and collect log messages."""
        msgs: List[str] = []
        still_active: List[StatusEffect] = []
        for e in self._status_effects:
            if e.is_expired:
                msg = e.on_remove(self)
                if msg:
                    msgs.append(msg)
            else:
                still_active.append(e)
        self._status_effects = still_active
        return msgs

    def has_effect(self, effect_name: str) -> bool:
        return any(e.name == effect_name for e in self._status_effects)

    def get_effect(self, effect_name: str) -> Optional[StatusEffect]:
        for e in self._status_effects:
            if e.name == effect_name:
                return e
        return None

    # --- abstract interface --------------------------------------------------
    @abstractmethod
    def choose_action(self, allies: List["Combatant"], enemies: List["Combatant"],
                      battle_ctx: "BattleContext") -> "ActionDecision":
        """Decide what to do this turn.  Implemented differently for players vs. AI."""

    def __repr__(self) -> str:
        return f"{self._name}(HP={self._hp}/{self._max_hp})"


# ---------------------------------------------------------------------------
# Battle Context  (passed around so actions can query game state)
# ---------------------------------------------------------------------------
class BattleContext:
    """
    Lightweight value-object that gives Actions and Effects access to the
    current round's state without coupling them to the engine.
    """

    def __init__(self, round_number: int, allies: List[Combatant],
                 enemies: List[Combatant], log_fn=None) -> None:
        self.round_number = round_number
        self.allies = allies
        self.enemies = enemies
        self.log = log_fn or (lambda msg: None)


# ---------------------------------------------------------------------------
# Action  (Strategy pattern — each action is its own object)
# ---------------------------------------------------------------------------
class Action(ABC):
    """An action a combatant can perform on their turn."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name of the action."""

    @abstractmethod
    def execute(self, user: Combatant, targets: List[Combatant],
                battle_ctx: BattleContext) -> List[str]:
        """
        Perform the action.  Returns a list of log messages describing
        what happened.
        """


# ---------------------------------------------------------------------------
# Action Decision  (what choose_action returns)
# ---------------------------------------------------------------------------
class ActionDecision:
    """Bundles an Action with its chosen targets."""

    def __init__(self, action: Action, targets: List[Combatant]) -> None:
        self.action = action
        self.targets = targets


# ---------------------------------------------------------------------------
# Turn-Order Strategy
# ---------------------------------------------------------------------------
class TurnOrderStrategy(ABC):
    """Determines the order in which combatants act each round."""

    @abstractmethod
    def determine_order(self, combatants: List[Combatant]) -> List[Combatant]:
        """Return combatants sorted by turn priority."""


# ---------------------------------------------------------------------------
# Item
# ---------------------------------------------------------------------------
class Item(ABC):
    """A single-use consumable item carried by a player."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name of the item."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description shown in the inventory menu."""

    @abstractmethod
    def use(self, owner: Combatant, battle_ctx: BattleContext) -> List[str]:
        """
        Apply the item's effect.  Returns log messages.
        The item is consumed after use (handled by the caller).
        """
