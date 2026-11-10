from django.urls import path
from . import views
from . import journey_views

urlpatterns = [
    path('dashboard/reports/<int:record_id>/pdf/', views.prediction_report_pdf, name='prediction_report_pdf'),
    path('', views.home, name='home'),
    path('predict/stroke/', views.stroke_predict, name='stroke_predict'),
    path('predict/lung-cancer/', views.lung_predict, name='lung_predict'),
    path('predict/api/stroke/', views.stroke_prediction_api, name='stroke_prediction_api'),
    path('predict/api/lung/', views.lung_prediction_api, name='lung_prediction_api'),
    path('predict/api/admin/retrain-models/', views.retrain_models_api, name='retrain_models_api'),
    path('diet/', views.diet_home, name='diet_home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/journey/', journey_views.health_timeline, name='health_timeline'),
    path('dashboard/check-in/', journey_views.daily_checkin, name='daily_checkin'),
    path('dashboard/goals/', journey_views.personal_goals, name='personal_goals'),
    path('dashboard/goals/<int:goal_id>/progress/', journey_views.goal_progress, name='goal_progress'),
    path('dashboard/reports/latest/', views.prediction_report, name='combined_report'),
    path('dashboard/reports/<int:record_id>/', views.prediction_report, name='prediction_report'),
    path('dashboard/appointments/', views.appointments_view, name='appointments'),
    path('dashboard/notifications/', views.notifications_view, name='notifications'),
    path('dashboard/datasets/<slug:dataset_slug>/', views.dataset_detail, name='dashboard_dataset'),
    path('wellness/doctors/', views.doctors, name='doctors'),
    path('wellness/exercises/', views.exercises, name='exercises'),
    path('wellness/data-tables/', views.data_tables, name='data_tables'),
]
