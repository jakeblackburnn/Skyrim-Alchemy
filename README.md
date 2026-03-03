# ESV: Skyrim Alchemy

Simulation infrastructure for Skyrim's alchemy system. Provides Monte Carlo framework for analyzing potion-making strategies and ingredient performance.

## Core Components

**Alembic** - Potion-making engine. Generates valid potions from inventory and executes exhaustion strategies.

**Inventory** - Ingredient storage with generation methods:
- `generate_weighted()` - Rarity-weighted sampling
- `generate_stable()` - Uniform random sampling  
- `generate_normal()` - Chi-squared quantity distribution

**Player** - Skill level, perks (Alchemist, Physician, Benefactor, Poisoner), and fortify alchemy enchantments.

**Potion** - Effect realization and value calculation from ingredient combinations.

**Database** - Loads Skyrim ingredient and effect data from CSVs (`data/master_ingredients.csv`, `data/effects.csv`).

## Potion-Making Strategy

Currently implements **lazy** strategy: iteratively select highest-value potion until inventory exhausted.

```python
from src.alembic import Alembic
from src.inventory import Inventory
from src.database import IngredientsDatabase
from src.player import Player

db = IngredientsDatabase()
inv = Inventory.generate_weighted(db, total=128, distinct=24)
player = Player(skill=50, alchemist_perk_level=3)

alembic = Alembic(db, player, inv)
potions = alembic.exhaust_inventory(strategy="lazy")
alembic.fancy_print()
```

## Monte Carlo Framework

Run experiments with configurable simulations and custom result aggregation.

**Runner** (`monte_carlo/runner.py`):
- `MonteCarloConfig` - Simulation count, progress bar, SIGINT debugging
- `MonteCarlo.run()` - Execute experiment with automatic state tracking

**Experiments** (`monte_carlo/experiments/`):
- Subclass `Experiment` and implement `run_once()`
- Subclass `MonteCarloResult` and implement `aggregate_stats()`

Example experiment (`run_mc.py`):
```python
from monte_carlo.runner import MonteCarlo, MonteCarloConfig
from monte_carlo.experiments.weighted_test import WeightedInventoryExperiment, WeightedInventoryResult

db = IngredientsDatabase()
config = MonteCarloConfig(num_simulations=3200, progress_bar=True)

result = WeightedInventoryResult(config=config, db=db)
exp = WeightedInventoryExperiment(db=db, total=128, distinct=24)

runner = MonteCarlo(config, result, verbose=True)
runner.run(exp)
```

## Analysis Tools

**Perk analysis** (`analysis/perks.py`) - Test perk combinations across ingredients to identify synergies.

**Rarity tolerance** (`analysis/rarity.py`) - Sweep rarity distributions to find stable vs volatile ingredients.

## Structure

```
src/               # Core simulation engine
  alembic.py       # Potion-making strategies
  inventory.py     # Inventory generation and management
  player.py        # Player stats and perks
  potion.py        # Effect realization
  database.py      # CSV data loading
  ingredient.py    # Ingredient objects
  effect.py        # Effect mechanics

monte_carlo/       # Monte Carlo framework
  runner.py        # Experiment execution
  experiments/     # Custom experiments

analysis/          # Meta-experiments (perks, rarity)
data/              # Skyrim data (ingredients, effects)
web_ui/            # Django calculator interface
```

## Dependencies

NumPy, Pandas, Django. See `requirements.txt`.
