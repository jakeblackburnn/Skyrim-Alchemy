# Monte Carlo Implementation Notes - MVP Focus

**Author:** J. Blackburn  
**Last Updated:** Feb 7, 2026  
**Status:** MVP Implementation Plan (Overhauled from original design specification)

---

## Critical Assessment of Current State

### What's Actually Implemented ✅
- Basic infrastructure skeleton: `MonteCarloConfig`, `Experiment`, `MonteCarloResult`, `MonteCarlo`
- Sequential execution loop (no parallelization yet)
- Abstract experiment interface
- Trivial test experiment (returns hardcoded value)

### What's Documented But Not Yet Implemented ❌
- RNG management and seed passing to experiments
- Result aggregation methods (mean, std, percentiles)
- Export capabilities (CSV, JSON, DataFrame)
- Any realistic Skyrim alchemy experiment
- Parallel execution
- Checkpointing
- Progress bars

### Infrastructure Status
**Current:** Basic skeleton exists but has API mismatches and missing functionality  
**Goal:** Minimum viable version that demonstrates full end-to-end pipeline

---

## Design Philosophy - Start Simple

**Principle:** Working code beats elegant architecture

The original design specification outlined an excellent end-state architecture with factory patterns, composable collectors, and advanced features. However, for MVP we need to:

1. **Fix the existing infrastructure** (API inconsistencies, missing methods)
2. **Build one working experiment** (toy example using tiny inventory)
3. **Validate the full pipeline** (infrastructure → experiment → simulation → results)
4. **Defer advanced features** until core functionality is proven

---

## MVP Specifications

### Goal
Create the **simplest possible working experiment** that demonstrates:
- Monte Carlo infrastructure → Experiment → Alchemy simulation → Results → Analysis

### Toy Experiment Design

**Fixed Inventory** (3 ingredients with known synergies for predictable testing):
- "Blue Mountain Flower" (Restore Health, Fortify Health, Fortify Conjuration, Damage Magicka Regen)
- "Hanging Moss" (Restore Health, Fortify Health, Damage Magicka, Fortify One-Handed)
- "Wheat" (Restore Health, Fortify Health, Damage Magicka Regen, Lingering Damage Magicka)

**Why these?** All share "Restore Health" and "Fortify Health" → guarantees valid 2-ingredient potions

**Quantity:** 1 of each ingredient (simplest case, no complex inventory exhaustion)

**Player:** Base beginner (skill=15, no perks)

**Expected Behavior:** Since inventory is fixed, results should be **deterministic** (same every run). This validates infrastructure correctness before adding true randomization.

### Metrics to Track (Minimal Set)

**Per run:**
- `run_id`: Simulation number
- `total_gold`: Sum of all potion values
- `num_potions`: Count of potions created
- `gold_per_ingredient`: Efficiency metric (total_gold / ingredients_consumed)
- `ingredients_consumed`: How many ingredients used
- `ingredients_remaining`: How many left unused

**Aggregated (across all runs):**
- Mean and standard deviation of each metric
- Min/max for sanity checking

---

## Implementation Roadmap

### Phase 1: Fix Infrastructure (30 min)

**File:** `monte_carlo/runner.py`

#### Changes Needed:

1. **Update `Experiment.run_once()` signature:**
   ```python
   @abstractmethod
   def run_once(self, run_id: int) -> Dict[str, any]:
       """Execute single simulation, return metrics dict"""
       pass
   ```

2. **Add seed initialization in `MonteCarlo.__init__()`:**
   ```python
   def __init__(self, config: MonteCarloConfig):
       self.config = config
       if config.seed is not None:
           random.seed(config.seed)
           np.random.seed(config.seed)
       print(f"Created Monte Carlo runner.\nConfig:\n{config.to_dict()}")
   ```

3. **Pass `run_id` in run loop:**
   ```python
   def run(self, experiment: Experiment):
       print("Running Monte Carlo experiment...")
       results = MonteCarloResult(config_dict=self.config.to_dict())
       
       for run_id in range(self.config.num_simulations):
           results.add_run(experiment.run_once(run_id))
       
       results.summary()
       return results
   ```

