from typing import Set, Dict, List, Optional
import random
import numpy as np

from .database import IngredientsDatabase
from .ingredient import Ingredient


class Inventory:

    # Inventory size distribution parameters
    INVENTORY_SIZE_PARAMS = {
        'normal': {
            'mean': 35,
            'std': 10,
            'min': 10,
            'max': 70
        },
    }

    # Default chi-squared parameters for normal strategy
    QUANTITY_PARAMS_NORMAL = {
        'df': 5,
        'scale': 1.5,
        'min_qty': 1,
        'max_qty': 50
    }

    def __init__(self, items: Optional[Dict[Ingredient, int]] = None):
        self._items = items.copy() if items is not None else {}

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

    @staticmethod
    def _sample_chi2_quantity(df, scale, min_qty, max_qty):
        raw_value = np.random.chisquare(df) * scale
        return max(min_qty, min(max_qty, int(raw_value)))

    @classmethod
    def generate_normal(cls, db, size=0, qty_params: Optional[dict] = None):

        all_ingredients = db.get_all_ingredients()

        # Ensure size doesn't exceed available ingredients
        size = min(size, len(all_ingredients))

        # Uniform random sampling without replacement
        sampled = random.sample(all_ingredients, size)

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
