r"""Run from repository root: env\Scripts\python.exe docs/assignment3/evidence/measure.py.
Uses only in-memory SQLite, synthetic data and blocked outbound requests.
"""
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.test_settings'
import django
django.setup()
import json
import platform
import statistics
import time
from importlib.metadata import version
from unittest.mock import patch
from django.conf import settings
from django.core.management import call_command
from django.test import Client, override_settings
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.settings import api_settings
from apps.authentication.models import CustomUser, Role
from apps.core.models import PredictionRecord, Appointment, Notification, DoctorContact, ExercisePlan
from apps.core.tests.test_regression import STROKE
from ml.prediction import predict_stroke
from apps.core.services import read_dataset_from_kaggle, EXPECTED_DATASETS

OUT = Path(__file__).parent
def timing(fn, n=100):
    fn() # warm-up excluded
    values = []
    for _ in range(n):
        start = time.perf_counter_ns()
        fn()
        values.append((time.perf_counter_ns()-start)/1e6)
    return {'n': n, 'median_ms': statistics.median(values), 'p95_ms': sorted(values)[94], 'max_ms': max(values)}

call_command('migrate', verbosity=0)
user = CustomUser.objects.create_user(email='evidence@example.test', password='synthetic-only', first_name='Evidence', last_name='User', is_approved=True)
results = {'prepared': '2026-09-30', 'environment': {'os': platform.system(), 'release': platform.release(), 'python': platform.python_version(), 'architecture': platform.machine(), 'logical_cpus': os.cpu_count(), 'packages': {p: version(p) for p in ['Django','djangorestframework','numpy','pandas','scikit-learn','joblib','PyMySQL']}, 'database': 'SQLite in-memory', 'client': 'Django test client; no browser/network/static downloads', 'fixtures': '1 synthetic approved user; no original database access'}, 'files': {d: [p.name for p in (ROOT/d).glob('*') if p.is_file()] for d in ['datasets','ml_models']}, 'authentication_classes': [c.__name__ for c in api_settings.DEFAULT_AUTHENTICATION_CLASSES]}
with override_settings(ALLOWED_HOSTS=['testserver']), patch('requests.get', side_effect=RuntimeError('Outbound requests disabled')):
    client = Client()
    protected = ['/dashboard/','/accounts/profile/','/dashboard/appointments/','/dashboard/notifications/','/predict/stroke/','/predict/lung-cancer/','/wellness/doctors/','/wellness/exercises/','/wellness/data-tables/']
    results['anonymous_pages'] = {p: client.get(p).status_code for p in protected}
    results['anonymous_prediction_api'] = client.post('/predict/api/stroke/', STROKE).status_code
    client.force_login(user)
    def dashboard():
        assert client.get('/dashboard/').status_code == 200
    def prediction():
        assert client.post('/predict/stroke/', STROKE).status_code == 200
    results['dashboard'] = timing(dashboard)
    results['stroke_page_post'] = timing(prediction)
    results['fallback_scoring'] = timing(lambda: predict_stroke(STROKE))
    with patch('apps.core.services.get_kaggle_credentials', return_value=('', '')):
        preview = read_dataset_from_kaggle(EXPECTED_DATASETS[0], 50)
        results['missing_credentials'] = {'exists': preview['exists'], 'source_mode': preview['source_mode']}
    results['sanitised_api_example'] = client.post('/predict/api/stroke/', STROKE).json()
    results['sanitised_api_example']['data']['record_id'] = '<generated integer>'
    basic = Client(HTTP_AUTHORIZATION='Basic ZXZpZGVuY2VAZXhhbXBsZS50ZXN0OnN5bnRoZXRpYy1vbmx5')
    user.is_approved = False
    user.save(update_fields=['is_approved'])
    results['unapproved_basic_auth_prediction_status'] = basic.post('/predict/api/stroke/', STROKE).status_code
with override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher']):
    hashed = make_password('synthetic-only')
    results['production_hasher_check'] = {'algorithm': hashed.split('$')[0], 'differs_from_plaintext': hashed != 'synthetic-only', 'check_password': check_password('synthetic-only', hashed)}
(OUT/'measurements.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
lines = ['# Model-derived data dictionary', '', 'Generated from Django model metadata, not live database rows. Domain models are defined in `apps/authentication/models.py` and `apps/core/models.py`. Inherited authentication fields are included. Empty values are allowed only where stated. Choice validation occurs in forms/model validation; it is not automatically a SQL CHECK constraint.', '']
for model in [Role, CustomUser, PredictionRecord, Appointment, Notification, DoctorContact, ExercisePlan]:
    lines += ['## '+model.__name__+' — `'+model._meta.db_table+'`', '', '| Field | Type | Constraints / purpose |', '| --- | --- | --- |']
    for f in model._meta.fields + model._meta.many_to_many:
        constraints = []
        if f.primary_key: constraints.append('primary key')
        if f.unique: constraints.append('unique')
        constraints += ['nullable' if f.null else 'not null', 'form blank allowed' if f.blank else 'form required']
        if f.max_length: constraints.append('max length '+str(f.max_length))
        if f.choices: constraints.append('choices '+', '.join(str(c[0]) for c in f.choices))
        if f.is_relation:
            constraints.append('references '+f.related_model.__name__)
            if getattr(f.remote_field, 'on_delete', None): constraints.append('delete '+f.remote_field.on_delete.__name__)
        if f.has_default(): constraints.append('default '+(f.default.__name__ if callable(f.default) else str(f.default)))
        if getattr(f,'auto_now_add',False): constraints.append('creation timestamp')
        lines.append('| '+f.name+' | '+f.get_internal_type()+' | '+'; '.join(constraints)+' |')
    lines.append('')
(OUT/'DATA_DICTIONARY.md').write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps({k:v for k,v in results.items() if k != 'sanitised_api_example'}, indent=2))
