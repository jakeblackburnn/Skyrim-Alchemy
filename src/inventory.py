from typing import Set, Dict, List, Optional
import random
import numpy as np

from .database import IngredientsDatabase
from .ingredient import Ingredient

class Inventory:

    # Inventory class wraps a dict of ingredients to quantities
    # and provides basic access and update methods
    # but no adding ingredients once created. 
    # 
    # implement a class method for individual inventory generation 
    # strategies 
    # ... would inheritence be easier than adding classmethods to this file?
    def __init__(self, items: Optional[Dict[Ingredient, int]] = None):
        self._items = items.copy() if items is not None else {}



    # Access methods

    def get_ingredient_availability(self, ingredient) -> bool:
        if ingredient in self._items.keys():
            return True
        return False

    def get_available_ingredients(self) -> List[Ingredient]:
        return list(self._items.keys())

    def get_quantity(self, ing: Ingredient) -> int:
        return self._items.get(ing, 0)

    def has_ingredient(self, ing: Ingredient, qty: int = 1) -> bool:
        return self.get_quantity(ing) >= qty

    def total_items(self) -> int:
        return sum(self._items.values())

    def unique_items(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0
    
    ###



    # update methods

    def consume(self, ing: Ingredient) -> bool:
        if not self.has_ingredient(ing):
            return False

        self._items[ing] -= 1
        if self._items[ing] == 0:
            del self._items[ing]

        return True

    def consume_recipe(self, ings: Set[Ingredient]) -> bool:
        for ing in ings:
            if not self.has_ingredient(ing):
                return False
        for ing in ings:
            self.consume(ing)

        return True

    ####


    # stable inventory generation

    @classmethod
    def generate_stable(cls, db, total: int, distinct: int):
        if total < distinct:
            raise ValueError(f"stable gen: more distinct than total ingredients is impossible!")
        if distinct > len(db):
            raise ValueError(f"stable gen: too many distinct ingredients! (max: 111)")


        # random selection of Ingredients (without replacement)
        ingredients = db.get_all_ingredients()
        sampled = random.sample(ingredients, distinct)

        # random partitions of total across distinct ingredients
        # start with base allocation of 1 per ingredient
        quantities = [1] * distinct
        remaining = total - distinct
        
        if remaining > 0:
            # use stick-breaking to create random uniform partition
            # generate distinct-1 random cut points in [0, remaining]
            cuts = sorted([random.randint(0, remaining) for _ in range(distinct - 1)])
            
            # add boundaries
            cuts = [0] + cuts + [remaining]
            
            # partition sizes are differences between consecutive cuts
            partition = [cuts[i+1] - cuts[i] for i in range(distinct)]
            
            # add partition to base quantities
            quantities = [q + p for q, p in zip(quantities, partition)]
        
        # build ingredient -> quantity mapping
        partitions = {ing: qty for ing, qty in zip(sampled, quantities)}
        
        return cls(partitions)

    ### 



    # Chi Squared sampling methods & defaults:

    @staticmethod
    def _sample_chi2_quantity(df, scale, min_qty, max_qty):
        raw_value = np.random.chisquare(df) * scale
        return max(min_qty, min(max_qty, int(raw_value)))

    # Default chi-squared parameters for normal strategy
    QUANTITY_PARAMS_NORMAL = {
        'df': 5,
        'scale': 1.5,
        'min_qty': 1,
        'max_qty': 50
    }

    @classmethod
    def generate_normal(cls, db, size=0, qty_params: Optional[dict] = None):

        size = min(size, len(db)) # ensure size isnt greater than max ingredients

        ingredients = db.get_all_ingredients()

        # Uniform random sampling without replacement
        sampled = random.sample(ingredients, size)

        # Use provided params or default
        params = qty_params if qty_params is not None else cls.QUANTITY_PARAMS_NORMAL

        items = {}
        for ing in sampled:
            qty = cls._sample_chi2_quantity(
                params['df'],
                params['scale'],
                params['min_qty'],
                params['max_qty']
            )
            items[ing] = qty

        return cls(items)

    def add(self, ing: Ingredient, qty: int = 1):
        if qty <= 0:
            raise ValueError(f"Quantity must be positive, got {qty}")
        self._items[ing] = self._items.get(ing, 0) + qty

    def to_ingredient_list(self) -> List[Ingredient]:
        return self.get_available_ingredients()

    def copy(self):
        return Inventory(self._items.copy())

    def __repr__(self):
        if self.is_empty():
            return "Inventory(empty)"
        lines = [f"Inventory({self.unique_items()} types, {self.total_items()} total)"]
        for ing, qty in self._items.items():
            lines.append(f"  {ing.name}: {qty}")
        return "\n".join(lines)

    def __len__(self):
        return self.unique_items()

    def __contains__(self, ing: Ingredient) -> bool:
        return self.has_ingredient(ing, qty=1)

    def __getitem__(self, ing: Ingredient) -> int:
        qty = self.get_quantity(ing)
        if qty == 0:
            raise KeyError(f"Ingredient '{ing.name}' not in inventory")
        return qty

    def __iter__(self):
        return iter(self._items.keys())

    def __bool__(self):
        return not self.is_empty()


def main():

    ing_db = IngredientsDatabase()
    inv = Inventory.generate_normal(ing_db, 7)

    print(inv)



if __name__ == "__main__":
    main()
