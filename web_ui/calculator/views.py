"""
views.py — HTTP layer for the calculator app.

Page views render the React SPA shell; the API endpoints wrap the alchemy engine
(/api/calculate) and serve precomputed experiment results (/api/insights,
/api/results/<experiment>). Domain concerns live in sibling modules: db (engine
singleton), serializers (JSON shapes), results (results-file loader).
"""
import json

from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from alchemy.alembic import Alembic
from alchemy.player import Player
from alchemy.inventory import Inventory

from .db import get_db
from .serializers import base_context
from . import results


# ── Page views ─────────────────────────────────────────────────────────────────
def calculator_view(request):
    return render(request, "calculator/calculator.html", base_context(get_db()))


def datasets_view(request):
    return render(request, "calculator/datasets.html", base_context(get_db()))


def insights_view(request):
    return render(request, "calculator/insights.html", base_context(get_db()))


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

        db = get_db()
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


# ── Insights / results API ──────────────────────────────────────────────────────
@require_http_methods(["GET"])
def insights_api(request):
    """
    GET /api/insights
    Serves the most recent base ingredient performance analysis JSON. The
    payload carries run-level stats plus `average_performance` (per-ingredient
    appearance rate, avg potion value, and avg session contribution).
    Run experiments/base_perf.py to refresh results.
    """
    base_perf = results.load_experiment("base_perf")

    if not base_perf:
        return JsonResponse(
            {"error": "No analysis results found. Run experiments/base_perf.py first."},
            status=404
        )

    return JsonResponse(base_perf)


@require_http_methods(["GET"])
def results_api(request, experiment):
    """
    GET /api/results/<experiment>
    Serves the most recent results JSON for a named experiment (see
    results.EXPERIMENT_PATTERNS). 404 if the experiment is unknown or has no
    results on disk yet.
    """
    data = results.load_experiment(experiment)
    if data is None:
        return JsonResponse(
            {"error": f"No results found for experiment '{experiment}'.",
             "available": results.available_experiments()},
            status=404,
        )
    return JsonResponse(data)


# ── CSV downloads ──────────────────────────────────────────────────────────────
def download_ingredients_csv(request):
    path = settings.DATA_DIR / "master_ingredients.csv"
    return FileResponse(open(path, "rb"), as_attachment=True, filename="skyrim_ingredients.csv")


def download_effects_csv(request):
    path = settings.DATA_DIR / "effects.csv"
    return FileResponse(open(path, "rb"), as_attachment=True, filename="skyrim_effects.csv")
