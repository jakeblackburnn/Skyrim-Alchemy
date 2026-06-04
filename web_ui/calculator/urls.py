from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    path('',                              views.calculator_view,        name='calculator'),
    path('datasets/',                     views.datasets_view,          name='datasets'),
    path('insights/',                     views.insights_view,          name='insights'),
    path('api/calculate',                 views.calculate_potions,      name='calculate_api'),
    path('api/insights',                  views.insights_api,           name='insights_api'),
    path('datasets/download/ingredients', views.download_ingredients_csv, name='download_ingredients'),
    path('datasets/download/effects',     views.download_effects_csv,   name='download_effects'),
]
