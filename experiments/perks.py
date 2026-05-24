import os
import sys
import json
from datetime import datetime

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from monte_carlo.runner import MonteCarloConfig
from monte_carlo.sweep import run_sweep
from monte_carlo.scenarios.rarity_weighted_inventory import RarityWeightedResult, RarityWeightedScenario
from alchemy.database import IngredientsDatabase
from alchemy.player import Player
import time


class _Tee:
    def __init__(self, *files): self.files = files
    def write(self, data):
        for f in self.files: f.write(data)
    def flush(self):
        for f in self.files: f.flush()


def run_perk_analysis():
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    txt_path = os.path.join(results_dir, 'perks.txt')

    with open(txt_path, 'w') as txt_file:
        original_stdout = sys.stdout
        sys.stdout = _Tee(original_stdout, txt_file)

        try:
            _run_perk_analysis_inner(results_dir)
        finally:
            sys.stdout = original_stdout


def _run_perk_analysis_inner(results_dir):
    db = IngredientsDatabase()
    config = MonteCarloConfig(num_simulations=10000, progress_bar=True)

    perk_configurations = {
        "baseline":             {"player": Player()},
        "benefactor":           {"player": Player(is_benefactor=True)},
        "physician":            {"player": Player(is_physician=True)},
        "poisoner":             {"player": Player(is_poisoner=True)},
        "benefactor+physician": {"player": Player(is_benefactor=True, is_physician=True)},
        "benefactor+poisoner":  {"player": Player(is_benefactor=True, is_poisoner=True)},
        "physician+poisoner":   {"player": Player(is_physician=True, is_poisoner=True)},
        "all_perks":            {"player": Player(is_benefactor=True, is_physician=True, is_poisoner=True)},
    }

    for name in perk_configurations:
        perk_configurations[name].update({"total": 128, "distinct": 24})

    print("="*80)
    print("PERK SYNERGY ANALYSIS")
    print("="*80)
    print(f"Running {config.num_simulations} simulations per perk configuration\n")

    start = time.time()
    results_by_perk = run_sweep(RarityWeightedScenario, RarityWeightedResult, perk_configurations, config, db=db)
    print(f"\nAll configurations completed in {time.time() - start:.2f}s")

    print("\n" + "="*80)
    print("PERK COMPARISON SUMMARY")
    print("="*80)

    for perk_name, result in results_by_perk.items():
        avg_potions = result.aggregated_stats[0]['average_potions']
        total_potions = result.aggregated_stats[0]['total_potions']
        print(f"\n{perk_name:25s}: avg={avg_potions:6.2f}  total={total_potions:10d}")

    print("\n" + "="*80)
    print("INGREDIENT SYNERGY WITH PERKS")
    print("="*80)
    print("All ingredients by average value for each perk configuration:\n")

    for perk_name, result in results_by_perk.items():
        perf_map = result.aggregated_stats[3]['average_performance']

        print(f"\n{perk_name}:")
        print("-" * 40)

        for i, (ing_name, perf) in enumerate(list(perf_map.items()), 1):
            avg_value = perf["avg_value"]
            if avg_value is not None:
                print(f"  {i:2d}. {ing_name:30s} {avg_value:6.0f}")
            else:
                print(f"  {i:2d}. {ing_name:30s} N/A")

    baseline_perf = results_by_perk["baseline"].aggregated_stats[3]['average_performance']

    print("\n" + "="*80)
    print("INGREDIENT PERK SENSITIVITY")
    print("="*80)
    print("Ingredients that benefit most from perks (vs baseline):\n")

    perk_benefits = {}
    for ing_name in baseline_perf.keys():
        if baseline_perf[ing_name]["avg_value"] is None:
            continue

        max_benefit = 0
        best_perk = "none"

        for perk_name, result in results_by_perk.items():
            if perk_name == "baseline":
                continue

            perf_map = result.aggregated_stats[3]['average_performance']
            if ing_name in perf_map and perf_map[ing_name]["avg_value"] is not None:
                benefit = perf_map[ing_name]["avg_value"] - baseline_perf[ing_name]["avg_value"]
                if benefit > max_benefit:
                    max_benefit = benefit
                    best_perk = perk_name

        if max_benefit > 0:
            perk_benefits[ing_name] = (max_benefit, best_perk)

    sorted_benefits = sorted(perk_benefits.items(), key=lambda x: x[1][0], reverse=True)

    print("All ingredients by perk benefit:\n")
    for i, (ing_name, (benefit, best_perk)) in enumerate(sorted_benefits, 1):
        baseline_val = baseline_perf[ing_name]["avg_value"]
        pct_increase = (benefit / baseline_val * 100) if baseline_val > 0 else 0
        print(f"  {i:2d}. {ing_name:30s} +{benefit:6.0f} ({pct_increase:5.1f}%)  best: {best_perk}")

    print("\n" + "="*80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    perk_comparison = {
        perk_name: {
            "avg_potions": result.aggregated_stats[0]['average_potions'],
            "total_potions": result.aggregated_stats[0]['total_potions'],
        }
        for perk_name, result in results_by_perk.items()
    }

    ingredient_performance = {
        perk_name: {
            ing_name: {
                "avg_value": perf["avg_value"],
                "appearance_rate": perf["appearance_rate"],
            }
            for ing_name, perf in result.aggregated_stats[3]['average_performance'].items()
        }
        for perk_name, result in results_by_perk.items()
    }

    perk_sensitivity = {
        ing_name: {
            "max_benefit": benefit,
            "best_perk": best_perk,
            "pct_increase": (benefit / baseline_perf[ing_name]["avg_value"] * 100)
                if baseline_perf[ing_name]["avg_value"] and baseline_perf[ing_name]["avg_value"] > 0 else 0,
        }
        for ing_name, (benefit, best_perk) in sorted_benefits
    }

    output = {
        "metadata": {
            "num_simulations": config.num_simulations,
            "timestamp": timestamp,
        },
        "perk_comparison": perk_comparison,
        "ingredient_performance": ingredient_performance,
        "perk_sensitivity": perk_sensitivity,
    }

    json_path = os.path.join(results_dir, f'perks_{timestamp}.json')
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to {json_path}")


if __name__ == "__main__":
    run_perk_analysis()
