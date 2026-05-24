from enum import Enum
import math
from .player import Player

class EffectType(Enum):
    FORTIFY = 1
    RESTORE = 2
    POISON = 3

# class for actual effects (in a potion)
#   NOT the same as a generic effect (in an ingredinent)
class RealizedEffect:
    def __init__(self, base_effect, player):
        self.name = base_effect.name
        self.base = base_effect  # Reference for type checks
        self.description_template = base_effect.description_template

        # Compute magnitude/duration based on variable_duration
        if base_effect.variable_duration:
            self.magnitude = base_effect.base_mag
            self.duration = base_effect._scale_dur(player)
        else:
            self.magnitude = base_effect._scale_mag(player)
            self.duration = base_effect.base_dur

        self.value = base_effect.value(player)

    def get_description(self):
        if self.description_template:
            return self.description_template.format(mag=self.magnitude, dur=self.duration)
        else:
            # Fallback to current format
            return f"{self.name}: {self.value} gold (mag={self.magnitude}, dur={self.duration})"

    # Delegate type checks to base effect
    @property
    def is_poison(self):
        return self.base.is_poison

    @property
    def is_fortify(self):
        return self.base.is_fortify

    @property
    def is_restore(self):
        return self.base.is_restore

    def __repr__(self):
        return (f"RealizedEffect('{self.name}', mag={self.magnitude}, "
                f"dur={self.duration}, value={self.value})")

class Effect:

    def __init__(self, name, mag, dur, cost, effect_type, variable_duration=False, description_template=None):

        self.name = name
        self.base_mag = mag
        self.base_dur = dur
        self.base_cost = cost
        self.description_template = description_template

        self.is_fortify = False
        self.is_restore = False
        self.is_poison = False

        match effect_type:
            case EffectType.FORTIFY:
                self.is_fortify = True
            case EffectType.RESTORE:
                self.is_restore = True
            case EffectType.POISON:
                self.is_poison = True

        self.variable_duration = variable_duration

    @classmethod
    def from_csv_line(cls, line):
        # CSV format: effect_name,effect_id,base_magnitude,base_duration,base_cost,effect_type,is_beneficial,varies_duration[,description_template]
        parts = line.strip().split(',')

        name = parts[0]
        base_mag = int(parts[2])
        base_dur = int(parts[3])
        base_cost = float(parts[4])
        varies_duration = parts[7].lower() == 'true'

        # Extract description template if present (column 8), backward compatible
        description_template = parts[8] if len(parts) > 8 and parts[8].strip() else None

        # Determine effect type based on is_beneficial flag and name
        is_beneficial = parts[6].lower() == 'true'

        if not is_beneficial:
            effect_type = EffectType.POISON
        elif name.startswith('Fortify'):
            effect_type = EffectType.FORTIFY
        elif name.startswith('Restore'):
            effect_type = EffectType.RESTORE
        else:
            effect_type = None

        return cls(name, base_mag, base_dur, base_cost, effect_type, varies_duration, description_template)

    def base_value(self):
        return self.value(Player())

    def value(self, player):
        if self.variable_duration:
            magnitude = self.base_mag
            duration = self._scale_dur(player)
        else:
            magnitude = self._scale_mag(player)
            duration = self.base_dur

        if duration == 0:
            duration = 10

        return math.floor(self.base_cost * pow(magnitude, 1.1) * pow(duration / 10, 1.1))

    # formula for scaling the magnitude or duration from actual game logic
    def _scale_factor(self, player):
        factor = 4 * (1 + player.alchemy_skill / 200)
        factor *= 1 + player.fortify_alchemy / 100

        factor *= 1 + (player.alchemist_perk / 100)
        factor *= 1 + (player.seeker_of_shadows / 100)
        factor *= 1 + (int(self.is_restore) * player.physician_perk / 100)
        factor *= 1 + (int(self.is_fortify) * player.benefactor_perk / 100) + (int(self.is_poison) * player.poisoner_perk / 100)

        return factor

    def _scale_mag(self, player):
        return round(self.base_mag * self._scale_factor(player))

    def _scale_dur(self, player):
        return round(self.base_dur * self._scale_factor(player))

    def realize(self, player):
        return RealizedEffect(self, player)

    def __repr__(self):
        if self.is_poison:
            effect_type = "Poison"
        elif self.is_fortify:
            effect_type = "Fortify"
        elif self.is_restore:
            effect_type = "Restore"
        else:
            effect_type = "Other"
        return (f"Effect('{self.name}', type={effect_type}, "
                f"base_mag={self.base_mag}, base_dur={self.base_dur}, base_cost={self.base_cost})")



if __name__ == "__main__":
    beginner = Player(15)
    advanced = Player(100)

    csv_line = "Damage Health,00073f32,5,0,3,destruction,false,false,Causes {mag} points of poison damage."
    effect_from_csv = Effect.from_csv_line(csv_line)

    print("--- Effect Tests ---")
    print(f"\n{effect_from_csv.name}: poison={effect_from_csv.is_poison}, base_mag={effect_from_csv.base_mag}, base_dur={effect_from_csv.base_dur}")

    print(f"Template: {effect_from_csv.description_template}")
    print(f"Beginner: {effect_from_csv.value(beginner)}, Advanced: {effect_from_csv.value(advanced)}")

    print("\n--- RealizedEffect Tests ---")
    realized_beginner = effect_from_csv.realize(beginner)
    realized_advanced = effect_from_csv.realize(advanced)

    print(f"Beginner realized: mag={realized_beginner.magnitude}, dur={realized_beginner.duration}, value={realized_beginner.value}")
    print(f"  Description: {realized_beginner.get_description()}")
    print(f"Advanced realized: mag={realized_advanced.magnitude}, dur={realized_advanced.duration}, value={realized_advanced.value}")
    print(f"  Description: {realized_advanced.get_description()}")
