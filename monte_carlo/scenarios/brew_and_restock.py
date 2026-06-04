from ..runner import Scenario
from alchemy.inventory import Inventory
from alchemy.alembic import Alembic
from alchemy.player import Player
from dataclasses import dataclass, field
import time


@dataclass
class BrewAndRestockScenario(Scenario):
    """Repeatedly brew the top `proportion` of an inventory, then restock it, over `cycles` rounds.

    Models continuous play (forage -> brew the best -> forage again) rather than a single
    hoard-then-dump. Each cycle exhausts `proportion` of the *current* inventory via the lazy
    (greedy, highest-value-first) strategy, then resamples the consumed capacity back up toward
    the original size. Per-cycle yield is tracked so the gold/potion curve over cycles is visible.

    total: starting ingredient count; distinct: starting unique ingredient types.
    proportion: fraction of the inventory consumed each cycle (passed to exhaust_inventory).
    cycles: number of brew-then-restock rounds.
    """
    player: Player = field(default_factory=Player)
    total: int = 128
    distinct: int = 24
    proportion: float = 0.5
    cycles: int = 4
    strategy: str = "lazy"

    def __str__(self):
        return "Brew And Restock Scenario - repeated partial-exhaust + restock cycles"

    def __repr__(self):
        return (
            f"BrewAndRestockScenario(total={self.total}, distinct={self.distinct}, "
            f"proportion={self.proportion}, cycles={self.cycles}, "
            f"strategy={self.strategy!r}, player={self.player!r})"
        )

    def _restock(self, inv, alembic):
        """Refill the consumed capacity back toward the original (total, distinct).

        Resamples only the *depleted* distinct types (those fully consumed), distributing the
        consumed item count among them. If no distinct type was fully depleted there is nothing
        new to add this cycle, so we skip. set_valid_potions() rebuilds so the freshly-sampled
        ingredients become brewable."""
        deficit_total = self.total - inv.total_items()
        deficit_distinct = self.distinct - inv.unique_items()
        if deficit_distinct < 1 or deficit_total < deficit_distinct:
            return
        inv.resample_stable(self.db, deficit_total, deficit_distinct, exclude_existing=True)
        alembic.set_valid_potions()

    def run_once(self, run_idx) -> dict:
        start = time.time()

        inv = Inventory.generate_stable(self.db, self.total, self.distinct)
        alembic = Alembic(self.db, self.player, inv)

        value_per_cycle = []
        potions_per_cycle = []
        prev_count = 0

        for cycle in range(self.cycles):
            potions = alembic.exhaust_inventory(strategy=self.strategy, proportion=self.proportion)
            cycle_potions = potions[prev_count:]
            value_per_cycle.append(sum(p.value for p in cycle_potions))
            potions_per_cycle.append(len(cycle_potions))
            prev_count = len(potions)

            if cycle < self.cycles - 1:
                self._restock(inv, alembic)

        return {
            "run_idx": run_idx,
            "num_potions": prev_count,
            "total_value": sum(value_per_cycle),
            "value_per_cycle": value_per_cycle,
            "potions_per_cycle": potions_per_cycle,
            "ingredients_map": alembic.ingredients_map,
            "simulation_time": time.time() - start,
        }

    def _per_cycle_averages(self):
        n = len(self.run_results)
        avg_value, avg_potions = [], []
        for c in range(self.cycles):
            avg_value.append(sum(run["value_per_cycle"][c] for run in self.run_results) / n)
            avg_potions.append(sum(run["potions_per_cycle"][c] for run in self.run_results) / n)

        cumulative, running = [], 0.0
        for v in avg_value:
            running += v
            cumulative.append(running)

        return {
            "avg_value_per_cycle": avg_value,
            "avg_potions_per_cycle": avg_potions,
            "cumulative_value_per_cycle": cumulative,
        }

    def aggregate_stats(self):
        start = time.time()
        self.aggregated_stats.update(self._average_and_total_potions())
        self.aggregated_stats.update(self._average_and_total_value())
        self.aggregated_stats.update(self._average_and_total_simtime())
        self.aggregated_stats.update(self._average_ingredient_performance())
        self.aggregated_stats.update(self._per_cycle_averages())
        self.aggregated_stats["result_aggregation_time"] = time.time() - start
