"""base ingredient performance experiment 

run a ton of sims with flat sampling and medium inventory
main result: average performance & contribution of each ingredient
"""

import json
import time
from datetime import datetime

from experiments.utils import tee_stdout, RESULTS_DIR

from monte_carlo.scenarios.stable_inventory import StableInventoryScenario
from monte_carlo.runner import run_monte_carlo 
from alchemy.database import IngredientsDatabase


def run_base_perf():
    RESULTS_DIR.mkdir(exist_ok=True)
    with tee_stdout(RESULTS_DIR / 'base_perf.txt'):
        base_perf_inner()

def base_perf_inner():

    db = IngredientsDatabase()
    base_scenario = StableInventoryScenario(total=200, distinct=50, db=db) # half of total and 

    start = time.time()
    res = run_monte_carlo(base_scenario, n=12800, seed=42, progress_bar=True) 
    print(f"simulation complete in {time.time() - start:.2f}s")
    
    stats = res.aggregated_stats
    print(stats)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = RESULTS_DIR / f'base_perf_{timestamp}.json'
    with open(json_path, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\nResults saved to {json_path}")

if __name__ == "__main__":
    run_base_perf()
