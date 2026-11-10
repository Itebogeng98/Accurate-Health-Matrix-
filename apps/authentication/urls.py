from django.urls import path
from . import views, management_views

urlpatterns = [
    path('accounts/users/', management_views.user_management, name='user_management'),
    path('accounts/users/activity/', management_views.activity_log, name='activity_log'),
    path('accounts/users/<int:user_id>/<str:action>/', management_views.manage_user, name='manage_user'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/api/token/', views.obtain_token, name='obtain_token'),
    path('accounts/api/signup/', views.signup_api, name='signup_api'),
]
