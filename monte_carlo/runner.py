import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm



@dataclass
class Scenario(ABC):
    """Base class for a Monte Carlo scenario.

    Subclasses must implement run_once(), aggregate_stats(), and __str__().
    db is the IngredientsDatabase forwarded from the runner.
    """
    run_results:      List[Dict[str, Any]] = field(default_factory=list)
    aggregated_stats: Dict[str, Any] = field(default_factory=dict)
    db: Optional[Any] = field(default=None)

    @abstractmethod
    def run_once(self, run_idx: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def aggregate_stats(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    def to_dataframe(self):
        return pd.DataFrame(self.run_results)

    def _average_and_total_simtime(self):
        total = sum(run["simulation_time"] for run in self.run_results)
        n = len(self.run_results)
        return {
            "total_simtime": total,
            "average_simtime": total / n,
        }

    def _average_and_total_potions(self):
        values = [run["num_potions"] for run in self.run_results]
        n = len(values)
        total = sum(values)
        mean = total / n
        variance = sum((v - mean) ** 2 for v in values) / n
        return {
            "total_potions": total,
            "average_potions": mean,
            "stderr_potions": (variance / n) ** 0.5,
        }

    def _average_and_total_value(self):
        values = [run["total_value"] for run in self.run_results]
        n = len(values)
        total = sum(values)
        mean = total / n
        variance = sum((v - mean) ** 2 for v in values) / n
        return {
            "total_value": total,
            "average_value": mean,
            "stderr_value": (variance / n) ** 0.5,
        }

    def _average_ingredient_performance(self):
        n = len(self.run_results)
        appearances = {ing: 0 for ing in self.db}
        potion_values = {ing: [] for ing in self.db}
        contributions = {ing: [] for ing in self.db}

        for run in self.run_results:
            ingmap = run["ingredients_map"]
            for ing in self.db:
                potions = ingmap.get(ing, [])
                if potions:
                    appearances[ing] += 1
                    for potion in potions:
                        potion_values[ing].append(potion.value)
                        contributions[ing].append(potion.value / potion.num_ingredients)

        def _mean_and_stderr(vals):
            if not vals:
                return None, None
            m = sum(vals) / len(vals)
            var = sum((v - m) ** 2 for v in vals) / len(vals)
            return m, (var / len(vals)) ** 0.5

        performance_map = {}
        for ing in self.db:
            avg_pv, stderr_pv = _mean_and_stderr(potion_values[ing])
            avg_ct, stderr_ct = _mean_and_stderr(contributions[ing])
            performance_map[ing.name] = {
                "appearance_rate": appearances[ing] / n,
                "avg_potion_value": avg_pv,
                "stderr_potion_value": stderr_pv,
                "avg_contribution": avg_ct,
                "stderr_contribution": stderr_ct,
            }

        performance_map = dict(sorted(
            performance_map.items(),
            key=lambda item: item[1]["avg_potion_value"] if item[1]["avg_potion_value"] is not None else -1,
            reverse=True,
        ))
        return {"average_performance": performance_map}


def run_monte_carlo(
    scenario: Scenario,
    n: int,
    seed: Optional[int] = None,
    progress_bar: bool = False,
    verbose: bool = False,
) -> Scenario:
    if verbose:
        print("running monte carlo...")
        print(str(scenario))

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    start = time.time()

    pbar = tqdm(total=n, desc="Monte Carlo", unit="sim", disable=not progress_bar)

    for run_idx in range(n):
        scenario.run_results.append(scenario.run_once(run_idx))
        pbar.update(1)

    pbar.close()

    if verbose:
        total = time.time() - start
        print(f"total runtime: {total}\navg runtime per simulation: {total / n}")
        print("aggregating results")

    agg_start = time.time()
    scenario.aggregate_stats()

    if verbose:
        print(f"results crunched. took {time.time() - agg_start}.")

    return scenario
