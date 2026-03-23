# Turn-Based Combat Arena — Reflection

## 1. Design Considerations

The primary challenge was to translate a turn-based game — an inherently procedural concept (loop → check → act → repeat) — into a genuinely object-oriented architecture where the engine operates exclusively through polymorphic interfaces.

The central design decision was defining **five narrow ABCs** (`Combatant`, `Action`, `StatusEffect`, `TurnOrderStrategy`, `Item`) that together form a "plugin contract." The `BattleEngine` never names a concrete class in its core loop; it asks each `Combatant` to `choose_action()`, calls `Action.execute()`, and iterates `StatusEffect` lifecycle hooks. This makes the engine a stable, closed module that new content can plug into without modification.

A secondary consideration was **separating the Boundary from the Domain**. The CLI module handles all `print()`/`input()` calls.  The player's action selection is injected into `PlayerCombatant` as a callback via `set_action_callback()`, meaning the entity layer has zero knowledge of the user interface. This would allow, for example, replacing the CLI with a web front-end or a test harness without changing a single domain class.

## 2. Extensibility

The architecture was designed for three primary extension vectors:

| Extension | Steps Required | Files Modified |
|---|---|---|
| New character class (e.g., Ranger) | Create a `Ranger(PlayerCombatant)` subclass with stats and a new `Action` subclass for its skill. | 0 existing files modified; 1–2 new files created. |
| New status effect (e.g., Poison) | Create a `PoisonEffect(StatusEffect)` subclass implementing the lifecycle hooks. | 0 existing files modified; 1 new class created. |
| New turn-order algorithm (e.g., random) | Create `RandomTurnOrder(TurnOrderStrategy)` and inject it into `BattleEngine`. | Only `main.py` changes (swap the strategy). |
| New item (e.g., Shield Potion) | Create a `ShieldPotion(Item)` subclass implementing `use()`. | 0 existing files modified; add to item selection list in `cli.py`. |

None of these extensions require modifying `BattleEngine`, confirming the Open/Closed Principle in practice.

## 3. Trade-offs and Limitations

### Deliberate Trade-offs

1. **Callback injection vs. an abstract method on `PlayerCombatant`**: I chose to inject the CLI's action-selection function as a callback rather than making `PlayerCombatant` abstract with an overridable `choose_action()`. This keeps the domain layer free of any UI coupling, but it means setups require an explicit `set_action_callback()` call in `main.py`. Forgetting this call results in a runtime error, which is caught by a clear `RuntimeError` message.

2. **String-based effect identification (`has_effect("Stun")`)**: The engine checks for stun by matching the effect's `name` property to the string `"Stun"`. This is simple and readable, but couples logic to a magic string. A stricter approach would use `isinstance()` checks or enum-based tags, trading readability for type safety.

3. **Single-player architecture**: The system supports exactly one player combatant per battle. While `run_battle()` accepts a `List[Combatant]` for players (making multi-player battles trivially supportable), the CLI's action callback and the item/cooldown system are designed for a single hero. Extending to a party-based system would require modest changes to `cli.py` and `main.py`, but zero changes to `engine.py`.

### Known Limitations

- **No persistent state/saving**: The game runs in a single session. A save/load system would require serialisation of `Combatant` state and effect stacks.
- **Enemy AI is trivial**: All enemies always use `BasicAttack`. The architecture fully supports smarter AI (each enemy subclass can override `choose_action()`), but the current scope only required the simple variant.
- **Item count limited to one**: The player picks a single item at game start. Supporting a full inventory would require expanding `cli.py`'s item-selection flow and possibly adding a backpack capacity limit.

## 4. Key Takeaways

- Investing time in defining **clean, minimal abstractions** up front pays compound returns as the system scales. Every new action, effect, or item "just works" without touching the engine.
- The **Boundary–Control–Entity** layering enforced a strict one-way dependency flow that eliminated circular imports and made each module independently testable.
- Python's `abc` module combined with type hints provided sufficient rigour for an OO design assignment while preserving the rapid-iteration benefits of a dynamic language.
