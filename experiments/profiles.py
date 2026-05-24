import os
import re
import sys
import json
from itertools import combinations
from datetime import datetime

import networkx as nx

os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from alchemy.database import IngredientsDatabase
from alchemy.player import Player
from alchemy.potion import Potion



class _Tee:
    def __init__(self, *files): self.files = files
    def write(self, data):
        for f in self.files: f.write(data)
    def flush(self):
        for f in self.files: f.flush()


def _shared_effects(ingredients):
    sets = [set(ing.get_effect_names()) for ing in ingredients]
    for i, s in enumerate(sets):
        if not any(s & sets[j] for j in range(len(sets)) if j != i):
            return False
    return True


def _enumerate_valid_potions(ingredients, player, db):
    potions: list[Potion] = []
    for size in (2, 3):
        for combo in combinations(ingredients, size):
            if _shared_effects(combo):
                try:
                    potions.append(Potion(list(combo), player, db))
                except ValueError:
                    pass
    return potions


def _index_potions_by_ingredient(potions, ingredients):
    index: dict[str, list[Potion]] = {ing.name: [] for ing in ingredients}
    for potion in potions:
        for name in potion.ingredient_names:
            index[name].append(potion)
    return index


def _synergizing_by_order(G, name):
    buckets: dict[str, list[str]] = {"1": [], "2": [], "3": [], "4": []}
    for neighbor in G.neighbors(name):
        order = G[name][neighbor]['weight']
        buckets[str(order)].append(neighbor)
    for k in buckets:
        buckets[k].sort()
    return buckets


def _best_potion(potions, size):
    candidates = [p for p in potions if len(p.ingredient_names) == size]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.total_value)


def _slugify(name):
    s = re.sub(r'[^a-z0-9]+', '_', name.lower())
    return s.strip('_')


def _save_per_ingredient_files(profiles, results_dir, timestamp):
    ingredients_dir = os.path.join(results_dir, 'ingredients')
    os.makedirs(ingredients_dir, exist_ok=True)
    for fname in os.listdir(ingredients_dir):
        if fname.endswith('.json'):
            os.remove(os.path.join(ingredients_dir, fname))

    for name, profile in profiles.items():
        payload = {
            "metadata": {
                "name": name,
                "timestamp": timestamp,
            },
            "profile": profile,
        }
        path = os.path.join(ingredients_dir, f'{_slugify(name)}.json')
        with open(path, 'w') as f:
            json.dump(payload, f, indent=2)

    print(f"Wrote {len(profiles)} per-ingredient files to {ingredients_dir}")


def _build_synergy_graph(ingredients):
    G = nx.Graph()
    G.add_nodes_from(ing.name for ing in ingredients)
    for a, b in combinations(ingredients, 2):
        shared = len(set(a.get_effect_names()) & set(b.get_effect_names()))
        if shared:
            G.add_edge(a.name, b.name, weight=shared)
    return G


def _effect_type_balance(ingredient, effects_db):
    counts = {"beneficial": 0, "poison": 0}
    for effect_name in ingredient.get_effect_names():
        effect = effects_db.get(effect_name)
        if effect is None:
            continue
        if effect.is_poison:
            counts["poison"] += 1
        else:
            counts["beneficial"] += 1
    return counts


def _perk_alignment(ingredient, effects_db):
    perks = set()
    for effect_name in ingredient.get_effect_names():
        effect = effects_db.get(effect_name)
        if effect is None:
            continue
        if effect.is_poison:
            perks.add("poisoner")
        elif effect.is_restore:
            perks.add("physician")
        elif effect.is_fortify:
            perks.add("benefactor")
    return sorted(perks)



def _print_profiles_table(profiles, sort_key, title):
    sorted_items = sorted(profiles.items(), key=lambda x: x[1][sort_key], reverse=True)
    header = (f"{'#':>3}  {'Name':<32} "
              f"{'Compat':>6}  {'S-Wt':>5}  {'S1':>3}  {'S2':>3}  {'S3':>3}  {'S4':>3}  "
              f"{'Subst.':>6}  {'Unique':>6}  {'Potions':>7}  {'DLC':<5}  {'Rarity':<12}  Perks")
    print(f"\n{title}")
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    for i, (name, p) in enumerate(sorted_items, 1):
        dlc = "Yes" if p['dlc'] else "No"
        perks = ", ".join(p['perk_alignment']) if p['perk_alignment'] else "—"
        unique = len(p['unique_effects'])
        sbo = p['synergy_by_order']
        print(f"{i:>3}  {name:<32} "
              f"{p['compatible_count']:>6}  {p['total_synergy_weight']:>5}  "
              f"{sbo['1']:>3}  {sbo['2']:>3}  {sbo['3']:>3}  {sbo['4']:>3}  "
              f"{p['substitutability']:>6.2f}  {unique:>6}  {p['valid_potion_count']:>7}  {dlc:<5}  {p['rarity']:<12}  {perks}")


