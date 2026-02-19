from ..runner import Experiment, MonteCarloResult
from src.inventory import Inventory
from src.alembic import Alembic
from src.player import Player
from src.database import IngredientsDatabase
from dataclasses import dataclass, field
import time

class AverageIngredientPerformance(Experiment):

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
        # set state for debugging:
        self.running = True
        self.run_idx = run_idx
        start = time.time()
        
        self.inv = Inventory.generate_normal(self.db, self.inv_size)

        self.alembic = Alembic(self.db, self.player, self.inv)
        self.potions = self.alembic.exhaust_inventory(strategy="lazy")

        ingmap = self.alembic.ingredients_map

        simtime = time.time() - start
        self.running = False

        return {"run_idx": run_idx,
                "num_potions": len(self.potions), 
                "ingredients_map": ingmap,
                "simulation_time": simtime}

@dataclass
class AverageIngredientResult(MonteCarloResult):
    db: IngredientsDatabase = field(default_factory=IngredientsDatabase)

    def __repr__(self):
        return "Easy Experiment - intended for basic functionality tests"

    def aggregate_stats(self):
        start = time.time()
        potion_stats = self._average_and_total_potions()
        self.aggregated_stats.append(potion_stats)

        simtime_stats = self._average_and_total_simtime()
        self.aggregated_stats.append(simtime_stats)
        self.aggregated_stats.append({"result aggregation time": time.time() - start})
        self.aggregated_stats.append(self._average_ingredient_performance())

    def _average_ingredient_performance(self):
        db = self.db

        appearances = {}
        total_values = {}

        for ing in db: 
            appearances[ing] = 0
            total_values[ing] = 0

        for run in self.run_results:
            ingmap = run["ingredients_map"]
            for ing in db:
                if ing in ingmap.keys():
                    appearances[ing] += 1
                    for potion in ingmap[ing]:
                        total_values[ing] += potion.value

        performance_map = dict(sorted(
            ((ing.name, (total_values[ing] // appearances[ing]) if appearances[ing] != 0 else None) for ing in db),
            key=lambda item: item[1] if item[1] is not None else -1,
            reverse=True
        ))

        return {
                "average_performance": performance_map,
        }



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
