from monte_carlo.runner import MonteCarlo, MonteCarloConfig, Experiment
from monte_carlo.experiments.easy_seven import EasyExperiment, EasyResult

# set up experimental config
# should maybe be a way to this in oneline?
# MonteCarlo classmethod?
config = MonteCarloConfig(num_simulations=1000, progress_bar=True)
result = EasyResult(config=config)
exp    = EasyExperiment(inv_size=3)

runner = MonteCarlo(config, result, verbose=True)
runner.run(exp)

print(result.to_dataframe())
