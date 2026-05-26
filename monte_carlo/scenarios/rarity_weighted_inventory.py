from ..runner import Scenario
from alchemy.inventory import Inventory
from alchemy.alembic import Alembic
from alchemy.player import Player
from alchemy.database import IngredientsDatabase
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class RarityWeightedScenario(Scenario):
    player: Player = field(default_factory=Player)
    total: int = 14
    distinct: int = 7
    rarity_dist: Optional[dict] = None

    def __repr__(self):
        return "Rarity Weighted Inventory Scenario - tests rarity-weighted inventory generation"

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
