import numpy as np
from .ingredient import Ingredient
from .database import IngredientsDatabase
from .effect import Effect
from .player import Player
from typing import Set

class Potion:

    def __init__(self, ingredients: Set, player, ingredients_db):
        # Validate ingredient count
        if len(ingredients) not in [2, 3]:
            raise ValueError(f"Potion requires 2 or 3 ingredients, got {len(ingredients)}")

        # Find common effects across ingredients
        all_effect_names = []
        for ingredient in ingredients:
            all_effect_names.extend(ingredient.get_effect_names())

        # Count occurrences and keep only effects shared by 2+ ingredients
        effect_counts = {}
        for effect_name in all_effect_names:
            effect_counts[effect_name] = effect_counts.get(effect_name, 0) + 1
        common_effect_names = {name for name, count in effect_counts.items() if count >= 2}

        # Validate that common effects exist
        if not common_effect_names:
            ingredient_names = [ing.name for ing in ingredients]
            raise ValueError(f"No common effects found among ingredients: {ingredient_names}")

        # Build Effect objects only for common effects, grouped by effect name
        # Track which ingredients contribute to validate all participate
        effect_groups = {}
        contributing_ingredients = set()
        for ingredient in ingredients:
            for effect_name in ingredient.get_effect_names():
                if effect_name in common_effect_names:
                    contributing_ingredients.add(ingredient.name)

                    # create ingredient effect object
                    effect = ingredients_db.ingredient_effect(effect_name, ingredient)

                    if effect_name not in effect_groups:
                        effect_groups[effect_name] = []
                    effect_groups[effect_name].append(effect)

        # Validate that all ingredients contribute at least one effect
        if len(contributing_ingredients) != len(ingredients):
            non_contributing = [ing.name for ing in ingredients if ing.name not in contributing_ingredients]
            raise ValueError(
                f"Ingredient(s) {non_contributing} share no effects with other ingredients"
            )

        # Keep only the highest base value effect from each group
        base_effects = []
        for effect_name, effect_list in effect_groups.items():
            base_values = [effect.base_value() for effect in effect_list]
            highest_idx = np.argmax(base_values)
            base_effects.append(effect_list[highest_idx])


        base_costs = [effect.base_value() for effect in base_effects]
        dominant_base = base_effects[np.argmax(base_costs)]

        # Apply Purity perk filtering if player has it
        if player.has_purity:
            if dominant_base.is_poison:
                # Remove beneficial effects (keep only poisons)
                base_effects = [e for e in base_effects if e.is_poison]
            else:
                # Remove harmful effects (keep only beneficial)
                base_effects = [e for e in base_effects if not e.is_poison]


        # Benefactor/poisoner perks only apply to effects in potions/poisons respectively
        # Check if we need to create a modified player (only if there's a perk mismatch)
        # TODO: find a better way to manage this (in RealizedEffect?)
        needs_modified_player = False
        if dominant_base.is_poison and player.benefactor_perk > 0:
            # Check if any non-poison effects exist
            needs_modified_player = any(not e.is_poison for e in base_effects if e != dominant_base)
        elif not dominant_base.is_poison and player.poisoner_perk > 0:
            # Check if any poison effects exist
            needs_modified_player = any(e.is_poison for e in base_effects if e != dominant_base)

        if needs_modified_player:
            calc_player = Player(
                skill=player.alchemy_skill,
                fortify=player.fortify_alchemy,
                alchemist_perk_level=player.alchemist_perk // 20,
                is_physician=player.physician_perk > 0,
                is_benefactor=(player.benefactor_perk > 0) and not dominant_base.is_poison,
                is_poisoner=(player.poisoner_perk > 0) and dominant_base.is_poison,
                is_seeker=player.seeker_of_shadows > 0,
                has_purity=player.has_purity
            )
        else:
            calc_player = player

        # Realize all effects with player stats (compute once)
        self.realized_effects = [effect.realize(calc_player) for effect in base_effects]
        self.total_value = sum(e.value for e in self.realized_effects)

        self.ingredients = ingredients
        self.ingredient_names = [ing.name for ing in ingredients]

        # Store dominant effect as realized
        self.dominant_effect = next(e for e in self.realized_effects if e.base.name == dominant_base.name)

        # Set potion/poison name based on dominant effect
        prefix = "Poison" if self.dominant_effect.is_poison else "Potion"
        self.name = f"{prefix} of {self.dominant_effect.name}"

    @property
    def value(self) -> int:
        return self.total_value

    @property
    def num_ingredients(self) -> int:
        return len(self.ingredients)

    @property
    def num_effects(self) -> int:
        return len(self.realized_effects)

    @property
    def is_poison(self) -> bool:
        return self.dominant_effect.is_poison

    @property
    def is_beneficial(self) -> bool:
        return not self.dominant_effect.is_poison

    @property
    def effect_names(self) -> list[str]:
        return [e.name for e in self.realized_effects]

    @property 
    def effects(self) -> list[Effect]:
        return self.realized_effects

    @property 
    def recipie(self) -> Set[Ingredient]:
        return self.ingredients

    def __repr__(self):
        return f"{self.name}\nIngredients: {', '.join(self.ingredient_names)}\nValue: {self.total_value}"

    def to_dict(self):
        return {
            "name": self.name,
            "ingredients": self.ingredient_names,
            "total_value": self.total_value,
            "effects": [
                {
                    "name": e.name,
                    "description": e.get_description(),
                    "magnitude": e.magnitude,
                    "duration": e.duration,
                    "value": e.value,
                    "is_poison": e.is_poison
                }
                for e in self.realized_effects
            ]
        }



if __name__ == "__main__":
    ing_db = IngredientsDatabase()

    player = Player(skill=40, alchemist_perk_level=1)

    # Get ingredient objects
    ings_1 = [
        ing_db.get_ingredient("Emperor Parasol Moss"),
        ing_db.get_ingredient("River Betty")
    ]
    potion_1 = Potion(ings_1, player, ing_db)
    print(potion_1)

    print("\n" + "="*50 + "\n")

    ings_2 = [
        ing_db.get_ingredient("Blue Mountain Flower"),
        ing_db.get_ingredient("Hanging Moss")
    ]
    potion_2 = Potion(ings_2, player, ing_db)
    print(potion_2)
