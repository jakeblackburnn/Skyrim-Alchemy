"""
Monte Carlo Runner Module for ESV Skyrim alchemy analysis with random inventory generation
Created by J. Blackburn - Feb 1 2026

Last updated - Feb 14 2026
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import time
from tqdm import tqdm

@dataclass
class MonteCarloConfig:
    num_simulations: int = 10
    num_workers: int = 1
    seed: Optional[int] = None
    progress_bar: bool = False
    checkpoints: bool = False
    checkpoint_freq: Optional[int] = 1

    def __repr__(self):
        return str({
            "num_simulations": self.num_simulations,
            "num_workers": self.num_workers,
            "seed": self.seed,
            "checkpoints": self.checkpoints,
            "checkpoint_freq": self.checkpoint_freq,
        })

@dataclass
class MonteCarloResult(ABC):
    run_results:      List[Dict[str, any]] = field(default_factory=list)
    aggregated_stats: List[Dict[str, any]] = field(default_factory=list)

    config: MonteCarloConfig = field(default_factory=lambda: None)

    def add_run(self, run: Dict[str, any]):
        self.run_results.append(run)

    def to_dataframe(self):
        # TODO: figure out dataframes
        pass

    @abstractmethod
    def aggregate_stats(self):
        # this is where any number crunching happens
        pass

    @abstractmethod
    def __repr__(self):
        # implement a descriptive name and comments
        pass

    def summary(self):
        print(f"Monte Carlo Results Summary")
        print(f"configuration:\n{str(self.config)}\n")
        print(f"results:\n{len(self.run_results)} run entries.\n")
        print(f"analysis:\n{self.aggregated_stats}\n")


class Experiment:
    @abstractmethod
    def run_once(self) -> Dict[str, any]:
        # this is where the actual potionmaking stuff happens
        pass



class MonteCarlo: # main runner object

    def __init__(self, config: MonteCarloConfig, results: MonteCarloResult, verbose=False):
        self.verbose = verbose
        if verbose: print("creating monte carlo runner...")

        self.config = config
        if verbose: print("loaded config:\n" + str(config))

        self.results = results
        if verbose: print("loaded results object.\n" + str(results))


    def run(self, experiment: Experiment):
        if self.verbose: print("running monte carlo...")

        start = time.time()

        # Create progress bar if enabled
        pbar = tqdm(
            total=self.config.num_simulations,
            desc="Monte Carlo",
            unit="sim",
            disable=not self.config.progress_bar
        ) if self.config.progress_bar else None

        for run_idx in range(self.config.num_simulations):
            self.results.add_run(experiment.run_once(run_idx))
            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()

        if self.verbose: 
            total = time.time() - start
            avg = total / self.config.num_simulations
            print(f"total runtime: {total}\navg runtime per simultation: {avg}")

        if self.verbose: print("aggregating results")
        start = time.time()
        self.results.aggregate_stats()
        if self.verbose: print(f"results crunched. took {time.time() - start}.")

        if self.verbose:
            print("experiments complete")
            self.results.summary()
