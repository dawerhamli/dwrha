"""
URL patterns for influencers app
"""
from django.urls import path
from . import views

app_name = 'influencers'

urlpatterns = [
    path('', views.InfluencerHomeView.as_view(), name='home'),
    path('thanks/<int:influencer_id>/', views.InfluencerThanksView.as_view(), name='thanks'),
    path('register/', views.register_influencer, name='register'),
    path('dashboard/<int:influencer_id>/', views.influencer_dashboard, name='dashboard'),
    path('dashboard/<int:influencer_id>/export/', views.export_participants_excel, name='export_participants'),
    path('register-participant/<str:token>/', views.register_participant_page, name='register_participant'),
    path('register-participant/<str:token>/submit/', views.register_participant, name='register_participant_submit'),
    path('play/<str:token>/', views.play_wheel_page, name='play_wheel'),
    path('spin/<str:token>/', views.spin_wheel, name='spin_wheel'),
    path('participants-count/<str:token>/', views.get_participants_count, name='participants_count'),
]


