"""Browser and API request handlers, grouped by feature."""
from contextlib import redirect_stdout
from io import StringIO

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import OperationalError, ProgrammingError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .forms import AppointmentForm, StrokePredictionForm, LungCancerPredictionForm
from .models import Appointment, Notification, PredictionRecord
from .journey import wellness_summary
from .services import (
    _save_prediction, get_patient_context, get_dataset_by_slug,
    read_dataset_preview, read_dataset_from_kaggle,
)
from .wellness_data import DOCTORS, EXERCISES, prediction_doctor_support
from ml.prediction import predict_stroke, predict_lung_cancer
from ml.recommendation import recommend_diet
from ml.nutrition import search_foods, SOURCE_URL as NUTRITION_SOURCE_URL

# Dashboard and health data

def home(request):
    return render(request, 'base/home.html')


@login_required
def dashboard(request):
    try:
        all_records = PredictionRecord.objects.filter(user=request.user)
        records = all_records[:10]
        total_reports = all_records.count()
        latest_record = all_records.first()
    except (OperationalError, ProgrammingError):
        records = []
        total_reports = 0
        latest_record = None

    context = {
        'records': records,
        'total_reports': total_reports,
        'latest_record': latest_record,
        'appointments': Appointment.objects.filter(user=request.user)[:4],
        'notifications': Notification.objects.filter(user=request.user)[:4],
        'pending_appointments': Appointment.objects.filter(user=request.user, status='pending').count(),
        **get_patient_context(request.user),
        **wellness_summary(request.user),
    }
    return render(request, 'core/dashboard/dashboard.html', context)


@login_required
def dataset_detail(request, dataset_slug):
    dataset = get_dataset_by_slug(dataset_slug)
    preview = read_dataset_preview(dataset['filename'])
    if not preview['exists']:
        preview = read_dataset_from_kaggle(dataset, limit=50)
    context = {
        **get_patient_context(request.user),
        'selected_dataset': dataset,
        'preview': preview,
    }
    return render(request, 'core/dashboard/dataset_detail.html', context)


@login_required
def appointments_view(request):
    form = AppointmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        appointment = form.save(commit=False)
        appointment.user = request.user
        appointment.save()
        Notification.objects.create(
            user=request.user,
            title='Appointment request submitted',
            message=f'Your appointment request for {appointment.preferred_date:%Y-%m-%d} is pending review.',
        )
        messages.success(request, 'Appointment request submitted successfully.')
        return redirect('appointments')

    context = {
        **get_patient_context(request.user),
        'form': form,
        'appointments': Appointment.objects.filter(user=request.user),
    }
    return render(request, 'core/dashboard/appointments.html', context)


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    if request.method == 'POST':
        notifications.update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')

    context = {
        **get_patient_context(request.user),
        'notifications': notifications,
    }
    return render(request, 'core/dashboard/notifications.html', context)


# Predictions

@login_required
@never_cache
def prediction_report(request, record_id=None):
    records = PredictionRecord.objects.filter(user=request.user)
    if record_id is not None:
        selected = [get_object_or_404(records, pk=record_id)]
        missing = []
    else:
        selected = []
        missing = []
        for disease, label in PredictionRecord.DISEASE_CHOICES:
            record = records.filter(disease=disease).order_by('-created_at', '-pk').first()
            if record is None:
                missing.append(label)
            else:
                selected.append(record)
    reports = []
    for record in selected:
        form = StrokePredictionForm() if record.disease == 'stroke' else LungCancerPredictionForm()
        inputs = []
        for name, field in form.fields.items():
            if name not in record.input_data:
                continue
            value = record.input_data[name]
            if hasattr(field, 'choices'):
                value = next((label for key, label in field.choices if str(key) == str(value)), value)
            inputs.append((field.label or name.replace('_', ' ').capitalize(), value))
        reports.append({
            'record': record,
            'score': round(record.probability * 100, 2),
            'inputs': inputs,
            'doctor_support': prediction_doctor_support(record.disease, record.risk_level),
        })
    return render(request, 'core/predictions/report.html', {
        'reports': reports,
        'missing': missing,
        'combined': record_id is None,
        'generated_at': timezone.now(),
    })


@login_required
def stroke_predict(request):
    form = StrokePredictionForm(request.POST or None)
    result = None

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        probability, risk = predict_stroke(data)
        foods = recommend_diet('stroke', risk)
        advice = 'Focus on low-salt, high-fibre meals, fruits, vegetables, whole grains, and regular exercise.'
        record = _save_prediction(request.user, 'stroke', risk, probability, data, advice)
        if record is None:
            messages.warning(request, 'Prediction worked, but the report was not saved because database migrations have not been run yet. Run: python manage.py migrate')
        result = {
            'record': record,
            'probability_percent': round(probability * 100, 2),
            'risk': risk,
            'foods': foods,
            'advice': advice,
            'doctor_support': prediction_doctor_support('stroke', risk),
        }

    return render(request, 'core/predictions/stroke.html', {'form': form, 'result': result})


