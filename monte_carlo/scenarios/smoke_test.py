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

        # state for diagnostics
        self.running = False
        self.run_idx = 0
        self.inv = None
        self.alembic = None
        self.potions = None

    def get_state(self) -> Dict[str, any]:
        return {
            "running": self.running,
            "run_idx": self.run_idx,
            "inv":     self.inv,
            "alembic": self.alembic,
            "potions": self.potions,
        }

    def run_once(self, run_idx) -> Dict[str, int]:
        self.running = True
        self.run_idx = run_idx
        start = time.time()

        self.inv = Inventory.generate_normal(self.db, self.inv_size)
        self.alembic = Alembic(self.db, self.player, self.inv)
        self.potions = self.alembic.exhaust_inventory(strategy="lazy")

        simtime = time.time() - start
        self.running = False

        return {"run_idx": run_idx, "num_potions": len(self.potions), "simulation_time": simtime}

@dataclass
class SmokeTestResult(MonteCarloResult):

    def __repr__(self):
        return "Smoke Test Scenario - basic functionality test for the MC runner"

    def aggregate_stats(self):
        start = time.time()
        self.aggregated_stats.append(self._average_and_total_potions())
        self.aggregated_stats.append(self._average_and_total_simtime())
        self.aggregated_stats.append({"result aggregation time": time.time() - start})
