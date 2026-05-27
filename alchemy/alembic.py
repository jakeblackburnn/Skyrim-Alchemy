from itertools import combinations
from typing import Set, Dict, List
from .potion import Potion
from .player import Player
from .inventory import Inventory
from .ingredient import Ingredient
from .database import IngredientsDatabase

class Alembic:

    def __init__(self, db=IngredientsDatabase(), player=Player(), inventory=None):
        """Create Alembic (alchemy table) from player, inventory, and ingredients database. 

        Note: If inventory is provided, valid_potions is populated immediately,
        otherwise it will remain empty until a inventory is added"""
        self.ing_db = db
        self.player = player 
        self.inventory = inventory  
        self.valid_potions = []
        self.realized_potions = []

        self.ingredients_map: Dict[Ingredient, List[Potion]] = {}

        if inventory: 
            self._set_valid_potions()



    def _set_valid_potions(self):
        """populates valid potions based on ingredients in inventory"""
        ingredients_list = self.inventory.get_available_ingredients()
        valid_combos = []
        for combo in combinations(ingredients_list, 2):
            if self._shared_effects(combo):
                valid_combos.append(list(combo))
        for combo in combinations(ingredients_list, 3):
            if self._shared_effects(combo):
                valid_combos.append(list(combo))
        self.valid_potions = [Potion(combo, self.player, self.ing_db) for combo in valid_combos]

    def _shared_effects(self, ingredients):
        """Returns True only if every ingredient shares at least one effect with at least one other ingredient"""
        ingredient_effects_sets = [set(ing.get_effect_names()) for ing in ingredients]
        for i, effects_i in enumerate(ingredient_effects_sets):
            has_shared = False
            for j, effects_j in enumerate(ingredient_effects_sets):
                if i != j and len(effects_i & effects_j) > 0:
                    has_shared = True
                    break
            if not has_shared:
                return False
        return True

    def _update_valid_potions(self, ingredients: Set[Ingredient]):
        # Filter ingredients for only those no longer available in inventory
        exhausted_ings = {ing for ing in ingredients 
                                if not self.inventory.has_ingredient(ing)}
        
        # Remove potions containing any of the exhausted ingredients
        self.valid_potions = [pot for pot in self.valid_potions 
                             if not any(ing in pot.recipe for ing in exhausted_ings)]
    

    def exhaust_inventory(self, strategy: str):
        """Consume the entire inventory using the given strategy, returning all realized potions.
        Mutates inventory and valid_potions in place. Currently 'lazy' is the only supported strategy 
        (lazy is greedy: always brews the highest-value available potion)."""
        if strategy == "lazy":
            self._lazy_strategy()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        if self.realized_potions: 
            self._set_ingredients_map()
        return self.realized_potions

    def create_potion(self, potion):
        if self.valid_potions:
            self.inventory.consume_recipe(potion.recipe)
            self._update_valid_potions(potion.recipe)
            self.realized_potions.append(potion)
            
    def _lazy_potionmaking(self):
        best = self._get_best_potion()
        if best:
            self.create_potion(best)

    def _lazy_strategy(self):
        while self.valid_potions:
            self._lazy_potionmaking()


    def _get_best_potion(self):
        if not self.valid_potions:
            return None
        return max(self.valid_potions, key=lambda p: p.total_value)

    def _filter_realized_by_ingredient(self, ingredient=None):
        return filter(lambda p: any([i is ingredient for i in p.recipe]), self.realized_potions)

    def _set_ingredients_map(self):
        for ing in self.ing_db:
            self.ingredients_map[ing] = list(self._filter_realized_by_ingredient(ing))
