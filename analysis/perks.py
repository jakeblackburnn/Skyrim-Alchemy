import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from monte_carlo.runner import MonteCarlo, MonteCarloConfig
from monte_carlo.experiments.weighted_test import WeightedInventoryResult, WeightedInventoryExperiment
from src.database import IngredientsDatabase
from src.player import Player
import time


def run_perk_analysis():
    db = IngredientsDatabase()
    config = MonteCarloConfig(num_simulations=10000, progress_bar=True)
    
    perk_configurations = {
        "baseline": Player(),
        "benefactor": Player(is_benefactor=True),
        "physician": Player(is_physician=True),
        "poisoner": Player(is_poisoner=True),
        "benefactor+physician": Player(is_benefactor=True, is_physician=True),
        "benefactor+poisoner": Player(is_benefactor=True, is_poisoner=True),
        "physician+poisoner": Player(is_physician=True, is_poisoner=True),
        "all_perks": Player(is_benefactor=True, is_physician=True, is_poisoner=True),
    }
    
    results_by_perk = {}
    
    print("="*80)
    print("PERK SYNERGY ANALYSIS")
    print("="*80)
    print(f"Running {config.num_simulations} simulations per perk configuration\n")
    
    for perk_name, player in perk_configurations.items():
        print(f"\n{'='*80}")
        print(f"Testing: {perk_name}")
        print(f"Player: {player}")
        print(f"{'='*80}")
        
        result = WeightedInventoryResult(config=config, db=db)
        exp = WeightedInventoryExperiment(db=db, player=player, total=128, distinct=24)
        
        runner = MonteCarlo(config, result, verbose=False)
        start = time.time()
        runner.run(exp)
        elapsed = time.time() - start
        
        results_by_perk[perk_name] = result
        
        print(f"\nCompleted in {elapsed:.2f}s")
        print(f"Average potions: {result.aggregated_stats[0]['average_potions']:.2f}")
    
    print("\n" + "="*80)
    print("PERK COMPARISON SUMMARY")
    print("="*80)
    
    for perk_name in perk_configurations.keys():
        result = results_by_perk[perk_name]
        avg_potions = result.aggregated_stats[0]['average_potions']
        total_potions = result.aggregated_stats[0]['total_potions']
        print(f"\n{perk_name:25s}: avg={avg_potions:6.2f}  total={total_potions:10d}")
    
    print("\n" + "="*80)
    print("INGREDIENT SYNERGY WITH PERKS")
    print("="*80)
    print("Top 10 ingredients by average value for each perk configuration:\n")
    
    for perk_name in perk_configurations.keys():
        result = results_by_perk[perk_name]
        perf_map = result.aggregated_stats[3]['average_performance']
        
        print(f"\n{perk_name}:")
        print("-" * 40)
        
        top_10 = list(perf_map.items())[:10]
        for i, (ing_name, perf) in enumerate(top_10, 1):
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

    print("Top 20 ingredients by perk benefit:\n")
    for i, (ing_name, (benefit, best_perk)) in enumerate(sorted_benefits[:20], 1):
        baseline_val = baseline_perf[ing_name]["avg_value"]
        pct_increase = (benefit / baseline_val * 100) if baseline_val > 0 else 0
        print(f"  {i:2d}. {ing_name:30s} +{benefit:6.0f} ({pct_increase:5.1f}%)  best: {best_perk}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    run_perk_analysis()
