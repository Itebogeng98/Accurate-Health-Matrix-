from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.authtoken.models import Token
from .models import CustomUser, Role, UserActivity


class UserManagementTests(TestCase):
    def setUp(self):
        self.role = Role.objects.get_or_create(role='Patient')[0]
        self.admin = CustomUser.objects.create_user(email='admin@example.com', password='Admin!923', role=self.role, is_staff=True, is_approved=True)
        self.patient = CustomUser.objects.create_user(email='patient@example.com', password='Patient!923', role=self.role)
        self.client.force_login(self.admin)

    def action_url(self, action, target=None):
        return reverse('manage_user', args=[(target or self.patient).pk, action])

    def test_non_staff_cannot_manage_even_with_admin_role(self):
        self.patient.role = Role.objects.get_or_create(role='Admin')[0]
        self.patient.save()
        self.client.force_login(self.patient)
        for url in (reverse('user_management'), reverse('activity_log'), self.action_url('edit'), self.action_url('approve')):
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url).status_code, 403)

    def test_anonymous_is_redirected(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('user_management')).status_code, 302)

    def test_list_search_and_filter(self):
        response = self.client.get(reverse('user_management'), {'q': 'patient@', 'status': 'pending'})
        self.assertContains(response, 'patient@example.com')
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'User Management')

    def test_get_is_review_only_then_approve_and_decline(self):
        self.assertEqual(self.client.get(self.action_url('approve')).status_code, 200)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.is_approved)
        self.client.post(self.action_url('approve'))
        self.patient.refresh_from_db()
        self.assertTrue(self.patient.is_approved)
        self.assertTrue(self.patient.is_active)
        Token.objects.create(user=self.patient)
        patient_client = Client()
        patient_client.force_login(self.patient)
        self.client.post(self.action_url('decline'))
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.is_active)
        self.assertFalse(self.patient.is_approved)
        self.assertFalse(Token.objects.filter(user=self.patient).exists())
        self.assertEqual(patient_client.get(reverse('profile')).status_code, 302)
        self.assertTrue(UserActivity.objects.filter(action='Declined user', target_email=self.patient.email).exists())

    def test_edit_does_not_grant_privileges(self):
        response = self.client.post(self.action_url('edit'), {'email': 'updated@example.com', 'first_name': 'Updated', 'last_name': 'User', 'phone_number': '', 'role': self.role.pk, 'is_staff': 'on', 'is_superuser': 'on'})
        self.assertEqual(response.status_code, 302)
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.email, 'updated@example.com')
        self.assertFalse(self.patient.is_staff)
        self.assertFalse(self.patient.is_superuser)

    def test_delete_requires_post_and_retains_log(self):
        UserActivity.objects.create(actor=self.patient, actor_email=self.patient.email, action='Viewed page')
        self.client.get(self.action_url('delete'))
        self.assertTrue(CustomUser.objects.filter(pk=self.patient.pk).exists())
        self.client.post(self.action_url('delete'))
        self.assertFalse(CustomUser.objects.filter(pk=self.patient.pk).exists())
        event = UserActivity.objects.get(actor_email='patient@example.com', action='Viewed page')
        self.assertIsNone(event.actor)
        self.assertTrue(UserActivity.objects.filter(action='Deleted user', target_email='patient@example.com').exists())

    def test_privileged_accounts_are_protected(self):
        for action in ('edit', 'delete', 'decline', 'approve'):
            self.client.post(self.action_url(action, self.admin))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertTrue(self.admin.is_staff)

    def test_csrf_required_for_actions(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.action_url('delete')).status_code, 403)
        self.assertTrue(CustomUser.objects.filter(pk=self.patient.pk).exists())

    def test_audit_contains_no_private_request_data(self):
        self.client.get(reverse('profile'), {'password': 'private-secret', 'health': 'private-symptom'})
        event = UserActivity.objects.filter(route='profile').first()
        self.assertEqual(event.actor_email, self.admin.email)
        self.assertNotIn('private', str(event.__dict__))
        self.assertContains(self.client.get(reverse('activity_log')), 'Viewed page')

    def test_bulk_delete_selected_requires_confirmation(self):
        chosen = UserActivity.objects.create(actor=self.patient, actor_email=self.patient.email, action='Viewed page')
        kept = UserActivity.objects.create(actor=self.patient, actor_email=self.patient.email, action='Viewed page')
        url = reverse('user_management') + '?tab=logs'
        response = self.client.post(url, {'tab': 'logs', 'operation': 'selected', 'log_ids': [chosen.pk]})
        self.assertContains(response, 'Delete 1 user logs?')
        self.assertTrue(UserActivity.objects.filter(pk=chosen.pk).exists())
        token = response.context['confirmation']
        self.client.post(url, {'tab': 'logs', 'operation': 'confirm', 'confirmation': token})
        self.assertFalse(UserActivity.objects.filter(pk=chosen.pk).exists())
        self.assertTrue(UserActivity.objects.filter(pk=kept.pk).exists())
        self.assertTrue(UserActivity.objects.filter(action='Deleted 1 user logs').exists())

    def test_filtered_delete_respects_dates_users_and_snapshot(self):
        from datetime import datetime
        from django.utils import timezone
        chosen = UserActivity.objects.create(actor=self.patient, actor_email=self.patient.email, action='Viewed page')
        older = UserActivity.objects.create(actor=self.patient, actor_email=self.patient.email, action='Viewed page')
        UserActivity.objects.filter(pk=chosen.pk).update(created_at=timezone.make_aware(datetime(2026, 11, 9, 23, 59)))
        UserActivity.objects.filter(pk=older.pk).update(created_at=timezone.make_aware(datetime(2026, 11, 8, 23, 59)))
        url = reverse('user_management') + '?tab=logs'
        response = self.client.post(url, {'tab': 'logs', 'operation': 'filtered', 'user': 'patient@', 'start_date': '2026-11-09', 'end_date': '2026-11-09'})
        self.assertEqual(response.context['count'], 1)
        added_later = UserActivity.objects.create(actor=self.patient, actor_email=self.patient.email, action='Viewed page')
        UserActivity.objects.filter(pk=added_later.pk).update(created_at=timezone.make_aware(datetime(2026, 11, 9, 23, 59)))
        self.client.post(url, {'tab': 'logs', 'operation': 'confirm', 'confirmation': response.context['confirmation']})
        self.assertFalse(UserActivity.objects.filter(pk=chosen.pk).exists())
        self.assertTrue(UserActivity.objects.filter(pk=older.pk).exists())
        self.assertTrue(UserActivity.objects.filter(pk=added_later.pk).exists())

    def test_invalid_dates_and_confirmation_cannot_delete_logs(self):
        entry = UserActivity.objects.create(actor=self.patient, actor_email=self.patient.email, action='Viewed page')
        url = reverse('user_management') + '?tab=logs'
        response = self.client.post(url, {'tab': 'logs', 'operation': 'filtered', 'start_date': '2026-11-10', 'end_date': '2026-11-09'})
        self.assertContains(response, 'From date must be on or before To date.')
        self.client.post(url, {'tab': 'logs', 'operation': 'confirm', 'confirmation': 'tampered'})
        self.assertTrue(UserActivity.objects.filter(pk=entry.pk).exists())

    def test_bulk_delete_denied_to_patient(self):
        self.client.force_login(self.patient)
        self.assertEqual(self.client.post(reverse('user_management') + '?tab=logs', {'operation': 'filtered'}).status_code, 403)
