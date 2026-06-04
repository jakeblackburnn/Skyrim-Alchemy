"""
serializers.py — turn engine objects into the JSON shapes the SPA expects.

These key names are part of the contract with the React frontend
(window.__INGREDIENTS__ / window.__EFFECTS__); do not rename without updating
the JS that reads them.
"""
import json


def serialize_ingredients(db):
    return [
        {
            "name":   ing.name,
            "value":  ing.value,
            "weight": ing.weight,
            "rarity": ing.rarity,
            "dlc":    ing.dlc,
            "source": ing.source,
            "effects": [
                {"name": ing.effect1, "mag": ing.effect1_mag, "dur": ing.effect1_dur},
                {"name": ing.effect2, "mag": ing.effect2_mag, "dur": ing.effect2_dur},
                {"name": ing.effect3, "mag": ing.effect3_mag, "dur": ing.effect3_dur},
                {"name": ing.effect4, "mag": ing.effect4_mag, "dur": ing.effect4_dur},
            ],
        }
        for ing in db
    ]


def serialize_effects(db):
    return [
        {
            "name":            eff.name,
            "base_cost":       eff.base_cost,
            "base_magnitude":  eff.base_mag,
            "base_duration":   eff.base_dur,
            "is_beneficial":   not eff.is_poison,
            "is_poison":       eff.is_poison,
            "varies_duration": eff.variable_duration,
        }
        for eff in db._effects.values()
    ]


def base_context(db):
    """JSON-serialised ingredient + effect data injected into every page."""
    return {
        "ingredients_json": json.dumps(serialize_ingredients(db)),
        "effects_json":     json.dumps(serialize_effects(db)),
    }
