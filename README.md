<div align="center">

# ⚔️ Turn-Based Combat Arena

**A SOLID-Architected CLI Combat Engine in Python**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OOP](https://img.shields.io/badge/OOP-SOLID_Principles-blueviolet?style=for-the-badge)
![CLI](https://img.shields.io/badge/Interface-CLI-green?style=for-the-badge&logo=windowsterminal&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

A fully object-oriented, command-line turn-based combat engine built from the ground up with **strict SOLID adherence**, **abstract base classes**, and a clean **Boundary–Control–Entity** architecture. Players choose a hero class, equip a consumable item, and battle through three increasingly brutal levels — complete with wave-based backup spawning, a dynamic status-effect system, and speed-based turn ordering — all powered by an engine that never touches a single concrete class.

</div>

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Architecture & SOLID Proof](#-architecture--solid-proof)
- [Game Mechanics](#-game-mechanics)
- [Project Structure](#-project-structure)
- [Installation & Execution](#-installation--execution)
- [Author](#-author)

---

## ✨ Key Features

### ⚡ Dynamic Turn-Order System
Combatants act each round in **descending order of their Speed stat**, determined at runtime by the injectable `SpeedBasedTurnOrder` strategy. Swap in a different `TurnOrderStrategy` implementation (random, initiative-roll, etc.) without touching the engine.

### 🌊 Wave-Based Backup Spawning
Each of the **3 difficulty levels** supports a backup wave. Reinforcements enter the battlefield **only after the initial wave is fully eliminated** — creating a strategic layer where overkill on the first wave matters.

| Level | Initial Wave | Backup Wave |
|-------|-------------|-------------|
| **1 — Easy** | 3 Goblins | — |
| **2 — Medium** | 1 Goblin, 1 Wolf | 2 Wolves |
| **3 — Hard** | 2 Goblins | 1 Goblin, 2 Wolves |

### 🎭 Status Effect Lifecycle
Effects like **Stun**, **DefenseBoost**, and **SmokeBomb** hook into a full lifecycle (`on_apply` → `on_turn_start` → `on_turn_end` → `tick` → `on_remove`), processed generically by the engine each turn — no `if/else` chains, pure polymorphism.

### 🗡️ Distinct Hero Classes

| Hero | HP | ATK | DEF | SPD | Special Skill |
|------|----|-----|-----|-----|---------------|
| **Warrior** | 260 | 40 | 20 | 30 | **Shield Bash** — Deals attack damage and **stuns** the target for 2 turns |
| **Wizard** | 200 | 50 | 10 | 20 | **Arcane Blast** — AoE damage to **all** enemies; each kill grants **+10 ATK** permanently |

### 🎒 Consumable Items (Choose 1 at Start)

| Item | Effect |
|------|--------|
| **Potion** | Heals 100 HP (capped at Max HP) |
| **Power Stone** | Fires your Special Skill for free — **no cooldown cost** |
| **Smoke Bomb** | All incoming enemy damage reduced to **0** for 2 turns |

---

## 🏗️ Architecture & SOLID Proof

The codebase is organised into a clean **Boundary–Control–Entity (BCE)** layered architecture:

```
Boundary (cli.py, main.py)
    ↓ depends on
Control (engine.py, turn_order.py)
    ↓ depends on
Entity (interfaces.py, combatants.py, actions.py, skills.py, effects.py, items.py)
```

### **SRP — Single Responsibility Principle**

> *Every class has one reason to change.*

- **`BattleEngine`** — orchestrates the round loop, effect ticking, and win/loss detection. Has **zero** `print()` or `input()` calls.
- **`cli.py`** — handles **all** user I/O: character selection, action menus, level intros. The domain layer never imports it.
- **`BasicAttack`** — computes and applies damage. Nothing else.
- **`SpeedBasedTurnOrder`** — a single method: `determine_order()`.

### **OCP — Open/Closed Principle**

> *Open for extension, closed for modification.*

Adding a **new Action** (e.g., `Fireball`)?
1. Create a class extending `Action`.
2. Implement `name` and `execute()`.
3. ✅ **`BattleEngine` is never modified** — it calls `decision.action.execute()` polymorphically.

The same applies to adding new `StatusEffect`, `Item`, or `TurnOrderStrategy` implementations — the engine's core loop remains untouched.

### **LSP — Liskov Substitution Principle**

> *Subtypes must be substitutable for their base types.*

`BattleEngine.run_battle()` accepts `List[Combatant]`. It calls `choose_action()`, `is_alive`, `take_damage()`, and `status_effects` — all defined on the abstract `Combatant` class. **`Warrior`, `Wizard`, `Goblin`, and `Wolf`** all satisfy this contract and are fully interchangeable inside the engine.

### **ISP — Interface Segregation Principle**

> *No client is forced to depend on methods it doesn't use.*

| Interface | Members | Bloat? |
|-----------|---------|--------|
| `Action` | `name`, `execute()` | ❌ **2 members** |
| `TurnOrderStrategy` | `determine_order()` | ❌ **1 method** |
| `Item` | `name`, `description`, `use()` | ❌ **3 members** |

Every member is used by every implementor.

### **DIP — Dependency Inversion Principle**

> *Depend on abstractions, not concretions.*

`BattleEngine`'s constructor signature:
```python
def __init__(self, turn_strategy: TurnOrderStrategy, log_fn: Callable = print)
```
It imports **only** `Combatant`, `BattleContext`, and `TurnOrderStrategy` from `interfaces.py`. The concrete `SpeedBasedTurnOrder` is injected by `main.py` — the engine never knows it exists.

---

## 🎮 Game Mechanics

- **Damage Formula**: `max(0, Attacker.ATK − Target.DEF)`
- **Turn Order**: Descending Speed stat per round
- **Special Skill Cooldown**: 3 turns after use
- **Defend**: +10 DEF for 2 turns (current + next)
- **Enemy AI**: Always performs `BasicAttack` on the player
- **Stun**: Target skips their turn for 2 turns
- **Smoke Bomb**: Incoming damage = 0 for 2 turns

---

## 📁 Project Structure

```
Turn-Based-Combat-Arena/
├── main.py                          # Entry point — wires Boundary → Control → Entity
└── combat_arena/
    ├── __init__.py
    ├── interfaces.py                # ABCs: Combatant, Action, StatusEffect, TurnOrderStrategy, Item
    ├── combatants.py                # Warrior, Wizard, Goblin, Wolf
    ├── actions.py                   # BasicAttack, Defend, UseItem, SpecialSkillAction
    ├── skills.py                    # ShieldBash, ArcaneBlast
    ├── effects.py                   # StunEffect, DefenseBoost, SmokeBombEffect
    ├── items.py                     # Potion, PowerStone, SmokeBomb
    ├── turn_order.py                # SpeedBasedTurnOrder
    ├── engine.py                    # BattleEngine — the core combat loop
    ├── levels.py                    # 3 levels with backup-wave factories
    └── cli.py                       # All user I/O (menus, banners, prompts)
```

---

## 🚀 Installation & Execution

```bash
# Clone the repository
git clone https://github.com/anniketkumar/Turn-Based-Combat-Arena.git

# Navigate to the project
cd Turn-Based-Combat-Arena

# Run the game (Python 3.10+ required, zero dependencies)
python main.py
```

> **Note**: No external packages required — the entire game runs on the Python standard library.

---

## 👤 Author

<table>
  <tr>
    <td><strong>Name</strong></td>
    <td>Aniket Kumar</td>
  </tr>
  <tr>
    <td><strong>University</strong></td>
    <td>Computer Science @ Nanyang Technological University (NTU)</td>
  </tr>
  <tr>
    <td><strong>GitHub</strong></td>
    <td><a href="https://github.com/anniketkumar">@anniketkumar</a></td>
  </tr>
</table>

---

<div align="center">

*Built with ❤️ and strict SOLID principles.*

</div>
