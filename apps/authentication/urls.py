from django.urls import path
from . import views

urlpatterns = [
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/api/token/', views.obtain_token, name='obtain_token'),
    path('accounts/api/signup/', views.signup_api, name='signup_api'),
]