4. **Add analysis methods to `MonteCarloResult`:**
   ```python
   def get_metric(self, metric_name: str) -> List[float]:
       """Extract a single metric across all runs"""
       return [run[metric_name] for run in self.run_results if metric_name in run]
   
   def mean(self, metric_name: str) -> float:
       """Calculate mean of a metric"""
       values = self.get_metric(metric_name)
       return np.mean(values) if values else 0.0
   
   def std(self, metric_name: str) -> float:
       """Calculate standard deviation of a metric"""
       values = self.get_metric(metric_name)
       return np.std(values) if values else 0.0
   
   def summary(self):
       """Print formatted summary statistics"""
       if not self.run_results:
           print("No results to summarize")
           return
       
       print(f"\nMonte Carlo Results Summary")
       print(f"=" * 50)
       print(f"Total runs: {len(self.run_results)}")
       print(f"\nConfiguration:")
       for key, val in self.config_dict.items():
           print(f"  {key}: {val}")
       
       # Get all metric names from first run
       if self.run_results:
           metrics = [k for k in self.run_results[0].keys() if k != 'run_id']
           print(f"\nMetrics (mean ± std):")
           for metric in metrics:
               print(f"  {metric}: {self.mean(metric):.2f} ± {self.std(metric):.2f}")
   ```

5. **Add necessary imports:**
   ```python
   import random
   import numpy as np
   ```

### Phase 2: Create Toy Experiment (45 min)

**File:** `monte_carlo/experiments/tiny_inventory.py`

```python
"""
Minimal toy experiment for testing Monte Carlo infrastructure.

Uses a tiny fixed inventory (3 ingredients) to produce deterministic results
and validate that the infrastructure correctly runs the alchemy simulation.
"""

from ..runner import Experiment
from src.database import IngredientsDatabase, EffectsDatabase
from src.inventory import Inventory
from src.alembic import Alembic
from typing import Dict, List


class TinyInventoryExperiment(Experiment):
    """
    Toy experiment with fixed 3-ingredient inventory for infrastructure testing.
    
    Expected behavior: Deterministic results (same potions every run) since
    inventory is fixed. Use this to validate infrastructure before adding
    randomization.
    """
    
    def __init__(self, 
                 ingredient_names: List[str],
                 player_stats: Dict[str, any]):
        """
        Args:
            ingredient_names: List of 3-5 ingredient names with known synergies
            player_stats: Player configuration dict (see src.player.Player.from_dict)
        """
        self.ingredient_names = ingredient_names
        self.player_stats = player_stats
        
    def run_once(self, run_id: int) -> Dict[str, any]:
        """
        Execute single simulation with fixed inventory.
        
        Args:
            run_id: Simulation number (0-indexed)
            
        Returns:
            Dict with metrics: run_id, total_gold, num_potions, etc.
        """
        
        # Create inventory with 1 of each ingredient
        inv = Inventory.from_ingredients(self.ingredient_names)
        initial_count = inv.total_items()
        
        # Run alchemy simulation
        alembic = Alembic(self.player_stats)
        alembic.set_inventory(inv)
        potions = alembic.exhaust_inventory(strategy='greedy-basic')
        
        # Calculate metrics
        total_gold = sum(p.total_value for p in potions)
        num_potions = len(potions)
        
        # Count ingredients consumed
        remaining_count = inv.total_items()
        consumed_count = initial_count - remaining_count
        
        # Avoid division by zero
        gold_per_ingredient = total_gold / consumed_count if consumed_count > 0 else 0
        
        return {
            'run_id': run_id,
            'total_gold': total_gold,
            'num_potions': num_potions,
            'ingredients_consumed': consumed_count,
            'ingredients_remaining': remaining_count,
            'gold_per_ingredient': gold_per_ingredient,
        }
```

### Phase 3: Update Runner Script (15 min)

**File:** `run_mc.py`

```python
"""
Monte Carlo runner for ESV Skyrim alchemy experiments.

This script demonstrates the Monte Carlo infrastructure with a simple
toy experiment using a tiny fixed inventory.
"""

from monte_carlo.runner import MonteCarlo, MonteCarloConfig
from monte_carlo.experiments.tiny_inventory import TinyInventoryExperiment

# Toy inventory: 3 ingredients with guaranteed synergies
# All share "Restore Health" and "Fortify Health" effects
TINY_INGREDIENTS = [
    "Blue Mountain Flower",
    "Hanging Moss",
    "Wheat",
]

# Base player (beginner)
BASE_PLAYER = {
    "alchemy_skill": 15,
    "fortify_alchemy": 0,
    "alchemist_perk": 0,
    "physician_perk": False,
    "benefactor_perk": False,
    "poisoner_perk": False,
    "seeker_of_shadows": False,
    "purity_perk": False
}

def main():
    print("ESV Skyrim Alchemy - Monte Carlo Toy Experiment")
    print("=" * 60)
    print(f"\nInventory: {', '.join(TINY_INGREDIENTS)}")
    print(f"Player: Base stats (skill={BASE_PLAYER['alchemy_skill']})\n")
    
    # Configure Monte Carlo (start with 10 runs for testing)
    config = MonteCarloConfig(
        num_simulations=10,
        seed=42,  # Reproducibility
    )
    
    # Create experiment
    experiment = TinyInventoryExperiment(
        ingredient_names=TINY_INGREDIENTS,
        player_stats=BASE_PLAYER
    )
    
    # Run simulation
    runner = MonteCarlo(config)
    result = runner.run(experiment)
    
    # Results already printed by result.summary()
    print("=" * 60)
    print("\nExperiment complete!")

if __name__ == "__main__":
    main()
```

