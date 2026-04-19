from typing import Set, Dict, List, Optional
import random
import numpy as np

from .database import IngredientsDatabase
from .ingredient import Ingredient

class Inventory:

    # Inventory class wraps a dict of ingredients to quantities
    # and provides basic access and update methods.
    def __init__(self, items: Optional[Dict[Ingredient, int]] = None):
        self._items = items.copy() if items is not None else {}

    # Defaults for ingredient sampling 

    # rarity weighted sampling probabilities
    BASIC_RARITY_DIST = { 
        "common": 0.50,
        "uncommon": 0.30,
        "rare": 0.15,
        "very_rare": 0.04,
        "unique": 0.01,
    }

    # chi-squared parameters for normal sampling
    QUANTITY_PARAMS_NORMAL = {
        'df': 5,
        'scale': 1.5,
        'min_qty': 1,
        'max_qty': 50
    }




    # Access methods

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


    # Update methods

    def add(self, ing: Ingredient, qty: int = 1):
        if qty <= 0:
            raise ValueError(f"Quantity must be positive, got {qty}")
        self._items[ing] = self._items.get(ing, 0) + qty

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



    # sampling methods
    # Each accepts an optional `exclude` set to filter the ingredient pool before sampling.


    # chi-squared distribution for sampling quantities of ingredients for nomal sampling strategy.
    @staticmethod
    def _sample_chi2_quantity(df, scale, min_qty, max_qty):
        raw_value = np.random.chisquare(df) * scale
        return max(min_qty, min(max_qty, int(raw_value)))

    # normal sampling - creates inventory with a certain number of distinct ingredients, 
    # but does not specify total quantity. quantity is randomized via chi-squared dist
    # specified in qty_params which default to QUANTITY_PARAMS_NORMAL.
    @staticmethod
    def _build_normal_sample(
        db,
        size: int = 0,
        qty_params: Optional[dict] = None,
        exclude: Optional[Set[Ingredient]] = None,
    ) -> Dict[Ingredient, int]:
        pool = db.get_all_ingredients()
        if exclude is not None:
            pool = [i for i in pool if i not in exclude]

        size = min(size, len(pool))
        sampled = random.sample(pool, size)

        params = qty_params if qty_params is not None else Inventory.QUANTITY_PARAMS_NORMAL

        items = {}
        for ing in sampled:
            qty = Inventory._sample_chi2_quantity(
                params['df'],
                params['scale'],
                params['min_qty'],
                params['max_qty']
            )
            items[ing] = qty

        return items


    # stable sampling - creates an inventory with exact total and distinct ingredients rather 
    # than the randomized total size in 'normal' sampling using stick-breaking algorithm
    @staticmethod
    def _build_stable_sample(
        db,
        total: int,
        distinct: int,
        exclude: Optional[Set[Ingredient]] = None,
    ) -> Dict[Ingredient, int]:
        pool = db.get_all_ingredients()
        if exclude is not None:
            pool = [i for i in pool if i not in exclude]

        if total < distinct:
            raise ValueError("stable gen: more distinct than total ingredients is impossible!")
        if distinct > len(pool):
            raise ValueError(f"stable gen: too many distinct ingredients! (max: {len(pool)})")

        sampled = random.sample(pool, distinct)

        quantities = [1] * distinct
        remaining = total - distinct
        if remaining > 0:
            cuts = sorted([random.randint(0, remaining) for _ in range(distinct - 1)])
            cuts = [0] + cuts + [remaining]
            partition = [cuts[i+1] - cuts[i] for i in range(distinct)]
            quantities = [q + p for q, p in zip(quantities, partition)]

        return {ing: qty for ing, qty in zip(sampled, quantities)}


    # weighted sampling - similar to stable sampling but using np random choice 
    # weight ingredient probabilities by rarity according to a supplied rarity prob dist 
    # defaults to BASIC_RARITY_DIST
    @staticmethod
    def _build_weighted_sample(
        db,
        total: int,
        distinct: int,
        rarity_dist: Optional[Dict[str, float]] = None,
        exclude: Optional[Set[Ingredient]] = None,
    ) -> Dict[Ingredient, int]:
        if rarity_dist is None:
            rarity_dist = Inventory.BASIC_RARITY_DIST

        pool = db.get_all_ingredients()
        if exclude is not None:
            pool = [i for i in pool if i not in exclude]

        if total < distinct:
            raise ValueError("weighted gen: more distinct than total ingredients is impossible!")
        if distinct > len(pool):
            raise ValueError(f"weighted gen: too many distinct ingredients! (max: {len(pool)})")

        weights = []
        for ing in pool:
            if ing.rarity not in rarity_dist:
                raise ValueError(
                    f"weighted gen: ingredient '{ing.name}' has rarity '{ing.rarity}' "
                    f"not found in rarity_dist. Available rarities: {list(rarity_dist.keys())}"
                )
            weights.append(rarity_dist[ing.rarity])

        weights_array = np.array(weights)
        probabilities = weights_array / weights_array.sum()

        indices = np.random.choice(len(pool), size=distinct, replace=False, p=probabilities)
        sampled = [pool[i] for i in indices]

        quantities = [1] * distinct
        remaining = total - distinct
        if remaining > 0:
            cuts = sorted([random.randint(0, remaining) for _ in range(distinct - 1)])
            cuts = [0] + cuts + [remaining]
            partition = [cuts[i+1] - cuts[i] for i in range(distinct)]
            quantities = [q + p for q, p in zip(quantities, partition)]

        return {ing: qty for ing, qty in zip(sampled, quantities)}



    # Generation classmethods — delegate to builders, construct and return new Inventory.

    @classmethod
    def generate_weighted(cls, db, total: int, distinct: int, rarity_dist: Optional[Dict[str, float]] = None):
        return cls(cls._build_weighted_sample(db, total, distinct, rarity_dist=rarity_dist))

    @classmethod
    def generate_stable(cls, db, total: int, distinct: int):
        return cls(cls._build_stable_sample(db, total, distinct))

    @classmethod
    def generate_normal(cls, db, size: int = 0, qty_params: Optional[dict] = None):
        return cls(cls._build_normal_sample(db, size, qty_params))



    # Resample instance methods — delegate to builders, merge into existing inventory.
    # exclude_existing=True: only samples ingredients not currently in inventory.

    def resample_weighted(self, db, total: int, distinct: int,
                          rarity_dist: Optional[Dict[str, float]] = None,
                          exclude_existing: bool = False):
        exclude = set(self._items.keys()) if exclude_existing else None
        for ing, qty in self._build_weighted_sample(db, total, distinct, rarity_dist=rarity_dist, exclude=exclude).items():
            self.add(ing, qty)

    def resample_stable(self, db, total: int, distinct: int, exclude_existing: bool = False):
        exclude = set(self._items.keys()) if exclude_existing else None
        for ing, qty in self._build_stable_sample(db, total, distinct, exclude=exclude).items():
            self.add(ing, qty)

    def resample_normal(self, db, size: int = 0, qty_params: Optional[dict] = None,
                        exclude_existing: bool = False):
        exclude = set(self._items.keys()) if exclude_existing else None
        for ing, qty in self._build_normal_sample(db, size, qty_params, exclude=exclude).items():
            self.add(ing, qty)


    # utilities and dunder methods

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

    print("Generating random inventory\n")

    ing_db = IngredientsDatabase()
    inv = Inventory.generate_normal(ing_db, 7)
    print(inv)

    print("\nResampling inventory\n")
    inv.resample_normal(ing_db, 7)
    print(inv)



if __name__ == "__main__":
    main()
