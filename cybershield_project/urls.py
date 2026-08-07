from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

from training.models import TrainingModule


def landing_page(request):
    return render(request, 'landing.html', {
        'module_count': TrainingModule.objects.count(),
    })

urlpatterns = [
    path('', landing_page, name='landing'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('training/', include('training.urls')),
    path('phishing/', include('phishing.urls')),
    path('dashboard/', include('dashboard.urls')),
]