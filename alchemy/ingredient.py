from __future__ import annotations

from .effect import Effect

class Ingredient:

    def __init__(self, name, id,
                 value, weight,
                 effect1, effect1_mag, effect1_dur,
                 effect2, effect2_mag, effect2_dur,
                 effect3, effect3_mag, effect3_dur,
                 effect4, effect4_mag, effect4_dur,
                 dlc, rarity, source):

        self.name = name
        self.id = id
        self.value = int(value)
        self.weight = float(weight)
        self.effect1 = effect1
        self.effect1_mag = int(effect1_mag)
        self.effect1_dur = int(effect1_dur)
        self.effect2 = effect2
        self.effect2_mag = int(effect2_mag)
        self.effect2_dur = int(effect2_dur)
        self.effect3 = effect3
        self.effect3_mag = int(effect3_mag)
        self.effect3_dur = int(effect3_dur)
        self.effect4 = effect4
        self.effect4_mag = int(effect4_mag)
        self.effect4_dur = int(effect4_dur)
        self.dlc = dlc
        self.rarity = rarity
        self.source = source

    @classmethod
    def from_csv_line(cls, line):
        """
        Parse a single row from master_ingredients.csv.

        Expected columns (19 total):
            ingredient_name, ingredient_id, base_value, weight,
            effect_1, effect_1_magnitude, effect_1_duration,
            effect_2, effect_2_magnitude, effect_2_duration,
            effect_3, effect_3_magnitude, effect_3_duration,
            effect_4, effect_4_magnitude, effect_4_duration,
            dlc, rarity, source_type
        """
        parts = line.strip().split(',')
        return cls(*parts)

    def get_effect_data(self, name):
        """Returns (magnitude, duration) for the named effect, or None if not present."""
        if self.effect1 == name:
            return (self.effect1_mag, self.effect1_dur)
        elif self.effect2 == name:
            return (self.effect2_mag, self.effect2_dur)
        elif self.effect3 == name:
            return (self.effect3_mag, self.effect3_dur)
        elif self.effect4 == name:
            return (self.effect4_mag, self.effect4_dur)
        else:
            return None

    def get_effect_names(self):
        return [self.effect1, self.effect2, self.effect3, self.effect4]

    def __repr__(self):
        effects = [self.effect1, self.effect2, self.effect3, self.effect4]
        return (f"Ingredient('{self.name}', value={self.value}, weight={self.weight}, "
                f"effects={effects})")


