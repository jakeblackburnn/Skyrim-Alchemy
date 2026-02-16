from itertools import combinations
from .potion import Potion
from .player import Player
from .inventory import Inventory
from .ingredient import Ingredient
from .database import IngredientsDatabase

class Alembic:

    def __init__(self, db=IngredientsDatabase(), player=Player(), inventory=None): 
        self.ing_db = db 
        self.player = player 
        self.inventory = inventory  
        self.realized_potions = []

        if inventory is not None:
            self._set_valid_potions()
        else:
            self.valid_potions = []  # Initialize empty list

    def _set_valid_potions(self):
        # this reconstructs the whole thing from the inventory state, 
        # really should only be used in the constructor or 
        # after manipulating the inventory manually which probably is a 
        # bad idea anyways. 
        ingredients_list = self.inventory.get_available_ingredients()
        valid_combos = []
        for combo in combinations(ingredients_list, 2):
            if self._shared_effects(combo):
                valid_combos.append(list(combo))
        for combo in combinations(ingredients_list, 3):
            if self._shared_effects(combo):
                valid_combos.append(list(combo))
        self.valid_potions = [Potion(combo, self.player, self.ing_db) for combo in valid_combos]

    def _update_valid_potions(self, ingredients: Set):
        # check if ingredients *werent* used up
        for ing in ingredients:
            if not self.inventory.get_ingredient_availability(ing):
                ingredients.remove(ing)

        for ing in ingredients:
            for pot in self.valid_potions:
                if ing in pot.ingredients:
                    self.valid_potions.remove(pot)

    def _shared_effects(self, ingredients):
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
    

    def exhaust_inventory(self, strategy=None):

        # should the strategies really be strings?
        if strategy == "lazy":
            self._lazy_strategy()
        elif strategy == None:
            pass
        elif strategy == "greedy":
            pass
        elif strategy == "random":
            pass
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        return self.realized_potions

    # fundamental potionmaking method - realizing a potion
    def create_potion(self, potion):
        if self.valid_potions:
            self.inventory.consume_recipe(potion.recipie)
            self._update_valid_potions(potion.recipie)
            self.realized_potions.append(potion)
            
    ### Lazy Potionmaking Algorithms

    def _lazy_potionmaking(self):
        best = self._get_best_potion()
        if best:
            self.create_potion(best)

    def _lazy_strategy(self):
        while self.valid_potions:
            self._lazy_potionmaking()

    ### Random algorithm
    def _random_strategy(self):
        pass

    ### Greedy Algorithm
    def _greedy_strategy(self):
        while not self.inventory.is_empty():
            if not self.valid_potions:
                break
            best = self._get_best_potion()
            self._update_valid_potions(best.ingredients)
            if self.inventory.consume_recipe(best.ingredients):
                self.realized_potions.append(best)
            else:
                break  
    
    ### Smart algorithm
    def _smart_potionmaking(self):
        pass

    def _lookahead(self):
        pass
    def _get_best_potion(self):
        if not self.valid_potions:
            return None
        return max(self.valid_potions, key=lambda p: p.total_value)

    def _get_value_sorted_potions(self):
        return sorted(self.potions, key=lambda p: p.total_value, reverse=True)

    def _filter_by_ingredient(self, ingredient=None):
        return filter(lambda p: any([i is ingredient for i in p.ingredients()]), self.potions)



def main():

    print("generating state stuff...")

    db = IngredientsDatabase()
    inv = Inventory.generate_normal(db, 7)
    player = Player()

    print("building alembic...")
    alembic = Alembic(db, player, inv)

    print("creating potions...")
    potions = alembic.exhaust_inventory("greedy-basic")

    print("printing potions\n================\n")
    for potion in potions:
        print(potion)

if __name__ == "__main__":
    main()
