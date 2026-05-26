from ..runner import Scenario
from alchemy.inventory import Inventory
from alchemy.alembic import Alembic
from alchemy.player import Player
from alchemy.database import IngredientsDatabase
from dataclasses import dataclass, field
import time


@dataclass
class StableInventoryScenario(Scenario):
    player: Player = field(default_factory=Player)
    total: int = 14
    distinct: int = 7

    def __repr__(self):
        return "Stable Inventory Scenario - intended for basic tests of stable inventory generation"

    def run_once(self, run_idx) -> None:
        start = time.time()

        inv = Inventory.generate_stable(self.db, self.total, self.distinct)
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
        self.aggregated_stats.update(self._average_and_total_potions())
        self.aggregated_stats.update(self._average_and_total_value())
        self.aggregated_stats.update(self._average_and_total_simtime())
        self.aggregated_stats.update(self._average_ingredient_performance())
        self.aggregated_stats["result_aggregation_time"] = time.time() - start
