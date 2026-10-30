from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import CustomUser
from apps.core.journey import goal_cards, wellness_summary
from apps.core.models import Appointment, DailyCheckIn, GoalProgress, PersonalGoal, PredictionRecord


class JourneyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(email='journey@example.test', password='test-pass', is_approved=True)
        cls.other = CustomUser.objects.create_user(email='other-journey@example.test', password='test-pass', is_approved=True)

    def setUp(self):
        self.client.force_login(self.user)

    def checkin_data(self, **overrides):
        return {'mood': 'good', 'sleep_hours': '7.5', 'activity_minutes': '20', 'note': 'A quiet day', **overrides}

    def test_new_pages_require_login_and_share_navigation(self):
        guest = Client()
        for name in ('daily_checkin', 'personal_goals', 'health_timeline'):
            url = reverse(name)
            self.assertEqual(guest.get(url).status_code, 302)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'base/patient_workspace.html')
            self.assertContains(response, 'aria-label="Patient navigation"', count=1)
            self.assertIn('no-store', response['Cache-Control'])

    def test_checkin_save_updates_same_day_and_ignores_forged_owner_and_date(self):
        url = reverse('daily_checkin')
        self.assertRedirects(self.client.post(url, self.checkin_data(user=self.other.pk, date='2000-01-01')), url)
        entry = DailyCheckIn.objects.get(user=self.user)
        self.assertEqual(entry.date, timezone.localdate())
        self.assertEqual(entry.sleep_hours, Decimal('7.5'))
        self.assertEqual(entry.activity_minutes, 20)
        self.assertFalse(DailyCheckIn.objects.filter(user=self.other).exists())
        self.client.post(url, self.checkin_data(mood='okay', note='Updated'))
        self.assertEqual(DailyCheckIn.objects.filter(user=self.user).count(), 1)
        entry.refresh_from_db()
        self.assertEqual(entry.note, 'Updated')
        self.assertEqual(entry.mood, 'okay')
        response = self.client.get(url)
        self.assertContains(response, 'Saved today')
        self.assertContains(response, 'First check-in milestone')

    def test_checkin_local_date_near_midnight_and_daily_history(self):
        url = reverse('daily_checkin')
        with patch('django.utils.timezone.now', return_value=datetime(2026, 10, 15, 23, 30, tzinfo=dt_timezone.utc)):
            self.client.post(url, self.checkin_data())
        self.assertEqual(DailyCheckIn.objects.get(user=self.user).date, date(2026, 10, 16))
        with patch('django.utils.timezone.now', return_value=datetime(2026, 10, 16, 23, 30, tzinfo=dt_timezone.utc)):
            self.client.post(url, self.checkin_data())
        self.assertEqual(DailyCheckIn.objects.filter(user=self.user).count(), 2)

    def test_checkin_validation_and_private_escaped_notes(self):
        url = reverse('daily_checkin')
        for overrides in ({'sleep_hours': '25'}, {'sleep_hours': '-1'}, {'activity_minutes': '-1'},
                          {'activity_minutes': '1441'}, {'mood': 'unknown'}, {'note': 'x' * 501}):
            response = self.client.post(url, self.checkin_data(**overrides))
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(DailyCheckIn.objects.filter(user=self.user).exists())
        DailyCheckIn.objects.create(user=self.other, mood='low', sleep_hours=6, activity_minutes=0, note='Other private reflection')
        self.client.post(url, self.checkin_data(note='<script>alert(1)</script>'))
        response = self.client.get(url)
        self.assertNotContains(response, 'Other private reflection')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')

    def test_goal_creation_and_target_validation(self):
        url = reverse('personal_goals')
        for target in ('0', '366', '-1', 'abc'):
            response = self.client.post(url, {'title': 'My habit', 'target_days': target})
            self.assertTrue(response.context['form'].errors)
        self.assertFalse(PersonalGoal.objects.exists())
        self.assertRedirects(self.client.post(url, {'title': 'Make time to unwind', 'target_days': 2,
                                                   'user': self.other.pk}), url)
        goal = PersonalGoal.objects.get()
        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.target_days, 2)

    def test_goal_tick_idempotent_undo_target_and_badges(self):
        goal = PersonalGoal.objects.create(user=self.user, title='Walk', target_days=2)
        url = reverse('goal_progress', args=[goal.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        for _ in range(2):
            self.client.post(url, {'action': 'complete', 'date': '2000-01-01'})
        self.assertEqual(goal.progress.count(), 1)
        self.assertEqual(goal.progress.get().date, timezone.localdate())
        self.assertEqual(goal_cards(self.user)[0]['badge'], 'Halfway there')
        self.client.post(url, {'action': 'undo'})
        self.assertEqual(goal.progress.count(), 0)
        yesterday = timezone.localdate() - timedelta(days=1)
        GoalProgress.objects.create(goal=goal, date=yesterday)
        self.client.post(url, {'action': 'complete'})
        card = goal_cards(self.user)[0]
        self.assertTrue(card['complete'])
        self.assertEqual(card['percent'], 100)
        self.assertEqual(card['badge'], 'Goal reached')
        with patch('apps.core.journey_views.timezone.localdate', return_value=timezone.localdate() + timedelta(days=1)):
            self.client.post(url, {'action': 'complete'})
        self.assertEqual(goal.progress.count(), 2)

    def test_goal_archive_restore_and_ownership(self):
        goal = PersonalGoal.objects.create(user=self.user, title='Read', target_days=7)
        other = PersonalGoal.objects.create(user=self.other, title='Private other goal', target_days=7)
        other_url = reverse('goal_progress', args=[other.pk])
        for action in ('complete', 'undo', 'archive', 'restore'):
            self.assertEqual(self.client.post(other_url, {'action': action}).status_code, 404)
        url = reverse('goal_progress', args=[goal.pk])
        self.assertEqual(self.client.post(url, {'action': 'invalid'}).status_code, 400)
        self.client.post(url, {'action': 'archive'})
        self.client.post(url, {'action': 'complete'})
        self.assertEqual(goal.progress.count(), 0)
        self.assertNotContains(self.client.get(reverse('personal_goals')), 'Private other goal')
        self.assertEqual(len(self.client.get(reverse('personal_goals')).context['cards']), 0)
        self.assertEqual(len(self.client.get(reverse('personal_goals'), {'archived': 1}).context['cards']), 1)
        self.client.post(url, {'action': 'restore'})
        goal.refresh_from_db()
        self.assertFalse(goal.archived)

    def test_database_daily_uniqueness(self):
        DailyCheckIn.objects.create(user=self.user, mood='good', sleep_hours=8, activity_minutes=10)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DailyCheckIn.objects.create(user=self.user, mood='good', sleep_hours=8, activity_minutes=10)
        goal = PersonalGoal.objects.create(user=self.user, title='Read')
        GoalProgress.objects.create(goal=goal)
        with self.assertRaises(IntegrityError), transaction.atomic():
            GoalProgress.objects.create(goal=goal)

    def test_mutations_require_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        goal = PersonalGoal.objects.create(user=self.user, title='Read')
        for url, data in ((reverse('daily_checkin'), self.checkin_data()),
                          (reverse('personal_goals'), {'title': 'Read', 'target_days': 7}),
                          (reverse('goal_progress', args=[goal.pk]), {'action': 'complete'})):
            self.assertEqual(csrf_client.post(url, data).status_code, 403)

    def test_timeline_mixes_owned_events_filters_and_paginates(self):
        record = PredictionRecord.objects.create(user=self.user, disease='stroke', risk_level='Low Risk', probability=.2)
        PredictionRecord.objects.create(user=self.other, disease='lung_cancer', risk_level='Private result', probability=.5)
        Appointment.objects.create(user=self.user, reason='Follow-up', preferred_date=timezone.localdate())
        DailyCheckIn.objects.create(user=self.user, mood='good', sleep_hours=8, activity_minutes=10)
        goal = PersonalGoal.objects.create(user=self.user, title='Read')
        GoalProgress.objects.create(goal=goal)
        url = reverse('health_timeline')
        response = self.client.get(url)
        self.assertEqual(response.context['events'].paginator.count, 5)
        self.assertNotContains(response, 'Private result')
        self.assertContains(response, reverse('prediction_report', args=[record.pk]))
        dates = [event['date'] for event in response.context['events']]
        self.assertEqual(dates, sorted(dates, reverse=True))
        for kind, count in [('checks', 1), ('checkins', 1), ('goals', 2), ('appointments', 1)]:
            response = self.client.get(url, {'kind': kind})
            self.assertEqual(response.context['events'].paginator.count, count)
        self.assertEqual(self.client.get(url, {'kind': 'invalid'}).context['selected'], 'all')
        for offset in range(1, 14):
            DailyCheckIn.objects.create(user=self.user, date=timezone.localdate()-timedelta(days=offset),
                                        mood='okay', sleep_hours=7, activity_minutes=0)
        response = self.client.get(url, {'kind': 'checkins', 'page': 2})
        self.assertEqual(response.context['events'].number, 2)
        self.assertEqual(len(response.context['events']), 2)
        self.assertContains(response, 'kind=checkins&amp;page=1')

    def test_dashboard_focuses_on_goals_without_removed_features(self):
        self.assertEqual(wellness_summary(self.user)['next_step']['url'], reverse('personal_goals'))
        goal = PersonalGoal.objects.create(user=self.user, title='Make time to unwind', target_days=2)
        self.assertEqual(wellness_summary(self.user)['next_step']['text'], goal.title)
        GoalProgress.objects.create(goal=goal)
        summary = wellness_summary(self.user)
        self.assertEqual(summary['next_step']['url'], reverse('personal_goals'))
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Your next step')
        self.assertContains(response, reverse('personal_goals'))
        self.assertNotContains(response, reverse('health_timeline'))
        self.assertNotContains(response, reverse('daily_checkin'))
        self.assertNotContains(response, 'check-in days')
        response = self.client.get(reverse('profile'))
        self.assertNotContains(response, reverse('health_timeline'))
        self.assertNotContains(response, reverse('daily_checkin'))
