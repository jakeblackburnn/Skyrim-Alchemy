from ..runner import Scenario, MonteCarloResult
from alchemy.inventory import Inventory
from alchemy.alembic import Alembic
from alchemy.player import Player
from alchemy.database import IngredientsDatabase
from dataclasses import dataclass, field
from typing import Dict
import time



class WeightedInventoryScenario(Scenario):

    def __init__(self, db=IngredientsDatabase(), player=Player(), total=14, distinct=7):
        self.db = db
        self.player = player 
        self.inv_total = total
        self.inv_distinct = distinct

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
        
        self.inv = Inventory.generate_weighted(self.db, self.inv_total, self.inv_distinct)
        self.alembic = Alembic(self.db, self.player, self.inv)
        self.potions = self.alembic.exhaust_inventory(strategy="lazy")

        ingmap = self.alembic.ingredients_map

        simtime = time.time() - start
        self.running = False

        return {"run_idx": run_idx, 
                "num_potions": len(self.potions), 
                "ingredients_map": ingmap,
                "simulation_time": simtime,
               }

@dataclass
class WeightedInventoryResult(MonteCarloResult):

    def __repr__(self):
        return "Weighted Inventory Scenario - tests weighted inventory generation"

    def aggregate_stats(self):
        start = time.time()
        potion_stats = self._average_and_total_potions()
        self.aggregated_stats.append(potion_stats)

        simtime_stats = self._average_and_total_simtime()
        self.aggregated_stats.append(simtime_stats)

        self.aggregated_stats.append({"result aggregation time": time.time() - start})

        self.aggregated_stats.append(self._average_ingredient_performance())
