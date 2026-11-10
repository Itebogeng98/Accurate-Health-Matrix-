import json
import importlib
import re
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import OperationalError
from django.test import SimpleTestCase, TestCase
from django.urls import URLResolver, get_resolver, resolve, reverse

from apps.authentication.models import CustomUser, Role
from apps.core.models import (
    Appointment, DoctorContact, ExercisePlan, Notification,
    PredictionRecord,
)
from apps.core.services import _save_prediction, read_dataset_preview
from ml.prediction import predict_lung_cancer, predict_stroke, risk_label
from ml.preprocessing import _predict_with_pipeline


STROKE = {
    'gender': 'Male', 'age': 65, 'hypertension': 1, 'heart_disease': 1,
    'ever_married': 'Yes', 'work_type': 'Private', 'residence_type': 'Urban',
    'avg_glucose_level': 160, 'bmi': 32, 'smoking_status': 'smokes',
}
LUNG = {
    'gender': 'M', 'age': 60, **dict.fromkeys([
        'smoking', 'yellow_fingers', 'anxiety', 'peer_pressure', 'chronic_disease',
        'fatigue', 'allergy', 'wheezing', 'alcohol_consuming', 'coughing',
        'shortness_of_breath', 'swallowing_difficulty', 'chest_pain',
    ], 2),
}


