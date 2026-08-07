from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('my-progress/', views.my_progress_view, name='my_progress'),
    path('my-analytics/', views.my_analytics_view, name='my_analytics'),
]
