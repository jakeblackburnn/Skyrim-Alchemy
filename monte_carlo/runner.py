"""
Monte Carlo Runner Module for ESV Skyrim alchemy analysis with random inventory generation
Created by J. Blackburn - Feb 1 2026

Last updated - Feb 14 2026
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import time
from tqdm import tqdm
import pandas as pd
import numpy as np

@dataclass
class MonteCarloResult(ABC):
    run_results:      List[Dict[str, any]] = field(default_factory=list)
    aggregated_stats: List[Dict[str, any]] = field(default_factory=list)
    db: Optional[Any] = field(default=None)

    def add_run(self, run: Dict[str, any]):
        self.run_results.append(run)

    def to_dataframe(self):
        return pd.DataFrame(self.run_results)

    @abstractmethod
    def aggregate_stats(self):
        # do number crunching here
        pass

    @abstractmethod
    def __repr__(self):
        pass

    def summary(self):
        print(f"Monte Carlo Summary")
        print("raw data results:")
        print(self.to_dataframe())
        print(f"analysis:\n{self.aggregated_stats}\n")

    def save_to_json(self, filepath):
        import json
        with open(filepath, 'w') as f:
            json.dump(self.aggregated_stats, f, indent=2)

    def _average_and_total_simtime(self):
        total = sum([run["simulation_time"] for run in self.run_results])
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


class Scenario:
    def get_state(self) -> Optional[Dict[str, any]]:
        """
        Override to provide current state for SIGINT debugging.

        Returns:
            Dict with scenario-specific state to display on Ctrl+C,
            or None if no debug state tracking is needed.
        """
        return None

    @abstractmethod
    def run_once(self) -> Dict[str, any]:
        pass


class MonteCarlo:

    def __init__(self, results: MonteCarloResult, num_simulations: int, progress_bar: bool = False, verbose: bool = False):
        self.results = results
        self.num_simulations = num_simulations
        self.progress_bar = progress_bar
        self.verbose = verbose

        if verbose: print("creating monte carlo runner...")
        if verbose: print("loaded results object.\n" + str(results))

    def run(self, scenario: Scenario, seed: Optional[int] = None):
        import signal
        import sys
        import random

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        if self.verbose: print("running monte carlo...")

        start = time.time()

        state_tracker = {
            'current_iteration': -1,
            'total_iterations': self.num_simulations,
            'start_time': start,
            'last_update_time': start
        }

        def sigint_handler(sig, frame):
            elapsed = time.time() - state_tracker['start_time']
            current_iter = state_tracker['current_iteration']
            total_iter = state_tracker['total_iterations']
            since_update = time.time() - state_tracker['last_update_time']

            print(f"\nSIGINT — iter {current_iter+1}/{total_iter} | elapsed {elapsed:.1f}s | avg {elapsed/(current_iter+1):.2f}s/iter | stalled {since_update:.1f}s")

            debug_state = scenario.get_state()
            if debug_state:
                for k, v in debug_state.items():
                    print(f"  {k}: {v[:5]}..." if isinstance(v, list) and len(v) > 5 else f"  {k}: {v}")

            if self.results.run_results:
                print(f"  completed runs: {len(self.results.run_results)}")

            sys.exit(0)

        signal.signal(signal.SIGINT, sigint_handler)

        pbar = tqdm(
            total=self.num_simulations,
            desc="Monte Carlo",
            unit="sim",
            disable=not self.progress_bar
        ) if self.progress_bar else None

        for run_idx in range(self.num_simulations):
            state_tracker['current_iteration'] = run_idx
            state_tracker['last_update_time'] = time.time()

            self.results.add_run(scenario.run_once(run_idx))
            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()

        if self.verbose:
            total = time.time() - start
            avg = total / self.num_simulations
            print(f"total runtime: {total}\navg runtime per simultation: {avg}")

        if self.verbose: print("aggregating results")
        start = time.time()
        self.results.aggregate_stats()
        if self.verbose: print(f"results crunched. took {time.time() - start}.")

        if self.verbose:
            print("scenarios complete")
            self.results.summary()
