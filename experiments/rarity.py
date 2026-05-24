import os
import sys
import json
from datetime import datetime

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from monte_carlo.runner import MonteCarlo, MonteCarloConfig, Scenario, MonteCarloResult
from alchemy.inventory import Inventory
from alchemy.alembic import Alembic
from alchemy.player import Player
from alchemy.database import IngredientsDatabase
from dataclasses import dataclass, field
from typing import Dict
import time


class _Tee:
    def __init__(self, *files): self.files = files
    def write(self, data):
        for f in self.files: f.write(data)
    def flush(self):
        for f in self.files: f.flush()


class RarityToleranceExperiment(Scenario):
    """Weighted inventory experiment with configurable rarity distribution"""

    def __init__(self, db=None, player=None, total=14, distinct=7, rarity_dist=None):
        if db is None:
            db = IngredientsDatabase()
        if player is None:
            player = Player()
        self.db = db
        self.player = player
        self.inv_total = total
        self.inv_distinct = distinct
        self.rarity_dist = rarity_dist

        self.running = False
        self.run_idx = 0
        self.inv = None
        self.alembic = None
        self.potions = None

    def get_state(self) -> Dict[str, any]:
        return {
            "running": self.running,
            "run_idx": self.run_idx,
            "inv": self.inv,
            "alembic": self.alembic,
            "potions": self.potions,
        }

    def run_once(self, run_idx) -> Dict[str, int]:
        self.running = True
        self.run_idx = run_idx
        start = time.time()

        self.inv = Inventory.generate_weighted(self.db, self.inv_total, self.inv_distinct, self.rarity_dist)
        self.alembic = Alembic(self.db, self.player, self.inv)
        self.potions = self.alembic.exhaust_inventory(strategy="lazy")

        ingmap = self.alembic.ingredients_map

        simtime = time.time() - start
        self.running = False

        return {
            "run_idx": run_idx,
            "num_potions": len(self.potions),
            "ingredients_map": ingmap,
            "simulation_time": simtime,
        }


@dataclass
class RarityToleranceResult(MonteCarloResult):

    def __repr__(self):
        return "Rarity Tolerance Experiment - tests ingredient performance across rarity distributions"

    def aggregate_stats(self):
        start = time.time()
        potion_stats = self._average_and_total_potions()
        self.aggregated_stats.append(potion_stats)

        simtime_stats = self._average_and_total_simtime()
        self.aggregated_stats.append(simtime_stats)

        self.aggregated_stats.append({"result aggregation time": time.time() - start})

        self.aggregated_stats.append(self._average_ingredient_performance())


def scale_rarity_distribution(base_dist, multiplier):
    """
    Scale rarity distribution to favor/penalize rare ingredients.
    multiplier < 1: rare ingredients become MORE likely (flattening)
    multiplier > 1: rare ingredients become LESS likely (steepening)
    """
    common_weight = base_dist["common"]
    scaled = {}

    for rarity, weight in base_dist.items():
        ratio = weight / common_weight
        new_ratio = ratio ** multiplier
        scaled[rarity] = new_ratio

    total = sum(scaled.values())
    normalized = {k: v/total for k, v in scaled.items()}

    return normalized


def run_rarity_analysis():
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    txt_path = os.path.join(results_dir, 'rarity.txt')

    with open(txt_path, 'w') as txt_file:
        original_stdout = sys.stdout
        sys.stdout = _Tee(original_stdout, txt_file)

        try:
            _run_rarity_analysis_inner(results_dir)
        finally:
            sys.stdout = original_stdout


