from __future__ import annotations

import csv
import warnings
from .effect import Effect
from .ingredient import Ingredient

class IngredientsDatabase:

    def __init__(self, data_dir="data"):
        self._ingredients = {}
        self._effects = {}
        self._load_ingredients(data_dir)
        self._load_effects(data_dir)

    def _load_ingredients(self, data_dir):
        with open(f"{data_dir}/master_ingredients.csv", newline='') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header

            for row in reader:
                line = ','.join(row)
                ingredient = Ingredient.from_csv_line(line)
                self._ingredients[ingredient.name] = ingredient

    def _load_effects(self, data_dir):
        with open(f"{data_dir}/effects.csv", newline='') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header

            for row in reader:
                line = ','.join(row)
                effect = Effect.from_csv_line(line)
                self._effects[effect.name] = effect

    def get_ingredient(self, name):
        return self._ingredients.get(name)

    def get_all_ingredients(self):
        return list(self._ingredients.values())

    def ingredient_effect(self, effect_name, ingredient):
        default_effect = self._effects.get(effect_name)
        if default_effect is None:
            return None

        effect_data = ingredient.get_effect_data(effect_name)
        if effect_data is None:
            return None

        mag, dur = effect_data

        ingredient_effect = Effect(
            name=default_effect.name,
            mag=mag,
            dur=dur,
            cost=default_effect.base_cost,
            effect_type=default_effect.effect_type,
            variable_duration=default_effect.variable_duration,
            description_template=default_effect.description_template
        )
        return ingredient_effect

    def __repr__(self):
        return f"IngredientsDatabase({len(self._ingredients)} ingredients loaded)"

    def __len__(self):
        return len(self._ingredients)

    def __contains__(self, name: str) -> bool:
        return name in self._ingredients

    def __getitem__(self, name: str):
        if name not in self._ingredients:
            raise KeyError(f"Ingredient '{name}' not found in database")
        return self._ingredients[name]

    def __iter__(self):
        return iter(self._ingredients.values())




