import base64
import uuid
from datetime import timedelta
from unittest.mock import patch, Mock

import requests
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import EmailMessage
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.email_backend import SendGridAPIBackend, EmailDeliveryUnknown
from apps.core.models import Appointment, PredictionRecord


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AppointmentBookingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='patient@example.com', password='test-pass',
            first_name='Test', last_name='Patient', is_approved=True)
        self.other = get_user_model().objects.create_user(email='other@example.com', password='test-pass')
        self.record = PredictionRecord.objects.create(user=self.user, disease='stroke',
            risk_level='Medium Risk', probability=.43, input_data={'age': 54, 'hypertension': '1'},
            recommendation='Discuss the results with a professional.')
        self.private = PredictionRecord.objects.create(user=self.other, disease='lung_cancer', probability=.7)
        self.client.force_login(self.user)
        self.payload = {
            'doctor_email': 'ie.sebapu@gmail.com', 'report': self.record.pk,
            'reason': 'Screening follow-up', 'preferred_date': str(timezone.localdate()+timedelta(days=1)),
            'notes': 'Please confirm availability.', 'share_report': 'on', 'request_token': str(uuid.uuid4()),
        }

    def test_booking_emails_selected_contact_with_pdf_and_patient_reply_to(self):
        response = self.client.post(reverse('appointments'), self.payload)
        self.assertRedirects(response, reverse('appointments'))
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.email_status, 'accepted')
        self.assertEqual(appointment.status, 'pending')
        self.assertEqual(appointment.report, self.record)
        self.assertIsNotNone(appointment.email_sent_at)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['ie.sebapu@gmail.com'])
        self.assertEqual(email.reply_to, [self.user.email])
        self.assertIn('Use results for learning and wellness support, not medical diagnosis.', email.body)
        filename, content, content_type = email.attachments[0]
        self.assertEqual(filename, f'AHM-screening-report-{self.record.pk}.pdf')
        self.assertEqual(content_type, 'application/pdf')
        self.assertTrue(content.startswith(b'%PDF-'))
        self.assertGreater(len(content), 4000)

    def test_duplicate_submission_does_not_resend_or_create_second_booking(self):
        self.client.post(reverse('appointments'), self.payload)
        self.client.post(reverse('appointments'), self.payload)
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_report_ownership_and_explicit_sharing_are_required(self):
        for changes in [{'report': self.private.pk}, {'share_report': ''},
                        {'doctor_email': 'unlisted@example.com'},
                        {'preferred_date': str(timezone.localdate()-timedelta(days=1))}]:
            with self.subTest(changes=changes):
                response = self.client.post(reverse('appointments'), {**self.payload, **changes})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
        self.assertFalse(Appointment.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_selected_report_and_available_email_contacts(self):
        response = self.client.get(reverse('appointments'), {'report': self.record.pk})
        self.assertEqual(response.context['form'].initial['report'], self.record)
        self.assertContains(response, 'ie.sebapu@gmail.com')
        self.assertContains(response, 'itebogengeugene@gmail.com')
        self.assertContains(response, 'TEST - ')
        self.assertEqual(self.client.get(reverse('appointments'), {'report': self.private.pk}).status_code, 404)
        self.assertEqual(self.client.get(reverse('appointments'), {'report': 'invalid'}).status_code, 404)
        self.assertContains(self.client.get(reverse('doctors')), 'ie.sebapu@gmail.com')

    def test_failure_is_saved_and_explicit_retry_reuses_booking(self):
        with patch('django.core.mail.EmailMessage.send', side_effect=RuntimeError('rejected')):
            self.client.post(reverse('appointments'), self.payload)
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.email_status, 'failed')
        self.client.post(reverse('appointments'), {'retry_appointment': appointment.pk})
        appointment.refresh_from_db()
        self.assertEqual(appointment.email_status, 'accepted')
        self.client.post(reverse('appointments'), {'retry_appointment': appointment.pk})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_unknown_delivery_does_not_automatically_resend(self):
        with patch('django.core.mail.EmailMessage.send', side_effect=EmailDeliveryUnknown):
            self.client.post(reverse('appointments'), self.payload)
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.email_status, 'unknown')
        self.client.post(reverse('appointments'), {'retry_appointment': appointment.pk})
        self.assertEqual(len(mail.outbox), 0)

    def test_patient_cannot_retry_another_patients_booking(self):
        appointment = Appointment.objects.create(user=self.other, preferred_date=timezone.localdate(),
            reason='Private request', email_status='failed')
        self.assertEqual(self.client.post(reverse('appointments'), {'retry_appointment': appointment.pk}).status_code, 404)

    def test_pdf_download_is_owned_and_private(self):
        url = reverse('prediction_report_pdf', args=[self.record.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF-'))
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.client.get(reverse('prediction_report_pdf', args=[self.private.pk])).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)


@override_settings(SENDGRID_API_KEY='test-key', EMAIL_TIMEOUT=5)
class SendGridBackendTests(SimpleTestCase):
    def test_sendgrid_receives_base64_pdf_attachment_and_reply_to(self):
        message = EmailMessage('Appointment request', 'Academic Website', 'sender@example.com',
                               ['doctor@example.com'], reply_to=['patient@example.com'])
        message.attach('report.pdf', b'%PDF-test', 'application/pdf')
        with patch('apps.core.email_backend.requests.post', return_value=Mock(status_code=202)) as post:
            self.assertEqual(SendGridAPIBackend().send_messages([message]), 1)
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['reply_to']['email'], 'patient@example.com')
        self.assertEqual(base64.b64decode(payload['attachments'][0]['content']), b'%PDF-test')
        self.assertEqual(payload['personalizations'][0]['to'], [{'email': 'doctor@example.com'}])

    def test_rejection_and_timeout_are_not_reported_as_success(self):
        message = EmailMessage('Test', 'Body', 'sender@example.com', ['doctor@example.com'])
        with patch('apps.core.email_backend.requests.post', return_value=Mock(status_code=403)):
            with self.assertRaises(RuntimeError):
                SendGridAPIBackend().send_messages([message])
        with patch('apps.core.email_backend.requests.post', side_effect=requests.Timeout):
            with self.assertRaises(EmailDeliveryUnknown):
                SendGridAPIBackend().send_messages([message])

    def test_existing_html_email_helper_preserves_html_content(self):
        from api.emails import send_welcome_email
        with override_settings(EMAIL_BACKEND='apps.core.email_backend.SendGridAPIBackend'):
            with patch('apps.core.email_backend.requests.post', return_value=Mock(status_code=202)) as post:
                self.assertEqual(send_welcome_email('test@example.com', 'Welcome', '<p>Welcome to AHM</p>'), 1)
        self.assertEqual(post.call_args.kwargs['json']['content'],
                         [{'type': 'text/html', 'value': '<p>Welcome to AHM</p>'}])
