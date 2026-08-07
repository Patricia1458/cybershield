from django.urls import path
from . import views

urlpatterns = [
    path('', views.campaign_list, name='campaign_list'),
    path('analytics/', views.analytics_view, name='phishing_analytics'),
    path('simulations/', views.my_phishing_view, name='my_simulations'),
    path('simulations/<uuid:token>/', views.simulation_detail, name='simulation_detail'),
    path('<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('track/<uuid:token>/', views.track_click, name='track_click'),
    path('report/<uuid:token>/', views.report_suspicious, name='report_suspicious'),
]
