"""
results.py — locate and load precomputed experiment results.

Experiments in experiments/ write timestamped JSON (e.g. base_perf_20260604_141627.json)
to settings.RESULTS_DIR. This module is the single place that knows where those
files live and how to find the newest one for a given experiment, so views stay
decoupled from the on-disk layout and naming convention.
"""
import glob
import json

from django.conf import settings

# Experiment name -> filename glob. Add a row here when a new experiment's
# results should be exposed to the web UI.
EXPERIMENT_PATTERNS = {
    "base_perf":         "base_perf_*.json",
    "perks":             "perks_*.json",
    "rarity":            "rarity_*.json",
    "profiles":          "profiles_*.json",
    "inventory_scaling": "inventory_scaling_*.json",
}


def load_latest(pattern):
    """Load the newest results JSON matching `pattern`, or None if none exist.

    Filenames carry a sortable YYYYMMDD_HHMMSS timestamp, so the lexically last
    match is the most recent.
    """
    files = sorted(glob.glob(str(settings.RESULTS_DIR / pattern)))
    if not files:
        return None
    with open(files[-1]) as f:
        return json.load(f)


def load_experiment(name):
    """Load the latest results for a named experiment, or None if unknown/absent."""
    pattern = EXPERIMENT_PATTERNS.get(name)
    if pattern is None:
        return None
    return load_latest(pattern)


def available_experiments():
    """Names of experiments that currently have at least one result file on disk."""
    return [name for name, pattern in EXPERIMENT_PATTERNS.items()
            if glob.glob(str(settings.RESULTS_DIR / pattern))]
