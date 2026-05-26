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
    inv_total: int = 14
    inv_distinct: int = 7
    rarity_dist: Optional[dict] = None

    def __repr__(self):
        return "Rarity Weighted Inventory Scenario - tests rarity-weighted inventory generation"

    def run_once(self, run_idx) -> None:
        start = time.time()

        inv = Inventory.generate_weighted(self.db, self.inv_total, self.inv_distinct, rarity_dist=self.rarity_dist)
        alembic = Alembic(self.db, self.player, inv)
        potions = alembic.exhaust_inventory(strategy="lazy")

        ingmap = alembic.ingredients_map
        simtime = time.time() - start

        self.run_results.append({
            "run_idx": run_idx,
            "num_potions": len(potions),
            "total_value": sum(p.value for p in potions),
            "ingredients_map": ingmap,
            "simulation_time": simtime,
        })

    def aggregate_stats(self):
        start = time.time()
        self.aggregated_stats.append(self._average_and_total_potions())
        self.aggregated_stats.append(self._average_and_total_value())
        self.aggregated_stats.append(self._average_and_total_simtime())
        self.aggregated_stats.append({"result aggregation time": time.time() - start})
        self.aggregated_stats.append(self._average_ingredient_performance())
