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
    path('leap/', views.leap_wheel_play, name='leap_wheel'),
    path('leap/spin/', views.leap_wheel_spin, name='leap_wheel_spin'),
    path('leap/prizes/', views.leap_wheel_prizes, name='leap_wheel_prizes'),
]
