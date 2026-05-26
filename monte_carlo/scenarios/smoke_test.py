from ..runner import Scenario
from alchemy.inventory import Inventory
from alchemy.alembic import Alembic
from alchemy.player import Player
from alchemy.database import IngredientsDatabase
from dataclasses import dataclass, field
import time


@dataclass
class SmokeTestScenario(Scenario):
    player: Player = field(default_factory=Player)
    inv_size: int = 7

    def __repr__(self):
        return "Smoke Test Scenario - basic functionality test for the MC runner"

    def run_once(self, run_idx) -> dict:
        start = time.time()

        inv = Inventory.generate_normal(self.db, self.inv_size)
        alembic = Alembic(self.db, self.player, inv)
        potions = alembic.exhaust_inventory(strategy="lazy")

        return {
            "run_idx": run_idx,
            "num_potions": len(potions),
            "total_value": sum(p.value for p in potions),
            "simulation_time": time.time() - start,
        }

    def aggregate_stats(self):
        start = time.time()
        self.aggregated_stats.update(self._average_and_total_potions())
        self.aggregated_stats.update(self._average_and_total_value())
        self.aggregated_stats.update(self._average_and_total_simtime())
        self.aggregated_stats["result_aggregation_time"] = time.time() - start
