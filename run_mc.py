from monte_carlo.runner import MonteCarlo, MonteCarloConfig, Experiment
from monte_carlo.experiments.easy_seven import EasyExperiment, EasyResult
from monte_carlo.experiments.avg_ingredient_value import AverageIngredientPerformance, AverageIngredientResult
from monte_carlo.experiments.stable_test import StableInventoryResult, StableInventoryExperiment
from monte_carlo.experiments.weighted_test import WeightedInventoryResult, WeightedInventoryExperiment
from src.database import IngredientsDatabase

# set up experimental config
# should maybe be a way to this in oneline?
# MonteCarlo classmethod?
db     = IngredientsDatabase()
config = MonteCarloConfig(num_simulations=3200, progress_bar=True)

# TODO: rename these guys
# result = AverageIngredientResult(config=config, db=db)
# exp    = AverageIngredientPerformance(db=db, inv_size=32)

result = WeightedInventoryResult(config=config, db=db)
# medium sized inventory, reasonable for ~2hrs gameplay-ish
exp = WeightedInventoryExperiment(db=db, total=128, distinct=24) 

runner = MonteCarlo(config, result, verbose=True)
runner.run(exp)
