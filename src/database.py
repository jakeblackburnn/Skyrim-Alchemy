import csv
import warnings
from .effect import Effect, EffectType
from .ingredient import Ingredient

class IngredientsDatabase:

    def __init__(self, data_dir="data"):
        self._ingredients = {}  # Dict[str, Ingredient]
        self._effects = {}  # Dict[str, Effect]
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

        if default_effect.is_fortify:
            effect_type = EffectType.FORTIFY
        elif default_effect.is_restore:
            effect_type = EffectType.RESTORE
        elif default_effect.is_poison:
            effect_type = EffectType.POISON
        else:
            effect_type = None

        # Create a new Effect object with ingredient-specific values
        # (don't modify the cached default_effect)
        ingredient_effect = Effect(
            name=default_effect.name,
            mag=mag,
            dur=dur,
            cost=default_effect.base_cost,
            effect_type=effect_type,
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





class EffectsDatabase: 

    def __init__(self, data_dir="data"):
        self.effects_file = open(f"{data_dir}/effects.csv", newline = '')
        self.effects_reader = csv.reader(self.effects_file)

    def default_effect(self, name):
        self.effects_file.seek(0)
        next(self.effects_reader)

        for row in self.effects_reader:
            effect_name = row[0]
            if effect_name == name:
                line = ','.join(row)
                return Effect.from_csv_line(line)

        return None

    def ingredient_effect(self, effect_name, ingredient):
        default_effect = self.default_effect(effect_name)
        if default_effect is None:
            return None

        effect_data = ingredient.get_effect_data(effect_name)
        if effect_data is None:
            return None

        mag, dur = effect_data
        default_effect.base_mag = mag
        default_effect.base_dur = dur

        return default_effect

    def __del__(self):
        self.effects_file.close()

if __name__ == "__main__":

    ing_db = IngredientsDatabase()
    print(ing_db)
