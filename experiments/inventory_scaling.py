import json
import time
from datetime import datetime

from experiments.utils import tee_stdout, RESULTS_DIR
from monte_carlo.sweep import run_sweep
from monte_carlo.scenarios.stable_inventory import StableInventoryScenario
from alchemy.database import IngredientsDatabase


# Grid axes. `distinct` is the diversity lever (drives recipe variety, and the
# combinatorial cost of enumerating valid potions). `stack_depth` sets total as a
# multiple of distinct (total = distinct * stack_depth), so the `total >= distinct`
# constraint always holds and each row shares a common "stack depth" interpretation.
DISTINCT_LEVELS = [4, 8, 16, 24, 32, 48, 64, 96, 111]
STACK_DEPTHS = [1, 2, 4, 8]
NUM_SIMULATIONS = 240


def _config_name(distinct, depth):
    return f"d{distinct:02d}_x{depth}"


def _build_configurations():
    """Return {name: {"total", "distinct"}} for every (distinct, stack_depth) cell."""
    configs = {}
    for distinct in DISTINCT_LEVELS:
        for depth in STACK_DEPTHS:
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
    header = f"{'distinct \\ depth':>16}" + "".join(f"{('x' + str(d)):>12}" for d in STACK_DEPTHS)
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for distinct in DISTINCT_LEVELS:
        row = f"{distinct:>16}"
        for depth in STACK_DEPTHS:
            row += f"{fmt % cell_value(distinct, depth):>12}"
        print(row)


def _run_inventory_scaling_inner():
    db = IngredientsDatabase()
    configurations = _build_configurations()

    print("=" * 80)
    print("INVENTORY SCALING ANALYSIS")
    print("=" * 80)
    print(f"Grid: {len(DISTINCT_LEVELS)} distinct levels x {len(STACK_DEPTHS)} stack depths "
          f"= {len(configurations)} cells")
    print(f"distinct levels: {DISTINCT_LEVELS}")
    print(f"stack depths:    {STACK_DEPTHS}  (total = distinct * depth)")
    print(f"Running {NUM_SIMULATIONS} simulations per cell (uniform sampling, default player)\n")

    start = time.time()
    results = run_sweep(StableInventoryScenario, configurations, NUM_SIMULATIONS, db=db, progress_bar=True)
    print(f"\nAll cells completed in {time.time() - start:.2f}s")

    # Index aggregated stats by (distinct, depth) for matrix rendering and JSON.
    cells = {}
    for distinct in DISTINCT_LEVELS:
        for depth in STACK_DEPTHS:
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

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

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
            "distinct_levels": DISTINCT_LEVELS,
            "stack_depths": STACK_DEPTHS,
        },
        "cells": {
            _config_name(d, x): cells[(d, x)]
            for d in DISTINCT_LEVELS
            for x in STACK_DEPTHS
        },
    }

    json_path = RESULTS_DIR / f'inventory_scaling_{timestamp}.json'
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {json_path}")


if __name__ == "__main__":
    run_inventory_scaling()
