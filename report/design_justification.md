# Turn-Based Combat Arena — Design Justification & SOLID Principles

## 1. Key Abstractions

The system is built on five abstract base classes defined in `interfaces.py`, each encoding a single responsibility:

| Abstraction | Module | Responsibility |
|---|---|---|
| `Combatant` (ABC) | `interfaces.py` | Represents any entity in combat — holds stats (HP, ATK, DEF, SPD), a list of `StatusEffect` objects, and the abstract `choose_action()` contract. |
| `Action` (ABC) | `interfaces.py` | Encapsulates a single thing a combatant can do on its turn via `execute()`. Implements the **Strategy** pattern. |
| `StatusEffect` (ABC) | `interfaces.py` | A temporary modifier with lifecycle hooks (`on_apply`, `on_turn_start`, `on_turn_end`, `on_remove`, `tick`). Implements a **Template Method**-style contract. |
| `TurnOrderStrategy` (ABC) | `interfaces.py` | Determines the order combatants act each round via `determine_order()`. Pure **Strategy** pattern. |
| `Item` (ABC) | `interfaces.py` | A single-use consumable with `use()`. Decouples item effects from the engine. |

Two supporting value-objects complete the interface layer:

- **`BattleContext`** — a lightweight data carrier passed to `Action.execute()` and `Item.use()`, providing round state (allies, enemies, round number) without coupling them to `BattleEngine`.
- **`ActionDecision`** — bundles an `Action` with its chosen `targets`, returned by `choose_action()`.

---

## 2. Design Decisions

### 2.1 Architectural Layering (Boundary–Control–Entity)

The codebase follows a **BCE** architecture:

| Layer | Modules | Role |
|---|---|---|
| **Boundary** | `cli.py`, `main.py` | All `input()`/`print()` interaction. The domain model never imports `cli.py`. |
| **Control** | `engine.py`, `turn_order.py` | Orchestration of the round loop, effect lifecycle, and win/loss detection. |
| **Entity** | `interfaces.py`, `combatants.py`, `actions.py`, `skills.py`, `effects.py`, `items.py`, `levels.py` | Domain model: characters, actions, effects, items, and level definitions. |

### 2.2 Responsibility Assignment

- **`BattleEngine`** owns the round loop, effect ticking, and victory checks — but *never* creates concrete combatants, actions, or effects. It receives them through its `run_battle(players, enemies)` method and through `ActionDecision` objects returned polymorphically.
- **`PlayerCombatant`** delegates action selection to an injected callback (`set_action_callback()`), decoupling the entity from the UI.
- **`EnemyCombatant`** encapsulates the AI policy (always `BasicAttack`) inside `choose_action()`.
- **`LevelDefinition`** uses factory callables (`initial_wave_factory`, `backup_wave_factory`) so level configuration is data-driven.

### 2.3 Coupling and Cohesion

| Metric | Assessment |
|---|---|
| **High cohesion** | Each module groups closely-related classes. `effects.py` contains only `StatusEffect` subclasses; `actions.py` contains only `Action` subclasses; `combatants.py` contains only `Combatant` subclasses. |
| **Low coupling** | `BattleEngine` depends on `Combatant`, `TurnOrderStrategy`, and `BattleContext` abstractions — never on `Warrior`, `Goblin`, `BasicAttack`, etc. The CLI depends on the domain model but the domain model has zero imports from `cli.py`. |
| **Unidirectional dependency** | Dependency flow: `main.py` → `cli.py` → domain layer ← `engine.py`. No circular imports exist. |

---

## 3. SOLID Proof

### 3.1 Single Responsibility Principle (SRP)

> *"A class should have only one reason to change."*

| Class | Single Responsibility | Evidence |
|---|---|---|
| `BattleEngine` | Orchestrate the round loop | Contains `run_battle()`, `_tick_effects()`, `_print_status()` — all related to battle flow. Has no knowledge of UI input or which concrete actions exist. |
| `CLI` (functions in `cli.py`) | Handle all user I/O | `select_character()`, `select_item()`, `player_action_callback()`, `show_level_intro()`, etc. The domain model never calls `print()` or `input()`. |
| `BasicAttack` | Execute a single-target attack | Its `execute()` computes damage and applies it — nothing else. |
| `Defend` | Apply a `DefenseBoost` effect | Its `execute()` does exactly one thing: `user.add_status_effect(DefenseBoost(...))`. |
| `StunEffect` | Prevent the target from acting | Lifecycle hooks (`on_turn_start` returns "stunned" message, `tick` decrements duration) — all related to the stun mechanic. |
| `SpeedBasedTurnOrder` | Sort combatants by speed | A single `determine_order()` method. |

### 3.2 Open/Closed Principle (OCP)

> *"Software entities should be open for extension, closed for modification."*