def run_profiles():
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    txt_path = os.path.join(results_dir, 'profiles.txt')

    with open(txt_path, 'w') as txt_file:
        original_stdout = sys.stdout
        sys.stdout = _Tee(original_stdout, txt_file)
        try:
            _run_profiles_inner(results_dir)
        finally:
            sys.stdout = original_stdout


def _run_profiles_inner(results_dir):
    db = IngredientsDatabase()
    ingredients = db.get_all_ingredients()
    effects_db = db._effects

    print(f"Loaded {len(ingredients)} ingredients, {len(effects_db)} effects")

    # --- Per-effect sharing counts ---
    effect_sharing: dict[str, list[str]] = {}
    for ing in ingredients:
        for name in ing.get_effect_names():
            effect_sharing.setdefault(name, []).append(ing.name)

    # --- Synergy graph ---
    print("Building synergy graph...")
    G = _build_synergy_graph(ingredients)

    # --- All valid potions (base player) for ideal-potion lookups ---
    print("Computing valid potions for ideal recipes (base player)...")
    base_player = Player()
    base_potions = _enumerate_valid_potions(ingredients, base_player, db)
    base_potions_by_ingredient = _index_potions_by_ingredient(base_potions, ingredients)

    # --- Build profiles ---
    print("Building profiles...")
    profiles = {}

    for ing in ingredients:
        effect_names = ing.get_effect_names()

        compatible_count = G.degree(ing.name)
        synergy_by_order = {"1": 0, "2": 0, "3": 0, "4": 0}
        total_synergy_weight = 0
        for neighbor in G.neighbors(ing.name):
            order = G[ing.name][neighbor]['weight']
            synergy_by_order[str(order)] = synergy_by_order.get(str(order), 0) + 1
            total_synergy_weight += order

        unique_effects = [
            name for name in effect_names
            if len(effect_sharing.get(name, [])) == 1
        ]

        sharing_counts = [
            len(effect_sharing.get(name, [])) - 1
            for name in effect_names
        ]
        substitutability = round(sum(sharing_counts) / len(sharing_counts), 2) if sharing_counts else 0

        balance = _effect_type_balance(ing, effects_db)
        perk_align = _perk_alignment(ing, effects_db)

        my_base_potions = base_potions_by_ingredient[ing.name]
        ideal_2 = _best_potion(my_base_potions, 2)
        ideal_3 = _best_potion(my_base_potions, 3)
        valid_potion_count = len(my_base_potions)

        profiles[ing.name] = {
            "compatible_count": compatible_count,
            "synergy_by_order": synergy_by_order,
            "synergizing_by_order": _synergizing_by_order(G, ing.name),
            "total_synergy_weight": total_synergy_weight,
            "unique_effects": unique_effects,
            "substitutability": substitutability,
            "effect_type_balance": balance,
            "perk_alignment": perk_align,
            "valid_potion_count": valid_potion_count,
            "ideal_2_ingredient_potion": ideal_2.to_dict() if ideal_2 else None,
            "ideal_3_ingredient_potion": ideal_3.to_dict() if ideal_3 else None,
            "rarity": ing.rarity,
            "dlc": ing.dlc != "base",
        }

    # --- Save JSON ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "metadata": {
            "timestamp": timestamp,
            "num_ingredients": len(ingredients),
            "num_valid_potions": len(base_potions),
        },
        "profiles": profiles,
    }

    json_path = os.path.join(results_dir, f'profiles_{timestamp}.json')
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {json_path}")

    # --- Per-ingredient JSON files ---
    _save_per_ingredient_files(profiles, results_dir, timestamp)

    # --- Print full tables ---
    print(f"\n{'='*80}")
    print(f"INGREDIENT PROFILES  ({len(profiles)} total)")
    print(f"{'='*80}")

    _print_profiles_table(profiles, 'total_synergy_weight', "Sorted by total_synergy_weight")



if __name__ == "__main__":
    run_profiles()
