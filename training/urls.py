from django.urls import path
from . import views

urlpatterns = [
    path('', views.module_list, name='module_list'),
    path('create/', views.create_module, name='create_module'),
    path('certificates/', views.my_certificates, name='my_certificates'),
    path('certificates/<str:certificate_id>/', views.certificate_detail, name='certificate_detail'),
    path('certificates/<str:certificate_id>/pdf/', views.certificate_pdf, name='certificate_pdf'),
    path('<int:module_id>/', views.module_detail, name='module_detail'),
    path('<int:module_id>/quiz/', views.take_quiz, name='take_quiz'),
    path('<int:module_id>/mark-viewed/<str:tab>/', views.mark_viewed, name='mark_viewed'),
]