class ArchitectureTests(SimpleTestCase):
    def test_routes_use_feature_handlers(self):
        for name in ('register', 'login', 'profile', 'logout', 'signup_api', 'obtain_token'):
            self.assertEqual(resolve(reverse(name)).func.__module__, 'apps.authentication.views')
        for name in ('home', 'dashboard', 'stroke_predict', 'doctors'):
            self.assertEqual(resolve(reverse(name)).func.__module__, 'apps.core.views')

    def test_all_route_paths_and_names_match_original(self):
        baseline = json.loads((settings.BASE_DIR / 'docs/restructuring_baseline.json').read_text())
        routes = []

        def walk(patterns, prefix=''):
            for pattern in patterns:
                if isinstance(pattern, URLResolver):
                    walk(pattern.url_patterns, prefix + str(pattern.pattern))
                else:
                    routes.append([prefix + str(pattern.pattern), pattern.name])

        walk(get_resolver().url_patterns)
        expected = baseline['routes'] + [
            ['accounts/users/', 'user_management'],
            ['accounts/users/activity/', 'activity_log'],
            ['accounts/users/<int:user_id>/<str:action>/', 'manage_user'],
            ['dashboard/reports/latest/', 'combined_report'],
            ['dashboard/reports/<int:record_id>/pdf/', 'prediction_report_pdf'],
            ['dashboard/reports/<int:record_id>/', 'prediction_report'],
            ['dashboard/journey/', 'health_timeline'],
            ['dashboard/check-in/', 'daily_checkin'],
            ['dashboard/goals/', 'personal_goals'],
            ['dashboard/goals/<int:goal_id>/progress/', 'goal_progress'],
        ]
        self.assertCountEqual(routes, expected)

    def test_model_tables_fields_and_relationships_match_original(self):
        baseline = json.loads((settings.BASE_DIR / 'docs/restructuring_baseline.json').read_text())
        models = {
            model._meta.label_lower: {
                'table': model._meta.db_table,
                'fields': [str(field.deconstruct()[1:]) for field in
                           model._meta.local_fields + model._meta.local_many_to_many
                           if not (model is Appointment and field.name in {
                               'doctor_name', 'doctor_email', 'email_status', 'email_sent_at',
                               'report', 'request_token'})],
            } for model in apps.get_models() if model._meta.label_lower in baseline['models']
        }
        # Callable defaults include process-specific addresses in repr().
        normalize = lambda value: re.sub(r' at 0x[0-9A-Fa-f]+', '', json.dumps(value, sort_keys=True))
        self.assertEqual(normalize(models), normalize(baseline['models']))
        self.assertIs(get_user_model(), CustomUser)
        from apps.authentication.models import CustomUser as LegacyUser
        from apps.core.models import PredictionRecord as LegacyPrediction
        self.assertIs(LegacyUser, CustomUser)
        self.assertIs(LegacyPrediction, PredictionRecord)

    def test_admin_registration_and_canonical_handlers(self):
        for model in (CustomUser, Role, Appointment, Notification, PredictionRecord,
                      DoctorContact, ExercisePlan):
            self.assertIn(model, admin.site._registry)
        for name in ('home', 'login', 'dashboard', 'stroke_predict', 'doctors'):
            self.assertEqual(resolve(reverse(name)).func.__module__, 'apps.authentication.views' if name == 'login' else 'apps.core.views')

    @patch('ml.prediction._load_model', return_value=None)
    def test_prediction_fallbacks_and_thresholds(self, loader):
        self.assertEqual(predict_stroke(STROKE), (0.95, 'High Risk'))
        self.assertEqual(predict_stroke({}), (0, 'Low Risk'))
        self.assertEqual(predict_lung_cancer(LUNG), (0.95, 'High Risk'))
        self.assertEqual(predict_lung_cancer({}), (0, 'Low Risk'))
        self.assertEqual([risk_label(p) for p in (.39, .4, .69, .7)],
                         ['Low Risk', 'Medium Risk', 'Medium Risk', 'High Risk'])

    def test_pipeline_receives_named_dataframe(self):
        model = Mock()
        model.predict_proba.return_value = [[.2, .8]]
        self.assertEqual(_predict_with_pipeline(model, STROKE), .8)
        self.assertEqual(model.predict_proba.call_args.args[0].to_dict('records'), [STROKE])
        with patch('ml.prediction._load_model', return_value=model):
            self.assertEqual(predict_stroke(STROKE), (.8, 'High Risk'))
        model.predict_proba.side_effect = ValueError('incompatible pipeline')
        self.assertIsNone(_predict_with_pipeline(model, STROKE))

    def test_model_loader_uses_existing_artifact_path(self):
        from ml.model_loader import _load_model
        with TemporaryDirectory() as directory:
            with patch('ml.model_loader.MODEL_DIR', Path(directory)):
                self.assertIsNone(_load_model('missing.pkl'))
                artifact = Path(directory) / 'stroke_model.pkl'
                artifact.touch()
                with patch('ml.model_loader.joblib.load', return_value='model') as load:
                    self.assertEqual(_load_model('stroke_model.pkl'), 'model')
                    load.assert_called_once_with(artifact)

    def test_csv_preview_limits_rows_and_preserves_columns(self):
        with TemporaryDirectory() as directory:
            (Path(directory) / 'sample.csv').write_text('a,b\n1,2\n3,4\n')
            with patch('apps.core.services.DATASETS_DIR', Path(directory)):
                preview = read_dataset_preview('sample.csv', limit=1)
                self.assertEqual(preview['rows'], [['1', '2']])
                self.assertEqual(preview['total_rows'], 2)
                self.assertEqual(preview['columns'], ['a', 'b'])
                self.assertFalse(read_dataset_preview('missing.csv')['exists'])


class WorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            email='patient@example.test', password='test-password',
            first_name='Test', last_name='Patient', is_approved=True,
        )
        cls.other = CustomUser.objects.create_user(
            email='other@example.test', password='test-password',
            first_name='Other', last_name='Patient',
        )

    def test_signup_and_approval_gate(self):
        response = self.client.post(reverse('signup_api'), {
            'email': 'new@example.test', 'password': 'test-password', 'confirm_password': 'test-password',
            'first_name': 'New', 'last_name': 'Patient',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        user = CustomUser.objects.get(email='new@example.test')
        self.assertTrue(user.check_password('test-password'))
        self.assertFalse(user.is_approved)
        self.assertEqual(self.client.post(reverse('obtain_token'), {
            'email': user.email, 'password': 'test-password',
        }, content_type='application/json').status_code, 403)

    def test_api_login_and_browser_login_logout(self):
        response = self.client.post(reverse('obtain_token'), {
            'email': self.user.email, 'password': 'test-password',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.client.logout()
        with patch('apps.authentication.views.requests.post', return_value=Mock(status_code=200, json=lambda: data)):
            self.assertRedirects(self.client.post(reverse('login'), {
                'email': self.user.email, 'password': 'test-password',
            }), reverse('dashboard'))
        self.assertEqual(self.client.session['auth_token'], data['token'])
        self.assertRedirects(self.client.get(reverse('logout')), reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_browser_registration_preserves_api_contract(self):
        with patch('apps.authentication.views.requests.get', return_value=Mock(status_code=200, json=lambda: {'data': []})), \
             patch('apps.authentication.views.requests.post', return_value=Mock(status_code=201, json=lambda: {})) as post:
            response = self.client.post(reverse('register'), {
                'email': 'new@example.test', 'password': 'test-password', 'confirm_password': 'test-password',
                'first_name': 'New', 'last_name': 'Patient',
            })
            self.assertRedirects(response, reverse('login'))
            self.assertTrue(post.call_args.args[0].endswith('/accounts/api/signup/'))

    def test_authentication_required_and_api_permissions(self):
        for name in ('dashboard', 'profile', 'appointments', 'notifications',
                     'stroke_predict', 'lung_predict', 'doctors', 'exercises', 'data_tables'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)
        self.assertEqual(self.client.post(reverse('stroke_prediction_api'), {}).status_code, 403)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('retrain_models_api'), {}).status_code, 403)

    def test_authenticated_pages_render(self):
        self.client.force_login(self.user)
        for name in ('home', 'dashboard', 'profile', 'appointments', 'notifications',
                     'stroke_predict', 'lung_predict', 'diet_home', 'doctors', 'exercises', 'data_tables'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                if name != 'home':
                    self.assertTemplateUsed(response, 'base/patient_workspace.html')
                    self.assertContains(response, 'aria-label="Patient navigation"', count=1)
                    self.assertContains(response, 'class="matrix-topbar"', count=1)
                    self.assertContains(response, reverse('dashboard') + '#reports')
        with patch('apps.core.services.get_kaggle_credentials', return_value=('', '')):
            self.assertEqual(self.client.get(reverse('dashboard_dataset', args=['stroke-dataset'])).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard_dataset', args=['missing'])).status_code, 404)

    def test_food_guide_pages_preserve_search_and_bound_card_count(self):
        self.client.force_login(self.user)
        foods = [{'food': f'Test food {i}'} for i in range(14)]
        with patch('apps.core.views.search_foods', return_value={
            'foods': foods, 'total_count': 14, 'match_count': 14,
        }) as search:
            response = self.client.get(reverse('diet_home'), {'q': 'oats & nuts', 'page': 2})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(list(response.context['food_page']), foods[6:12])
            self.assertContains(response, 'q=oats%20%26%20nuts&amp;page=3')
            search.assert_called_once_with('oats & nuts')
            for page, expected in [('invalid', 1), ('999', 3)]:
                response = self.client.get(reverse('diet_home'), {'page': page})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['food_page'].number, expected)

    def test_printable_reports_require_login_and_ownership(self):
        record = PredictionRecord.objects.create(user=self.user, disease='stroke',
            risk_level='Medium Risk', probability=.42, input_data=STROKE,
            recommendation='Saved advice')
        private = PredictionRecord.objects.create(user=self.other, disease='lung_cancer',
            risk_level='High Risk', probability=.9, recommendation='Private advice')
        for url in (reverse('prediction_report', args=[record.pk]), reverse('combined_report')):
            self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get(reverse('prediction_report', args=[record.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '42.00%')
        self.assertContains(response, 'Saved advice')
        self.assertContains(response, 'Information used')
        self.assertContains(response, 'Print / save as PDF')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.client.get(reverse('prediction_report', args=[private.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('prediction_report', args=[99999])).status_code, 404)
        response = self.client.get(reverse('combined_report'))
        self.assertContains(response, 'Lung Cancer: no saved check yet.')
        self.assertNotContains(response, 'Private advice')

    def test_combined_report_uses_latest_record_per_condition(self):
        self.client.force_login(self.user)
        PredictionRecord.objects.create(user=self.user, disease='stroke', risk_level='Low Risk',
            probability=.1, recommendation='Old stroke advice')
        stroke = PredictionRecord.objects.create(user=self.user, disease='stroke', risk_level='Medium Risk',
            probability=.5, input_data=STROKE, recommendation='Latest stroke advice')
        lung = PredictionRecord.objects.create(user=self.user, disease='lung_cancer', risk_level='High Risk',
            probability=.8, input_data=LUNG, recommendation='Latest lung advice')
        response = self.client.get(reverse('combined_report'))
        self.assertEqual([item['record'].pk for item in response.context['reports']], [stroke.pk, lung.pk])
        self.assertContains(response, 'Latest stroke advice')
        self.assertContains(response, 'Latest lung advice')
        self.assertNotContains(response, 'Old stroke advice')
        self.assertContains(response, '80.00%')
        self.assertEqual(response.context['missing'], [])
        self.assertIn(('Smoking', 'Yes'), response.context['reports'][1]['inputs'])

    def test_empty_combined_report_and_prediction_report_links(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('combined_report'))
        self.assertContains(response, 'No reports yet')
        self.assertNotContains(response, 'id="print-report"')
        for name, data, predictor in [('stroke_predict', STROKE, 'predict_stroke'),
                                      ('lung_predict', LUNG, 'predict_lung_cancer')]:
            with patch('apps.core.views.' + predictor, return_value=(.25, 'Low Risk')):
                response = self.client.post(reverse(name), data)
            record = PredictionRecord.objects.filter(user=self.user).first()
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, reverse('prediction_report', args=[record.pk]))
            self.assertContains(response, reverse('combined_report'))

    def test_appointment_notification_and_profile_updates(self):
        self.client.force_login(self.user)
        record = PredictionRecord.objects.create(user=self.user, disease='stroke', probability=.43)
        self.assertRedirects(self.client.post(reverse('appointments'), {
            'doctor_email': 'ie.sebapu@gmail.com', 'report': record.pk,
            'share_report': 'on', 'request_token': str(uuid.uuid4()),
            'reason': 'Follow-up', 'preferred_date': '2027-01-01', 'notes': 'Test',
        }), reverse('appointments'))
        self.assertEqual(Appointment.objects.get(user=self.user).status, 'pending')
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 1)
        other = Notification.objects.create(user=self.other, title='Private', message='Other user')
        self.client.post(reverse('notifications'))
        self.assertFalse(Notification.objects.filter(user=self.user, is_read=False).exists())
        other.refresh_from_db()
        self.assertFalse(other.is_read)
        self.client.post(reverse('profile'), {'first_name': 'Changed', 'last_name': 'Patient', 'phone_number': '0123456789'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Changed')

    @patch('ml.prediction._load_model', return_value=None)
    def test_browser_and_api_predictions_are_persisted(self, loader):
        self.client.force_login(self.user)
        for name, payload in [('stroke_predict', STROKE), ('lung_predict', LUNG),
                              ('stroke_prediction_api', STROKE), ('lung_prediction_api', LUNG)]:
            response = self.client.post(reverse(name), payload)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(PredictionRecord.objects.filter(user=self.user).count(), 4)
        self.assertEqual(self.client.post(reverse('stroke_prediction_api'), {}).status_code, 400)
        with patch('apps.core.services.PredictionRecord.objects.create', side_effect=OperationalError):
            self.assertIsNone(_save_prediction(self.user, 'stroke', 'Low Risk', 0, {}, ''))

    def test_admin_and_retraining_endpoint(self):
        self.user.is_staff = self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/admin/accounts/customuser/').status_code, 200)
        with patch('scripts.train_models.train_stroke') as stroke, patch('scripts.train_models.train_lung') as lung:
            self.assertEqual(self.client.post(reverse('retrain_models_api')).status_code, 200)
            stroke.assert_called_once()
            lung.assert_called_once()
