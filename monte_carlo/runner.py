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
import pandas as pd

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
        return pd.DataFrame(self.run_results)

    @abstractmethod
    def aggregate_stats(self):
        # this is where any number crunching happens
        pass

    @abstractmethod
    def __repr__(self):
        # implement a descriptive name and comments
        pass

    def summary(self):
        print(f"Monte Carlo Summary")
        print("raw data results:")
        print(self.to_dataframe())
        print(f"analysis:\n{self.aggregated_stats}\n")


class Experiment:
    def get_state(self) -> Optional[Dict[str, any]]:
        """
        Override to provide current state for SIGINT debugging.
        
        Returns:
            Dict with experiment-specific state to display on Ctrl+C,
            or None if no debug state tracking is needed.
        """
        return None

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
        import signal
        import sys
        
        if self.verbose: print("running monte carlo...")

        start = time.time()

        # State tracking for SIGINT handler
        state_tracker = {
            'current_iteration': -1,
            'total_iterations': self.config.num_simulations,
            'start_time': start,
            'last_update_time': start
        }
        
        def sigint_handler(sig, frame):
            """Handle Ctrl+C by dumping current state and exiting gracefully"""
            print("\n" + "="*70)
            print("MONTE CARLO INTERRUPTED (SIGINT)")
            print("="*70)
            
            elapsed = time.time() - state_tracker['start_time']
            since_update = time.time() - state_tracker['last_update_time']
            current_iter = state_tracker['current_iteration']
            total_iter = state_tracker['total_iterations']
            
            print(f"\nProgress:")
            print(f"  Iteration: {current_iter + 1}/{total_iter} ({(current_iter+1)/total_iter*100:.1f}%)")
            print(f"  Total elapsed: {elapsed:.2f}s")
            if current_iter >= 0:
                print(f"  Average per iteration: {elapsed/(current_iter+1):.2f}s")
            print(f"  Time since last update: {since_update:.2f}s")
            
            # Determine if hung or just slow
            if since_update > 30:
                print(f"\n⚠️  WARNING: No update in {since_update:.1f}s - possible hang!")
            elif since_update > 10:
                print(f"\n⚠️  SLOW: Processing for {since_update:.1f}s - might be expensive operation")
            else:
                print(f"\n✓ Program is actively running (last update {since_update:.1f}s ago)")
            
            # Get experiment-specific debug state
            debug_state = experiment.get_state()
            if debug_state:
                print(f"\nExperiment Debug State:")
                for key, value in debug_state.items():
                    # Truncate long lists for readability
                    if isinstance(value, list) and len(value) > 5:
                        print(f"  {key}: {value[:5]} ... ({len(value)} total)")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"\nExperiment Debug State: (none available)")
            
            # Show partial results
            if self.results.run_results:
                print(f"\nPartial Results:")
                print(f"  Completed runs: {len(self.results.run_results)}")
                print(f"  Last result: {self.results.run_results[-1]}")
            
            print("\n" + "="*70)
            print("Exiting gracefully.")
            print("="*70 + "\n")
            sys.exit(0)
        
        # Register signal handler
        signal.signal(signal.SIGINT, sigint_handler)

        # Create progress bar if enabled
        pbar = tqdm(
            total=self.config.num_simulations,
            desc="Monte Carlo",
            unit="sim",
            disable=not self.config.progress_bar
        ) if self.config.progress_bar else None

        for run_idx in range(self.config.num_simulations):
            # Update state tracker before running experiment
            state_tracker['current_iteration'] = run_idx
            state_tracker['last_update_time'] = time.time()
            
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
