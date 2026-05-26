import os
import sys
import json
from datetime import datetime

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from monte_carlo.sweep import run_sweep
from monte_carlo.scenarios.rarity_weighted_inventory import RarityWeightedScenario
from alchemy.inventory import Inventory
from alchemy.database import IngredientsDatabase
import time


class _Tee:
    def __init__(self, *files): self.files = files
    def write(self, data):
        for f in self.files: f.write(data)
    def flush(self):
        for f in self.files: f.flush()


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
    return {k: v / total for k, v in scaled.items()}


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
    num_simulations = 320

    base_dist = Inventory.BASIC_RARITY_DIST.copy()

    rarity_multipliers = {
        "very_flat":    0.3,
        "flat":         0.5,
        "normal":       1.0,
        "steep":        2.0,
        "very_steep":   3.0,
        "extreme_steep": 5.0,
    }

    rarity_distributions = {
        name: scale_rarity_distribution(base_dist, mult)
        for name, mult in rarity_multipliers.items()
    }

    rarity_configurations = {
        name: {"total": 128, "distinct": 24, "rarity_dist": dist}
        for name, dist in rarity_distributions.items()
    }

    print("="*80)
    print("RARITY TOLERANCE ANALYSIS")
    print("="*80)
    print(f"Running {num_simulations} simulations per rarity distribution\n")

    print("Rarity Distributions:")
    for name, dist in rarity_distributions.items():
        print(f"\n{name}:")
        for rarity, weight in dist.items():
            print(f"  {rarity:15s}: {weight:6.4f}")

    start = time.time()
    results_by_distribution = run_sweep(RarityWeightedScenario, rarity_configurations, num_simulations, db=db, progress_bar=True)
    print(f"\nAll distributions completed in {time.time() - start:.2f}s")

    print("\n" + "="*80)
    print("RARITY DISTRIBUTION COMPARISON")
    print("="*80)

    for dist_name, result in results_by_distribution.items():
        avg_potions = result.aggregated_stats['average_potions']
        stderr_potions = result.aggregated_stats['stderr_potions']
        total_potions = result.aggregated_stats['total_potions']
        avg_value = result.aggregated_stats['average_value']
        stderr_value = result.aggregated_stats['stderr_value']
        print(f"\n{dist_name:20s}: avg_potions={avg_potions:6.2f} ±{stderr_potions:.2f}  avg_value={avg_value:8.0f} ±{stderr_value:.0f}  total_potions={total_potions:10d}")

    print("\n" + "="*80)
    print("INGREDIENT RARITY TOLERANCE")
    print("="*80)
    print("How ingredient performance changes across rarity distributions:\n")

    baseline_perf = results_by_distribution["normal"].aggregated_stats['average_performance']

    tolerance_scores = {}
    for ing_name in baseline_perf.keys():
        if baseline_perf[ing_name]["avg_potion_value"] is None:
            continue

        values_across_distributions = [
            results_by_distribution[dist_name].aggregated_stats['average_performance'][ing_name]["avg_potion_value"]
            for dist_name in rarity_distributions
            if ing_name in results_by_distribution[dist_name].aggregated_stats['average_performance']
            and results_by_distribution[dist_name].aggregated_stats['average_performance'][ing_name]["avg_potion_value"] is not None
        ]

        if len(values_across_distributions) >= 2:
            avg_value = sum(values_across_distributions) / len(values_across_distributions)
            variance = sum((v - avg_value) ** 2 for v in values_across_distributions) / len(values_across_distributions)
            std_dev = variance ** 0.5
            cv = std_dev / avg_value if avg_value > 0 else 0

            tolerance_scores[ing_name] = {
                'avg': avg_value,
                'std_dev': std_dev,
                'cv': cv,
                'min': min(values_across_distributions),
                'max': max(values_across_distributions),
            }

    print("Most STABLE ingredients (low variation across distributions):\n")
    for i, (ing_name, stats) in enumerate(sorted(tolerance_scores.items(), key=lambda x: x[1]['cv']), 1):
        print(f"  {i:2d}. {ing_name:30s} CV={stats['cv']:5.3f}  avg={stats['avg']:6.0f}  range=[{stats['min']:5.0f}, {stats['max']:5.0f}]")

    print("\n" + "="*80)
    print("Most VOLATILE ingredients (high variation across distributions):\n")
    for i, (ing_name, stats) in enumerate(sorted(tolerance_scores.items(), key=lambda x: x[1]['cv'], reverse=True), 1):
        print(f"  {i:2d}. {ing_name:30s} CV={stats['cv']:5.3f}  avg={stats['avg']:6.0f}  range=[{stats['min']:5.0f}, {stats['max']:5.0f}]")

    print("\n" + "="*80)
    print("INGREDIENT PERFORMANCE BY RARITY TYPE")
    print("="*80)

    for ing_name in baseline_perf.keys():
        if baseline_perf[ing_name]["avg_potion_value"] is None:
            continue

        ing_obj = next((ing for ing in db if ing.name == ing_name), None)
        if ing_obj is None:
            continue

        print(f"\n{ing_name} (rarity: {ing_obj.rarity}):")
        for dist_name, result in results_by_distribution.items():
            perf_map = result.aggregated_stats['average_performance']
            if ing_name in perf_map and perf_map[ing_name]["avg_potion_value"] is not None:
                pv = perf_map[ing_name]["avg_potion_value"]
                ct = perf_map[ing_name]["avg_contribution"]
                print(f"  {dist_name:20s}: potion_val={pv:6.0f}  contribution={ct:6.0f}")

    print("\n" + "="*80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output = {
        "metadata": {
            "num_simulations": num_simulations,
            "timestamp": timestamp,
            "distributions": rarity_distributions,
        },
        "distribution_comparison": {
            dist_name: {
                "avg_potions": result.aggregated_stats['average_potions'],
                "stderr_potions": result.aggregated_stats['stderr_potions'],
                "total_potions": result.aggregated_stats['total_potions'],
                "avg_value": result.aggregated_stats['average_value'],
                "stderr_value": result.aggregated_stats['stderr_value'],
            }
            for dist_name, result in results_by_distribution.items()
        },
        "ingredient_performance": {
            dist_name: {
                ing_name: {
                    "avg_potion_value": perf["avg_potion_value"],
                    "stderr_potion_value": perf["stderr_potion_value"],
                    "avg_contribution": perf["avg_contribution"],
                    "stderr_contribution": perf["stderr_contribution"],
                    "appearance_rate": perf["appearance_rate"],
                }
                for ing_name, perf in result.aggregated_stats['average_performance'].items()
            }
            for dist_name, result in results_by_distribution.items()
        },
        "tolerance_scores": tolerance_scores,
    }

    json_path = os.path.join(results_dir, f'rarity_{timestamp}.json')
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to {json_path}")


if __name__ == "__main__":
    run_rarity_analysis()
