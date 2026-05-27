from ..runner import Scenario
from alchemy.inventory import Inventory
from alchemy.alembic import Alembic
from alchemy.player import Player
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class RarityWeightedScenario(Scenario):
    """Exhaust a rarity-weighted random inventory and record potion yield and value.

    total: total ingredient count drawn; distinct: number of unique ingredient types.
    rarity_dist: optional override for per-ingredient rarity weights.
    """
    player: Player = field(default_factory=Player)
    total: int = 14
    distinct: int = 7
    rarity_dist: Optional[dict] = None

    def __str__(self):
        return "Rarity Weighted Inventory Scenario - tests rarity-weighted inventory generation"

    def __repr__(self):
        return (
            f"RarityWeightedScenario(total={self.total}, distinct={self.distinct}, "
            f"rarity_dist={self.rarity_dist!r}, player={self.player!r})"
        )

    def run_once(self, run_idx) -> dict:
        start = time.time()

        inv = Inventory.generate_weighted(self.db, self.total, self.distinct, rarity_dist=self.rarity_dist)
        alembic = Alembic(self.db, self.player, inv)
        potions = alembic.exhaust_inventory(strategy="lazy")

        return {
            "run_idx": run_idx,
            "num_potions": len(potions),
            "total_value": sum(p.value for p in potions),
            "ingredients_map": alembic.ingredients_map,
            "simulation_time": time.time() - start,
        }

    def aggregate_stats(self):
        start = time.time()
        self.aggregated_stats.update(self._average_and_total_potions())
        self.aggregated_stats.update(self._average_and_total_value())
        self.aggregated_stats.update(self._average_and_total_simtime())
        self.aggregated_stats.update(self._average_ingredient_performance())
        self.aggregated_stats["result_aggregation_time"] = time.time() - start