def _run_rarity_analysis_inner(results_dir):
    db = IngredientsDatabase()
    config = MonteCarloConfig(num_simulations=10000, progress_bar=True)

    base_dist = Inventory.BASIC_RARITY_DIST.copy()

    rarity_multipliers = {
        "very_flat": 0.3,
        "flat": 0.5,
        "normal": 1.0,
        "steep": 2.0,
        "very_steep": 3.0,
        "extreme_steep": 5.0,
    }

    rarity_distributions = {}
    for name, mult in rarity_multipliers.items():
        rarity_distributions[name] = scale_rarity_distribution(base_dist, mult)

    results_by_distribution = {}

    print("="*80)
    print("RARITY TOLERANCE ANALYSIS")
    print("="*80)
    print(f"Running {config.num_simulations} simulations per rarity distribution\n")

    print("Rarity Distributions:")
    for name, dist in rarity_distributions.items():
        print(f"\n{name}:")
        for rarity, weight in dist.items():
            print(f"  {rarity:15s}: {weight:6.4f}")

    for dist_name, rarity_dist in rarity_distributions.items():
        print(f"\n{'='*80}")
        print(f"Testing: {dist_name}")
        print(f"{'='*80}")

        result = RarityToleranceResult(config=config, db=db)
        exp = RarityToleranceExperiment(db=db, player=Player(), total=128, distinct=24, rarity_dist=rarity_dist)

        runner = MonteCarlo(config, result, verbose=False)
        start = time.time()
        runner.run(exp)
        elapsed = time.time() - start

        results_by_distribution[dist_name] = result

        print(f"\nCompleted in {elapsed:.2f}s")
        print(f"Average potions: {result.aggregated_stats[0]['average_potions']:.2f}")

    print("\n" + "="*80)
    print("RARITY DISTRIBUTION COMPARISON")
    print("="*80)

    for dist_name in rarity_distributions.keys():
        result = results_by_distribution[dist_name]
        avg_potions = result.aggregated_stats[0]['average_potions']
        total_potions = result.aggregated_stats[0]['total_potions']
        print(f"\n{dist_name:20s}: avg={avg_potions:6.2f}  total={total_potions:10d}")

    print("\n" + "="*80)
    print("INGREDIENT RARITY TOLERANCE")
    print("="*80)
    print("How ingredient performance changes across rarity distributions:\n")

    baseline_perf = results_by_distribution["normal"].aggregated_stats[3]['average_performance']

    tolerance_scores = {}
    for ing_name in baseline_perf.keys():
        if baseline_perf[ing_name]["avg_value"] is None:
            continue

        values_across_distributions = []
        for dist_name in rarity_distributions.keys():
            perf_map = results_by_distribution[dist_name].aggregated_stats[3]['average_performance']
            if ing_name in perf_map and perf_map[ing_name]["avg_value"] is not None:
                values_across_distributions.append(perf_map[ing_name]["avg_value"])

        if len(values_across_distributions) >= 2:
            avg_value = sum(values_across_distributions) / len(values_across_distributions)
            variance = sum((v - avg_value) ** 2 for v in values_across_distributions) / len(values_across_distributions)
            std_dev = variance ** 0.5
            coefficient_of_variation = std_dev / avg_value if avg_value > 0 else 0

            tolerance_scores[ing_name] = {
                'avg': avg_value,
                'std_dev': std_dev,
                'cv': coefficient_of_variation,
                'min': min(values_across_distributions),
                'max': max(values_across_distributions),
            }

    print("Most STABLE ingredients (low variation across distributions):\n")
    sorted_by_stability = sorted(tolerance_scores.items(), key=lambda x: x[1]['cv'])
    for i, (ing_name, stats) in enumerate(sorted_by_stability, 1):
        print(f"  {i:2d}. {ing_name:30s} CV={stats['cv']:5.3f}  avg={stats['avg']:6.0f}  range=[{stats['min']:5.0f}, {stats['max']:5.0f}]")

    print("\n" + "="*80)
    print("Most VOLATILE ingredients (high variation across distributions):\n")
    sorted_by_volatility = sorted(tolerance_scores.items(), key=lambda x: x[1]['cv'], reverse=True)
    for i, (ing_name, stats) in enumerate(sorted_by_volatility, 1):
        print(f"  {i:2d}. {ing_name:30s} CV={stats['cv']:5.3f}  avg={stats['avg']:6.0f}  range=[{stats['min']:5.0f}, {stats['max']:5.0f}]")

    print("\n" + "="*80)
    print("INGREDIENT PERFORMANCE BY RARITY TYPE")
    print("="*80)

    for ing_name in list(baseline_perf.keys()):
        if baseline_perf[ing_name]["avg_value"] is None:
            continue

        ing_obj = None
        for ing in db:
            if ing.name == ing_name:
                ing_obj = ing
                break

        if ing_obj is None:
            continue

        print(f"\n{ing_name} (rarity: {ing_obj.rarity}):")
        for dist_name in rarity_distributions.keys():
            perf_map = results_by_distribution[dist_name].aggregated_stats[3]['average_performance']
            if ing_name in perf_map and perf_map[ing_name]["avg_value"] is not None:
                print(f"  {dist_name:20s}: {perf_map[ing_name]['avg_value']:6.0f}")

    print("\n" + "="*80)

    # Build structured JSON output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    distribution_comparison = {}
    for dist_name in rarity_distributions.keys():
        result = results_by_distribution[dist_name]
        distribution_comparison[dist_name] = {
            "avg_potions": result.aggregated_stats[0]['average_potions'],
            "total_potions": result.aggregated_stats[0]['total_potions'],
        }

    ingredient_performance = {}
    for dist_name in rarity_distributions.keys():
        result = results_by_distribution[dist_name]
        perf_map = result.aggregated_stats[3]['average_performance']
        ingredient_performance[dist_name] = {
            ing_name: {
                "avg_value": perf["avg_value"],
                "appearance_rate": perf["appearance_rate"],
            }
            for ing_name, perf in perf_map.items()
        }

    tolerance_scores_json = {
        ing_name: {
            "avg": stats["avg"],
            "std_dev": stats["std_dev"],
            "cv": stats["cv"],
            "min": stats["min"],
            "max": stats["max"],
        }
        for ing_name, stats in tolerance_scores.items()
    }

    output = {
        "metadata": {
            "num_simulations": config.num_simulations,
            "timestamp": timestamp,
            "distributions": {name: dist for name, dist in rarity_distributions.items()},
        },
        "distribution_comparison": distribution_comparison,
        "ingredient_performance": ingredient_performance,
        "tolerance_scores": tolerance_scores_json,
    }

    json_path = os.path.join(results_dir, f'rarity_{timestamp}.json')
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to {json_path}")


if __name__ == "__main__":
    run_rarity_analysis()
