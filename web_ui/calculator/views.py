"""
views.py — drop-in replacement for web_ui/calculator/views.py
Uses Alembic (main branch). No client-side alchemy logic required.
"""
import json
import glob
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from alchemy.alembic import Alembic
from alchemy.player import Player
from alchemy.inventory import Inventory
from alchemy.database import IngredientsDatabase


# ── Shared DB singleton (loaded once per process) ─────────────────────────────
_DB = None
def _get_db():
    global _DB
    if _DB is None:
        _DB = IngredientsDatabase()
    return _DB


# ── Data serialisation helpers ─────────────────────────────────────────────────
def _serialize_ingredients(db):
    return [
        {
            "name":   ing.name,
            "value":  ing.value,
            "weight": ing.weight,
            "rarity": ing.rarity,
            "dlc":    ing.dlc,
            "source": ing.source,
            "effects": [
                {"name": ing.effect1, "mag": ing.effect1_mag, "dur": ing.effect1_dur},
                {"name": ing.effect2, "mag": ing.effect2_mag, "dur": ing.effect2_dur},
                {"name": ing.effect3, "mag": ing.effect3_mag, "dur": ing.effect3_dur},
                {"name": ing.effect4, "mag": ing.effect4_mag, "dur": ing.effect4_dur},
            ],
        }
        for ing in db
    ]


def _serialize_effects(db):
    return [
        {
            "name":            eff.name,
            "base_cost":       eff.base_cost,
            "base_magnitude":  eff.base_mag,
            "base_duration":   eff.base_dur,
            "is_beneficial":   not eff.is_poison,
            "is_poison":       eff.is_poison,
            "varies_duration": eff.variable_duration,
        }
        for eff in db._effects.values()
    ]


def _base_context():
    """JSON-serialised ingredient + effect data injected into every page."""
    db = _get_db()
    return {
        "ingredients_json": json.dumps(_serialize_ingredients(db)),
        "effects_json":     json.dumps(_serialize_effects(db)),
    }


# ── Page views ─────────────────────────────────────────────────────────────────
def calculator_view(request):
    return render(request, "calculator/calculator.html", _base_context())


def datasets_view(request):
    return render(request, "calculator/datasets.html", _base_context())


def insights_view(request):
    return render(request, "calculator/insights.html", _base_context())


# ── Calculator API ─────────────────────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def calculate_potions(request):
    """
    POST /api/calculate
    Body: { skill, fortify, alchemist_rank, physician, benefactor,
            poisoner, purity, seeker, ingredients: [str, ...] }
    """
    try:
        data = json.loads(request.body)

        ingredient_names = data.get("ingredients", [])
        if len(ingredient_names) < 2:
            return JsonResponse({"error": "Please select at least 2 ingredients"}, status=400)

        player = Player(
            skill=int(data.get("skill", 15)),
            fortify=int(data.get("fortify", 0)),
            alchemist_perk_level=int(data.get("alchemist_rank", 0)),
            is_physician=bool(data.get("physician", False)),
            is_benefactor=bool(data.get("benefactor", False)),
            is_poisoner=bool(data.get("poisoner", False)),
            is_seeker=bool(data.get("seeker", False)),
            has_purity=bool(data.get("purity", False)),
        )

        db = _get_db()
        items, missing = {}, []
        for name in ingredient_names:
            ing = db.get_ingredient(name)
            if ing:
                items[ing] = 1
            else:
                missing.append(name)

        if missing:
            return JsonResponse({"error": f"Unknown ingredients: {missing}"}, status=400)

        alembic = Alembic(db=db, player=player, inventory=Inventory(items))
        potions = sorted(alembic.valid_potions, key=lambda p: p.total_value, reverse=True)

        return JsonResponse({"potions": [p.to_dict() for p in potions]})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ── Insights API ───────────────────────────────────────────────────────────────
@require_http_methods(["GET"])
def insights_api(request):
    """
    GET /api/insights
    Serves the most recent pre-computed analysis JSON files from results/.
    Returns: { perks: {...}, rarity: {...} }
    Run experiments/perks.py and experiments/rarity.py to refresh results.
    """
    results_dir = settings.PROJECT_ROOT / "results"

    def load_latest(pattern):
        files = sorted(glob.glob(str(results_dir / pattern)))
        if not files:
            return None
        with open(files[-1]) as f:
            return json.load(f)

    perks_data  = load_latest("perks_*.json")
    rarity_data = load_latest("rarity_*.json")

    if not perks_data and not rarity_data:
        return JsonResponse(
            {"error": "No analysis results found. Run experiments/perks.py and experiments/rarity.py first."},
            status=404
        )

    return JsonResponse({"perks": perks_data, "rarity": rarity_data})


# ── CSV downloads ──────────────────────────────────────────────────────────────
def download_ingredients_csv(request):
    from django.http import FileResponse
    path = settings.PROJECT_ROOT / "data" / "master_ingredients.csv"
    return FileResponse(open(path, "rb"), as_attachment=True, filename="skyrim_ingredients.csv")


def download_effects_csv(request):
    from django.http import FileResponse
    path = settings.PROJECT_ROOT / "data" / "effects.csv"
    return FileResponse(open(path, "rb"), as_attachment=True, filename="skyrim_effects.csv")
