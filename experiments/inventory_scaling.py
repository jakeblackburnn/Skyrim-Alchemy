""" 
Inventory Scaling Experiment - Tracking value efficiency at different inventory scales 

    >>> Notes:
inventory setup is driven in terms of total number of ingredients and number of distinct ingredients.
This should give some idea of when to perform alchemy and when to continue stockpiling ingredients

Based on my intuition about the alchemy system, I expect rapid improvement in gold value in the number of distinct ingredients 
and diminishing returns in the higher ranges, due to the intense connectivity of the ingredient compatability graph. 

Results from this experiment could be connected to compatability graph connectivity, and reframed in terms of perk progression as well, 
i.e., waiting to accumulate more ingredients increases efficiency, but also slows perk progression and could hamper overall progression
in the long run
"""

import json
import time
from datetime import datetime

from experiments.utils import tee_stdout, RESULTS_DIR
from monte_carlo.sweep import run_sweep
from monte_carlo.scenarios.stable_inventory import StableInventoryScenario
from alchemy.database import IngredientsDatabase


# Grid axes: 
#   DISTINCT_INGS - number of distinct ingredients
#   SIZE_MULTS - multiplier to get total inventory size
DISTINCT_INGS = [4, 8, 16, 24, 32, 48, 64, 96, 111] # 111 maxxes 
SIZE_MULTS = [1, 2, 4, 8]
NUM_SIMULATIONS = 240


def _config_name(distinct, depth):
    return f"d{distinct:02d}_x{depth}"


def _build_configurations():
    """Return {name: {"total", "distinct"}} for every (distinct, stack_depth) cell."""
    configs = {}
    for distinct in DISTINCT_INGS:
        for depth in SIZE_MULTS:
            configs[_config_name(distinct, depth)] = {
                "total": distinct * depth,
                "distinct": distinct,
            }
    return configs


def run_inventory_scaling():
    RESULTS_DIR.mkdir(exist_ok=True)
    with tee_stdout(RESULTS_DIR / 'inventory_scaling.txt'):
        _run_inventory_scaling_inner()


def _print_matrix(title, cell_value, fmt):
    """Print a distinct x stack_depth matrix; cell_value(distinct, depth) -> float."""
    print(f"\n{title}")
    header = f"{'distinct \\ depth':>16}" + "".join(f"{('x' + str(d)):>12}" for d in SIZE_MULTS)
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for distinct in DISTINCT_INGS:
        row = f"{distinct:>16}"
        for depth in SIZE_MULTS:
            row += f"{fmt % cell_value(distinct, depth):>12}"
        print(row)


def _run_inventory_scaling_inner():
    db = IngredientsDatabase()
    configurations = _build_configurations()

    print("INVENTORY SCALING ANALYSIS\n")
    print(f"distinct ingredients: {DISTINCT_INGS}")
    print(f"total inventory size multipliers:    {SIZE_MULTS}")
    print(f"Running {NUM_SIMULATIONS} simulations per grid cell\n")

    start = time.time()
    results = run_sweep(StableInventoryScenario, configurations, NUM_SIMULATIONS, db=db, progress_bar=True)
    print(f"\nAll cells completed in {time.time() - start:.2f}s")

    # Index aggregated stats by (distinct, size) for matrix rendering and JSON.
    cells = {}
    for distinct in DISTINCT_INGS:
        for depth in SIZE_MULTS:
            stats = results[_config_name(distinct, depth)].aggregated_stats
            total = distinct * depth
            cells[(distinct, depth)] = {
                "total": total,
                "distinct": distinct,
                "avg_value": stats["average_value"],
                "stderr_value": stats["stderr_value"],
                "avg_potions": stats["average_potions"],
                "stderr_potions": stats["stderr_potions"],
                "gold_per_ingredient": stats["average_value"] / total,
            }

    print("RESULTS")

    _print_matrix(
        "Total gold (avg total_value per inventory)",
        lambda d, x: cells[(d, x)]["avg_value"],
        "%.0f",
    )
    _print_matrix(
        "Gold per ingredient invested (avg_value / total)",
        lambda d, x: cells[(d, x)]["gold_per_ingredient"],
        "%.1f",
    )
    _print_matrix(
        "Avg potions brewed per inventory",
        lambda d, x: cells[(d, x)]["avg_potions"],
        "%.1f",
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "metadata": {
            "num_simulations": NUM_SIMULATIONS,
            "timestamp": timestamp,
            "distinct_ings": DISTINCT_INGS,
            "size_mults": SIZE_MULTS,
        },
        "cells": {
            _config_name(d, x): cells[(d, x)]
            for d in DISTINCT_INGS
            for x in SIZE_MULTS
        },
    }

    json_path = RESULTS_DIR / f'inventory_scaling_{timestamp}.json'
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {json_path}")


if __name__ == "__main__":
    run_inventory_scaling()
