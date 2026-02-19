from itertools import combinations
from typing import Set
from .potion import Potion
from .player import Player
from .inventory import Inventory
from .ingredient import Ingredient
from .database import IngredientsDatabase

class Alembic:

    def __init__(self, db=IngredientsDatabase(), player=Player(), inventory=None): 
            # potion making state
        self.ing_db = db 
        self.player = player 
        self.inventory = inventory  
        self.valid_potions = []
        self.realized_potions = []

            # data collection state
        self.ingredients_map: Dict[Ingredient, filter[Potion]] = {}

        if inventory: 
            self._set_valid_potions()


    # this reconstructs the whole thing from the inventory state, 
    # really should only be used in the constructor or 
    # after manipulating the inventory manually which probably is a 
    # bad idea anyways. 
    # unless inventory needs to be updated in a way 
    # that cant be accounted for by using _update_valid_potions()
    def _set_valid_potions(self):

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
        # Filter ingredients to only those no longer available in inventory
        exhausted_ings = {ing for ing in ingredients 
                                if not self.inventory.get_ingredient_availability(ing)}
        
        # Remove potions containing any of the available ingredients
        self.valid_potions = [pot for pot in self.valid_potions 
                             if not any(ing in pot.recipie for ing in exhausted_ings)]


            

    

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

        if self.realized_potions: 
            self._set_ingredients_map()
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
            self._update_valid_potions(best.recipie)
            if self.inventory.consume_recipe(best.recipie):
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

    def _filter_realized_by_ingredient(self, ingredient=None):
        return filter(lambda p: any([i is ingredient for i in p.recipie]), self.realized_potions)

    # maps each ingredient to a list of potions participated in.
    def _set_ingredients_map(self):
        for ing in self.ing_db:
            self.ingredients_map[ing] = list(self._filter_realized_by_ingredient(ing))

    def fancy_print(self):
        # should print realized_potions and ingredients_map
        # but formatted well and concise
        sorted_potions = sorted(self.realized_potions, key=lambda p: p.total_value, reverse=True)
        total_gold = sum(p.total_value for p in sorted_potions)

        print("=== Crafting Session Results ===\n")

        print(f"Potions Crafted ({len(sorted_potions)} total | {total_gold} gold):")
        for i, potion in enumerate(sorted_potions, 1):
            print(f"  {i}. {potion.name:<40} {potion.total_value} gold")

        print("\nIngredient Usage:")
        usage = {ing: len(list(potions)) for ing, potions in self.ingredients_map.items()}
        for ing, count in sorted(usage.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"  {ing.name:<30} used in {count} potion{'s' if count != 1 else ''}")



# Practical Test
def main():

    print("generating state stuff...")

    db = IngredientsDatabase()
    inv = Inventory.generate_normal(db, 7)
    player = Player()

    print("building alembic...")
    alembic = Alembic(db, player, inv)

    print("creating potions...")
    potions = alembic.exhaust_inventory("lazy")

#    print("printing potions\n================\n")
#    for potion in potions:
    #    print(potion)

    print("Printing the entire alembic\n================\n")
    alembic.fancy_print()




if __name__ == "__main__":
    main()
