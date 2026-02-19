from monte_carlo.runner import MonteCarlo, MonteCarloConfig, Experiment
from monte_carlo.experiments.easy_seven import EasyExperiment, EasyResult
from monte_carlo.experiments.avg_ingredient_value import AverageIngredientPerformance, AverageIngredientResult
from src.database import IngredientsDatabase

# set up experimental config
# should maybe be a way to this in oneline?
# MonteCarlo classmethod?
db     = IngredientsDatabase()
config = MonteCarloConfig(num_simulations=64000, progress_bar=True)
result = AverageIngredientResult(config=config, db=db)
exp    = AverageIngredientPerformance(db=db, inv_size=32)

runner = MonteCarlo(config, result, verbose=True)
runner.run(exp)
