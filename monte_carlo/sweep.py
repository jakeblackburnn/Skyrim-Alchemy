from .runner import MonteCarlo, MonteCarloConfig, MonteCarloResult, Scenario
from typing import Dict, Type


def run_sweep(
    scenario_cls: Type[Scenario],
    result_cls: Type[MonteCarloResult],
    configurations: Dict[str, dict],
    config: MonteCarloConfig,
    db=None,
    verbose=False,
) -> Dict[str, MonteCarloResult]:
    """
    Run MonteCarlo for each named configuration dict, returning {name: result}.

    Each entry in `configurations` maps a label to kwargs passed to scenario_cls.
    `db` is forwarded to both scenario_cls and result_cls (pass None to omit).
    """
    results = {}
    for name, kwargs in configurations.items():
        result = result_cls(config=config, db=db)
        if db is not None:
            scenario = scenario_cls(db=db, **kwargs)
        else:
            scenario = scenario_cls(**kwargs)
        runner = MonteCarlo(config, result, verbose=verbose)
        runner.run(scenario)
        results[name] = result
    return results