**Adding a new Action** (e.g., `FireballAction`):
1. Create a new class in `actions.py` (or a new module) extending `Action`.
2. Implement `name` and `execute()`.
3. **No changes to `BattleEngine`** — it calls `decision.action.execute()` polymorphically (line 85 of `engine.py`).

**Adding a new StatusEffect** (e.g., `PoisonEffect`):
1. Create a new class extending `StatusEffect`.
2. Implement the lifecycle hooks.
3. **No changes to `BattleEngine`** — it iterates `combatant.status_effects` and calls `on_turn_start()`, `tick()`, `on_turn_end()` generically (lines 61–71, 118–128 of `engine.py`).

**Adding a new Item** (e.g., `Elixir`):
1. Create a new class extending `Item`.
2. Implement `use()`.
3. **No changes to `BattleEngine`** — `UseItem.execute()` delegates to `self._item.use()` (line 65 of `actions.py`).

### 3.3 Liskov Substitution Principle (LSP)

> *"Objects of a superclass should be replaceable with objects of a subclass without affecting correctness."*

**Proof**: `BattleEngine.run_battle()` accepts `players: List[Combatant]` and `enemies: List[Combatant]`. It calls:
- `combatant.is_alive` (line 54)
- `combatant.status_effects` (line 61)
- `combatant.choose_action(allies, foes, ctx)` (line 84)
- `combatant.take_damage()`, `combatant.hp`, etc. — all defined on `Combatant`.

All four concrete subclasses — `Warrior`, `Wizard`, `Goblin`, `Wolf` — correctly implement these contracts:
- `PlayerCombatant.choose_action()` delegates to the injected callback.
- `EnemyCombatant.choose_action()` returns `ActionDecision(BasicAttack(), [target])`.

Both are valid substitutions for `Combatant` everywhere in the engine. No `isinstance` checks differentiate between Player and Enemy during the core action–execute loop.

### 3.4 Interface Segregation Principle (ISP)

> *"No client should be forced to depend on interfaces it does not use."*

| Interface | Methods | Assessment |
|---|---|---|
| `Action` | `name`, `execute()` | **2 members** — minimal. Every concrete action uses both. |
| `TurnOrderStrategy` | `determine_order()` | **1 method** — as lean as possible. |
| `Item` | `name`, `description`, `use()` | **3 members** — all are essential for inventory display and consumption. |
| `StatusEffect` | `name`, `remaining_turns`, `is_expired`, lifecycle hooks | **7 members** — each serves a distinct role in the effect lifecycle. No concrete effect leaves any method unused. `StunEffect` uses `on_turn_start()` to flag "skip turn"; `DefenseBoost` uses `on_remove()` to reset its bonus; `SmokeBombEffect` uses `on_turn_start()` to log the smoke message. |

No interface forces its implementors to carry dead methods.

### 3.5 Dependency Inversion Principle (DIP)

> *"High-level modules should depend on abstractions, not on low-level modules."*

**High-level module: `BattleEngine`** (in `engine.py`)

| Constructor Parameter | Type | Concrete? |
|---|---|---|
| `turn_strategy` | `TurnOrderStrategy` (ABC) | ❌ — abstraction |

| Method Parameter | Type | Concrete? |
|---|---|---|
| `players` | `List[Combatant]` (ABC) | ❌ — abstraction |
| `enemies` | `List[Combatant]` (ABC) | ❌ — abstraction |

The engine's `import` statements (line 12 of `engine.py`):
```python
from combat_arena.interfaces import Combatant, BattleContext, TurnOrderStrategy
```
It imports **only abstractions**. The concrete `SpeedBasedTurnOrder` is injected by `main.py`:
```python
engine = BattleEngine(turn_strategy=SpeedBasedTurnOrder())
```

The wiring of concrete classes to abstractions is done exclusively in the Boundary layer (`main.py`), not inside the engine itself.

---

## 4. Design Patterns Summary

| Pattern | Where Applied |
|---|---|
| **Strategy** | `TurnOrderStrategy` / `SpeedBasedTurnOrder` — interchangeable turn-order algorithms. `Action` hierarchy — each action encapsulates a distinct algorithm. |
| **Template Method** | `StatusEffect` lifecycle hooks — the engine calls the same sequence of hooks; each subclass fills in the behaviour. |
| **Dependency Injection** | `BattleEngine.__init__()` receives `TurnOrderStrategy`. `PlayerCombatant.set_action_callback()` receives the CLI function. `main.py` wires everything together. |
| **Factory Method** | `LevelDefinition.initial_wave_factory` and `backup_wave_factory` — callables that produce enemy lists on demand. |
| **Decorator / Wrapper** | `SpecialSkillAction` wraps an `Action` (the skill) and adds cooldown semantics. `UseItem` wraps an `Item` inside the `Action` interface. |
