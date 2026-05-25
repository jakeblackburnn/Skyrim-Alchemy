from ..runner import Scenario, MonteCarloResult
from alchemy.inventory import Inventory
from alchemy.alembic import Alembic
from alchemy.player import Player
from alchemy.database import IngredientsDatabase
from dataclasses import dataclass
from typing import Dict
import time


class RarityWeightedScenario(Scenario):

    def __init__(self, db=IngredientsDatabase(), player=Player(), total=14, distinct=7, rarity_dist=None):
        self.db = db
        self.player = player
        self.inv_total = total
        self.inv_distinct = distinct
        self.rarity_dist = rarity_dist

    def run_once(self, run_idx) -> Dict[str, int]:
        start = time.time()

        inv = Inventory.generate_weighted(self.db, self.inv_total, self.inv_distinct, rarity_dist=self.rarity_dist)
        alembic = Alembic(self.db, self.player, inv)
        potions = alembic.exhaust_inventory(strategy="lazy")

        ingmap = alembic.ingredients_map
        simtime = time.time() - start

        return {"run_idx": run_idx,
                "num_potions": len(potions),
                "total_value": sum(p.value for p in potions),
                "ingredients_map": ingmap,
                "simulation_time": simtime,
               }


@dataclass
class RarityWeightedResult(MonteCarloResult):

    def __repr__(self):
        return "Rarity Weighted Inventory Scenario - tests rarity-weighted inventory generation"

    def aggregate_stats(self):
        start = time.time()
        self.aggregated_stats.append(self._average_and_total_potions())
        self.aggregated_stats.append(self._average_and_total_value())
        self.aggregated_stats.append(self._average_and_total_simtime())
        self.aggregated_stats.append({"result aggregation time": time.time() - start})
        self.aggregated_stats.append(self._average_ingredient_performance())
