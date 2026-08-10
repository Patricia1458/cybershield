from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CyberShieldLoginForm

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='accounts/login.html', authentication_form=CyberShieldLoginForm),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'password-reset/confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete',
    ),
    path('home/', views.dashboard_home, name='dashboard_home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('invite/', views.invite_employee, name='invite_employee'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:user_id>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:user_id>/assign/', views.assign_training, name='assign_training'),
]