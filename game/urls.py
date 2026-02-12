"""
URL patterns for game app
"""
from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('play/<str:token>/', views.play_game, name='play'),
    path('spin/<str:token>/', views.spin_wheel, name='spin'),
    path('dashboard/<str:token>/', views.game_dashboard, name='dashboard'),
]