### Phase 4: Testing & Validation (20 min)

**Commands:**
```bash
python run_mc.py
```

**Expected Behavior:**
1. 10 runs complete without errors
2. **All runs produce identical results** (deterministic with fixed inventory)
3. Metrics show consistent values (mean with std ≈ 0)
4. Summary output displays:
   - Configuration (10 simulations, seed=42)
   - Metrics with mean ± std for each

**Validation Checks:**
- `total_gold > 0` (potions have value)
- `num_potions >= 1` (at least one valid combination exists)
- `ingredients_consumed <= 3` (can't use more than available)
- `gold_per_ingredient` is reasonable (100-500 gold range expected)
- `std` for all metrics ≈ 0 (deterministic results)

**Common Issues:**
- If `total_gold = 0`: Check ingredient names exist in database
- If `num_potions = 0`: Ingredients may not share effects
- If std > 0: Randomization leaked in (should be impossible with fixed inventory)

### Phase 5: Add Randomization (Next Iteration)

Once deterministic version works, add true Monte Carlo variation:

1. **Change inventory generation:**
   ```python
   def run_once(self, run_id: int) -> Dict[str, any]:
       # Use random inventory instead of fixed
       db = IngredientsDatabase()
       inv = Inventory.generate_normal(db, size=5)  # Random 5 ingredients
       # ... rest of simulation
   ```

2. **Expected behavior changes:**
   - Different results per run (std > 0)
   - Wider range of total_gold values
   - Variable num_potions

3. **Add inventory tracking:**
   ```python
   return {
       # ... existing metrics
       'inventory_size': inv.unique_items(),
       'ingredient_names': ','.join(inv.get_available_ingredients()),
   }
   ```

---

## Architecture Diagram (Simplified MVP)

```
run_mc.py
    ↓
MonteCarlo(config)  ← MonteCarloConfig(num_sims=10, seed=42)
    ↓
MonteCarlo.run(experiment)  ← TinyInventoryExperiment(ingredients, player)
    ↓
Loop: experiment.run_once(run_id)  [run_id = 0, 1, 2, ..., 9]
    ↓
    Inventory.from_ingredients(["Blue Mountain Flower", "Hanging Moss", "Wheat"])
        ↓
    Alembic(player_stats)
        ↓  
    alembic.set_inventory(inv)
        ↓
    alembic.exhaust_inventory('greedy-basic')  → List[Potion]
        ↓
    Calculate metrics (total_gold, num_potions, efficiency)
        ↓
    Return Dict[str, any]
    ↓
MonteCarloResult.add_run(dict)
    ↓
MonteCarloResult.summary()  → Console output with statistics
```

---

## Success Criteria for MVP

MVP is **complete** when:

1. ✅ `python run_mc.py` runs without errors
2. ✅ Output shows sensible Skyrim alchemy results (gold values, potion counts)
3. ✅ Results are deterministic (same seed → same output, std ≈ 0)
4. ✅ Can change config (num_simulations, seed) and see expected changes
5. ✅ Code is simple enough to understand in 5 minutes

MVP is **NOT complete** until you can:
- Add a new experiment by subclassing `Experiment`
- Run it with the same `MonteCarlo` runner without modifying runner code
- Get aggregated results (mean, std) automatically

---

## Deferred Features (Post-MVP)

**Not needed for MVP:**
- ❌ Factory functions (premature abstraction)
- ❌ Composable metric collectors (over-engineering)
- ❌ Custom aggregators (YAGNI - You Aren't Gonna Need It)
- ❌ Parallel execution (sequential works fine for now)
- ❌ Checkpointing (runs complete in <1 second)
- ❌ DataFrame conversion (can add when needed)
- ❌ CSV/JSON export (console output sufficient for testing)
- ❌ Progress bars (runs too fast to matter)
- ❌ `rng` parameter in `run_once()` (use module-level random for now)

**Add only when needed:**
1. **Randomization** (Phase 5) - Next immediate priority
2. **Export** (when analyzing >100 runs and need external tools)
3. **Parallelization** (when runs take >10 seconds total)
4. **Real experiments** (vendor analysis, perk sensitivity) - after infrastructure proven

---

## Next Steps After MVP

### 1. Randomization Test (Phase 5)
- Switch from fixed inventory to `Inventory.generate_normal(db, size=5)`
- Verify std > 0 (actual variation across runs)
- Increase to 100 simulations
- Analyze distribution of results

### 2. Scaling Test
- Run 1000 simulations
- Measure execution time
- Decide if parallelization needed (likely not needed yet)

### 3. First Real Experiment
Implement vendor vs player inventory comparison:
```python
class VendorComparisonExperiment(Experiment):
    def run_once(self, run_id: int) -> Dict:
        db = IngredientsDatabase()
        
        # Alternate between strategies
        if run_id % 2 == 0:
            inv = Inventory.generate_vendor(db)
            inv_type = 'vendor'
        else:
            inv = Inventory.generate_random_weighted(db)
            inv_type = 'player'
        
        # ... run simulation
        return {
            'inventory_type': inv_type,
            'total_gold': ...,
            # ... other metrics
        }
```

### 4. Export Capability
Add when ready for external analysis:
```python
# In MonteCarloResult
def to_json(self, filepath: str):
    import json
    with open(filepath, 'w') as f:
        json.dump({
            'config': self.config_dict,
            'results': self.run_results
        }, f, indent=2)
```

### 5. Advanced Features (Only When Specific Need Identified)
- Parallel execution (if runs become slow)
- Custom aggregators (if standard stats insufficient)
- Factory patterns (if pickle/multiprocessing issues arise)

---

## Design Principles (Revised for MVP)

1. **Start Simple:** Working code beats elegant architecture
2. **One Thing at a Time:** Fix infrastructure → build experiment → add features
3. **Validate Early:** Deterministic test case catches bugs immediately
4. **Defer Optimization:** Sequential execution is fine until proven otherwise
5. **Concrete Before Abstract:** Build one experiment well before generalizing
6. **YAGNI:** You Aren't Gonna Need It - only add features when needed

---

## Key Differences from Original Notes

| Original Design | This MVP Plan | Rationale |
|-----------------|---------------|-----------|
| Factory functions for dependencies | Direct instantiation | Simpler, sufficient for single-threaded |
| Composable metric collectors | Simple dict return | Less code, easier to understand |
| Custom aggregators | Basic mean/std methods | Covers 90% of use cases |
| `run_once(run_id, rng)` | `run_once(run_id)` | Module random sufficient for now |
| Parallel execution | Sequential only | Fast enough, avoids complexity |
| Advanced features up front | Defer until needed | Reduces initial development time |
| Multiple example experiments | One working toy experiment | Proves infrastructure before expanding |

**Philosophy:** Original notes describe the **destination** (mature system). This plan describes the **first step** (working MVP).

Once the toy experiment works perfectly, complexity can be added incrementally with confidence that the foundation is solid.

---

## Estimated Implementation Time

- **Phase 1 (Infrastructure fixes):** 30 minutes
- **Phase 2 (Toy experiment):** 45 minutes  
- **Phase 3 (Runner script):** 15 minutes
- **Phase 4 (Testing):** 20 minutes
- **Total MVP:** ~2 hours of focused work

---

## Future Architecture (Post-MVP)

After MVP is working, the original design specification provides excellent guidance for scaling up:

1. **Parallel Execution:** Add multiprocessing when needed
2. **Factory Pattern:** Introduce when pickling becomes necessary
3. **Advanced Metrics:** Add composable collectors when experiment complexity grows
4. **Export Formats:** Add CSV/JSON/DataFrame when external analysis needed
5. **Real Experiments:** Implement vendor analysis, perk sensitivity, ingredient synergy

The key insight: **Build incrementally with working code at each step**, rather than implementing the full architecture upfront.

---

## References

- **Original design notes:** Excellent long-term architecture vision (factory patterns, composable collectors)
- **Current codebase:** Strong simulation foundation in `src/` ready for Monte Carlo integration
- **Bug report:** Identifies previous issues with perk calculations (fixed in player configuration)
- **Design patterns:** Start with Strategy pattern (Experiment subclasses), add others as needed
- **Scientific computing:** NumPy for basic statistics, defer pandas until data volume requires it
