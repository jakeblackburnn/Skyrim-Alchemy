from ..runner import Scenario, MonteCarloResult
from alchemy.inventory import Inventory
from alchemy.alembic import Alembic
from alchemy.player import Player
from alchemy.database import IngredientsDatabase
from dataclasses import dataclass
from typing import Dict
import time



class SmokeTestScenario(Scenario):

    def __init__(self, db=IngredientsDatabase(), player=Player(), inv_size=7):
        self.db = db
        self.player = player
        self.inv_size = inv_size

    def run_once(self, run_idx) -> Dict[str, int]:
        start = time.time()

        inv = Inventory.generate_normal(self.db, self.inv_size)
        alembic = Alembic(self.db, self.player, inv)
        potions = alembic.exhaust_inventory(strategy="lazy")

        simtime = time.time() - start

        return {"run_idx": run_idx, "num_potions": len(potions), "total_value": sum(p.value for p in potions), "simulation_time": simtime}

@dataclass
class SmokeTestResult(MonteCarloResult):

    def __repr__(self):
        return "Smoke Test Scenario - basic functionality test for the MC runner"

    def aggregate_stats(self):
        start = time.time()
        self.aggregated_stats.append(self._average_and_total_potions())
        self.aggregated_stats.append(self._average_and_total_value())
        self.aggregated_stats.append(self._average_and_total_simtime())
        self.aggregated_stats.append({"result aggregation time": time.time() - start})
