from .runner import run_monte_carlo, Scenario
from typing import Dict, Type
import hashlib


def run_sweep(
    scenario_cls: Type[Scenario],
    configurations: Dict[str, dict],
    num_simulations: int,
    db=None,
    progress_bar: bool = False,
    verbose: bool = False,
) -> Dict[str, Scenario]:
    """
    Run run_monte_carlo for each named configuration, returning {name: scenario}.

    `db` is forwarded to every scenario_cls call. Seeds are derived deterministically
    from each configuration name and num_simulations, so results are reproducible.
    """
    results = {}
    for name, kwargs in configurations.items():
        seed = int(hashlib.sha256(f"{name}:{num_simulations}".encode()).hexdigest(), 16) % (2 ** 32)
        scenario = scenario_cls(db=db, **kwargs)
        run_monte_carlo(scenario, n=num_simulations, seed=seed, progress_bar=progress_bar, verbose=verbose)
        results[name] = scenario
    return results
