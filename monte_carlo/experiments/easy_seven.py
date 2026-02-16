from ..runner import Experiment, MonteCarloResult
from src.inventory import Inventory
from src.alembic import Alembic
from src.player import Player
from src.database import IngredientsDatabase
from dataclasses import dataclass
import time

class EasyExperiment(Experiment):

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

        return {"run_idx": run_idx, "num_potions": len(potions), "simulation_time": simtime}

@dataclass
class EasyResult(MonteCarloResult):

    def __repr__(self):
        return "Easy Experiment - intended for basic functionality tests"

    def aggregate_stats(self):
        start = time.time()
        potion_stats = self._average_and_total_potions()
        self.aggregated_stats.append(potion_stats)

        simtime_stats = self._average_and_total_simtime()
        self.aggregated_stats.append(simtime_stats)
        self.aggregated_stats.append({"result aggregation time": time.time() - start})

    def _average_and_total_simtime(self):
        total = sum([run["simulation_time"] for run in self.run_results])
        return {
            "total_simtime": total,
            "average_simtime": total / self.config.num_simulations,
        }

    def _average_and_total_potions(self):
        total = sum([run["num_potions"] for run in self.run_results])
        return {
            "total_potions": total,
            "average_potions": total / self.config.num_simulations,
        }
