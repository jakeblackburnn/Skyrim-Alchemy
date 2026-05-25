from .runner import MonteCarlo, MonteCarloResult, Scenario
from typing import Dict, Type
import hashlib


def run_sweep(
    scenario_cls: Type[Scenario],
    result_cls: Type[MonteCarloResult],
    configurations: Dict[str, dict],
    num_simulations: int,
    db=None,
    progress_bar: bool = False,
    verbose: bool = False,
) -> Dict[str, MonteCarloResult]:
    """
    Run MonteCarlo for each named configuration dict, returning {name: result}.

    Each entry in `configurations` maps a label to kwargs passed to scenario_cls.
    `db` is forwarded to both scenario_cls and result_cls (pass None to omit).
    """
    results = {}
    for name, kwargs in configurations.items():
        seed_data = f"{name}:{num_simulations}"
        seed = int(hashlib.sha256(seed_data.encode()).hexdigest(), 16) % (2 ** 32)

        result = result_cls(db=db)
        scenario = scenario_cls(db=db, **kwargs) if db is not None else scenario_cls(**kwargs)
        runner = MonteCarlo(result, num_simulations, progress_bar=progress_bar, verbose=verbose)
        runner.run(scenario, seed=seed)
        results[name] = result
    return results