@login_required
def lung_predict(request):
    form = LungCancerPredictionForm(request.POST or None)
    result = None

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        probability, risk = predict_lung_cancer(data)
        foods = recommend_diet('lung_cancer', risk)
        advice = 'Avoid smoking, reduce alcohol use, increase antioxidant-rich foods, and seek professional screening if symptoms persist.'
        record = _save_prediction(request.user, 'lung_cancer', risk, probability, data, advice)
        if record is None:
            messages.warning(request, 'Prediction worked, but the report was not saved because database migrations have not been run yet. Run: python manage.py migrate')
        result = {
            'record': record,
            'probability_percent': round(probability * 100, 2),
            'risk': risk,
            'foods': foods,
            'advice': advice,
            'doctor_support': prediction_doctor_support('lung_cancer', risk),
        }

    return render(request, 'core/predictions/lung.html', {'form': form, 'result': result})


def _prediction_response(request, form_class, disease, predictor, advice):
    form = form_class(request.data)
    if not form.is_valid():
        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': form.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    data = form.cleaned_data
    probability, risk = predictor(data)
    foods = recommend_diet(disease, risk)
    record = _save_prediction(request.user, disease, risk, probability, data, advice)

    return Response({
        'status': 'success',
        'message': 'Prediction generated successfully',
        'data': {
            'record_id': record.id if record else None,
            'disease': disease,
            'risk': risk,
            'probability': probability,
            'probability_percent': round(probability * 100, 2),
            'advice': advice,
            'foods': foods,
        },
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stroke_prediction_api(request):
    return _prediction_response(
        request,
        StrokePredictionForm,
        'stroke',
        predict_stroke,
        'Focus on low-salt, high-fibre meals, fruits, vegetables, whole grains, and regular exercise.',
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lung_prediction_api(request):
    return _prediction_response(
        request,
        LungCancerPredictionForm,
        'lung_cancer',
        predict_lung_cancer,
        'Avoid smoking, reduce alcohol use, increase antioxidant-rich foods, and seek professional screening if symptoms persist.',
    )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def retrain_models_api(request):
    try:
        from scripts.train_models import train_stroke, train_lung

        output = StringIO()
        with redirect_stdout(output):
            train_stroke()
            train_lung()

        return Response({
            'status': 'success',
            'message': 'Model retraining completed.',
            'output': output.getvalue(),
        }, status=status.HTTP_200_OK)
    except Exception as exc:
        return Response({
            'status': 'error',
            'message': 'Model retraining failed.',
            'error': str(exc),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Recommendations

def diet_home(request):
    foods = recommend_diet('stroke', 'Medium Risk') + recommend_diet('lung_cancer', 'Medium Risk')
    foods = list({food['food']: food for food in foods}.values())
    query = request.GET.get('q', '').strip()[:100]
    food_guide = search_foods(query)
    food_page = Paginator(food_guide['foods'], 6).get_page(request.GET.get('page'))
    return render(request, 'core/recommendations/diet.html', {
        'foods': foods,
        'query': query,
        'food_guide': food_guide,
        'food_page': food_page,
        'nutrition_source_url': NUTRITION_SOURCE_URL,
    })


# Wellness

@login_required
def doctors(request):
    speciality = request.GET.get('speciality', 'all')
    doctors = DOCTORS
    if speciality != 'all':
        doctors = [d for d in DOCTORS if speciality.lower() in d['specialty'].lower()]
    return render(request, 'core/wellness/doctors.html', {'doctors': doctors, 'speciality': speciality})


@login_required
def exercises(request):
    category = request.GET.get('category', 'all')
    exercises = EXERCISES
    if category != 'all':
        exercises = [e for e in EXERCISES if category.lower() in e['category'].lower()]
    return render(request, 'core/wellness/exercises.html', {'exercises': exercises, 'category': category})


@login_required
def data_tables(request):
    tables = [
        {
            'table': 'auth_user',
            'purpose': 'Stores registered website users created through Register/Login.',
            'etl_stage': 'Load: Django writes user data directly into this table.'
        },
        {
            'table': 'predictions_predictionrecord',
            'purpose': 'Stores every stroke/lung cancer prediction result, risk level, input JSON and recommendation.',
            'etl_stage': 'Load: prediction output is saved after the form is submitted.'
        },
        {
            'table': 'wellness_doctorcontact',
            'purpose': 'Optional database table for Gauteng doctors/specialists if you choose to load the static directory into DB.',
            'etl_stage': 'Transform/Load: doctor contacts are cleaned and displayed in the Doctors page.'
        },
        {
            'table': 'wellness_exerciseplan',
            'purpose': 'Optional database table for exercise recommendations if you choose to manage exercises from admin.',
            'etl_stage': 'Transform/Load: exercise plans are categorized by stroke, lung health and general wellness.'
        },
    ]
    etl_files = [
        {'name': 'datasets/healthcare-dataset-stroke-data.csv', 'status': 'Local CSV; inspect availability on the dashboard', 'used_for': 'Stroke model training'},
        {'name': 'datasets/lung cancer.csv', 'status': 'Local CSV; inspect availability on the dashboard', 'used_for': 'Lung cancer model training'},
        {'name': 'datasets/food_nutrition.csv', 'status': 'Local CSV; inspect availability on the dashboard', 'used_for': 'Searchable food guide and recommendation nutrient values'},
        {'name': 'scripts/train_models.py', 'status': 'ETL + training script', 'used_for': 'Extract CSV, clean/transform data, train models, export .pkl files'},
        {'name': 'ml_models/*.pkl', 'status': 'Generated after training', 'used_for': 'Prediction engine used by Django views'},
    ]
    return render(request, 'core/wellness/data_tables.html', {'tables': tables, 'etl_files': etl_files})
