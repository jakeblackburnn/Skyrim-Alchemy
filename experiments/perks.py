import os
import json
from datetime import datetime

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from experiments.utils import tee_stdout
from monte_carlo.sweep import run_sweep
from monte_carlo.scenarios.rarity_weighted_inventory import RarityWeightedScenario
from alchemy.database import IngredientsDatabase
from alchemy.player import Player
import time


def run_perk_analysis():
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    txt_path = os.path.join(results_dir, 'perks.txt')

    with tee_stdout(txt_path):
        _run_perk_analysis_inner(results_dir)


def _run_perk_analysis_inner(results_dir):
    db = IngredientsDatabase()
    num_simulations = 320

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
    print(f"Running {num_simulations} simulations per perk configuration\n")

    start = time.time()
    results_by_perk = run_sweep(RarityWeightedScenario, perk_configurations, num_simulations, db=db, progress_bar=True)
    print(f"\nAll configurations completed in {time.time() - start:.2f}s")

    print("\n" + "="*80)
    print("PERK COMPARISON SUMMARY")
    print("="*80)

    for perk_name, result in results_by_perk.items():
        avg_potions = result.aggregated_stats['average_potions']
        stderr_potions = result.aggregated_stats['stderr_potions']
        total_potions = result.aggregated_stats['total_potions']
        avg_value = result.aggregated_stats['average_value']
        stderr_value = result.aggregated_stats['stderr_value']
        print(f"\n{perk_name:25s}: avg_potions={avg_potions:6.2f} ±{stderr_potions:.2f}  avg_value={avg_value:8.0f} ±{stderr_value:.0f}  total_potions={total_potions:10d}")

    print("\n" + "="*80)
    print("INGREDIENT SYNERGY WITH PERKS")
    print("="*80)
    print("All ingredients by average value for each perk configuration:\n")

    for perk_name, result in results_by_perk.items():
        perf_map = result.aggregated_stats['average_performance']

        print(f"\n{perk_name}:")
        print("-" * 40)

        for i, (ing_name, perf) in enumerate(list(perf_map.items()), 1):
            pv = perf["avg_potion_value"]
            ct = perf["avg_contribution"]
            if pv is not None:
                print(f"  {i:2d}. {ing_name:30s} potion_val={pv:6.0f}  contribution={ct:6.0f}")
            else:
                print(f"  {i:2d}. {ing_name:30s} N/A")

    baseline_perf = results_by_perk["baseline"].aggregated_stats['average_performance']

    print("\n" + "="*80)
    print("INGREDIENT PERK SENSITIVITY")
    print("="*80)
    print("Ingredients that benefit most from perks (vs baseline):\n")

    perk_benefits = {}
    for ing_name in baseline_perf.keys():
        if baseline_perf[ing_name]["avg_potion_value"] is None:
            continue

        max_benefit = 0
        best_perk = "none"

        for perk_name, result in results_by_perk.items():
            if perk_name == "baseline":
                continue

            perf_map = result.aggregated_stats['average_performance']
            if ing_name in perf_map and perf_map[ing_name]["avg_potion_value"] is not None:
                benefit = perf_map[ing_name]["avg_potion_value"] - baseline_perf[ing_name]["avg_potion_value"]
                if benefit > max_benefit:
                    max_benefit = benefit
                    best_perk = perk_name

        if max_benefit > 0:
            perk_benefits[ing_name] = (max_benefit, best_perk)

    sorted_benefits = sorted(perk_benefits.items(), key=lambda x: x[1][0], reverse=True)

    print("All ingredients by perk benefit:\n")
    for i, (ing_name, (benefit, best_perk)) in enumerate(sorted_benefits, 1):
        baseline_val = baseline_perf[ing_name]["avg_potion_value"]
        pct_increase = (benefit / baseline_val * 100) if baseline_val > 0 else 0
        print(f"  {i:2d}. {ing_name:30s} +{benefit:6.0f} ({pct_increase:5.1f}%)  best: {best_perk}")

    print("\n" + "="*80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    perk_comparison = {
        perk_name: {
            "avg_potions": result.aggregated_stats['average_potions'],
            "stderr_potions": result.aggregated_stats['stderr_potions'],
            "total_potions": result.aggregated_stats['total_potions'],
            "avg_value": result.aggregated_stats['average_value'],
            "stderr_value": result.aggregated_stats['stderr_value'],
        }
        for perk_name, result in results_by_perk.items()
    }

    ingredient_performance = {
        perk_name: {
            ing_name: {
                "avg_potion_value": perf["avg_potion_value"],
                "stderr_potion_value": perf["stderr_potion_value"],
                "avg_contribution": perf["avg_contribution"],
                "stderr_contribution": perf["stderr_contribution"],
                "appearance_rate": perf["appearance_rate"],
            }
            for ing_name, perf in result.aggregated_stats['average_performance'].items()
        }
        for perk_name, result in results_by_perk.items()
    }

    perk_sensitivity = {
        ing_name: {
            "max_benefit": benefit,
            "best_perk": best_perk,
            "pct_increase": (benefit / baseline_perf[ing_name]["avg_potion_value"] * 100)
                if baseline_perf[ing_name]["avg_potion_value"] and baseline_perf[ing_name]["avg_potion_value"] > 0 else 0,
        }
        for ing_name, (benefit, best_perk) in sorted_benefits
    }

    output = {
        "metadata": {
            "num_simulations": num_simulations,
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
