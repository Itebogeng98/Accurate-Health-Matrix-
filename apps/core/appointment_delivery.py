"""Persisted appointment delivery with duplicate-submission protection."""
from django.conf import settings
from django.utils import timezone

from .email_backend import EmailDeliveryUnknown
from .models import Appointment


def send_appointment_email(appointment):
    # Atomic claim prevents two requests from sending the same booking twice.
    claimed = Appointment.objects.filter(pk=appointment.pk, email_status__in=['not_sent', 'failed']).update(email_status='sending')
    if not claimed:
        appointment.refresh_from_db()
        return appointment.email_status
    try:
        from .report_pdf import build_screening_pdf
        if not appointment.report_id or appointment.report.user_id != appointment.user_id:
            raise ValueError('A report owned by the patient is required.')
        if settings.EMAIL_BACKEND.endswith(('console.EmailBackend', 'dummy.EmailBackend', 'filebased.EmailBackend')):
            raise ValueError('Configure an email delivery backend before sending appointment requests.')
        pdf = build_screening_pdf(appointment.report)
        from api.emails import build_appointment_email
        email = build_appointment_email(appointment, pdf)
        if email.send(fail_silently=False) != 1:
            raise RuntimeError('The email provider did not accept the message.')
    except EmailDeliveryUnknown:
        status = 'unknown'
    except Exception:
        # No patient data, provider response, or credentials should reach logs/UI.
        status = 'failed'
    else:
        status = 'accepted'
    Appointment.objects.filter(pk=appointment.pk).update(
        email_status=status, email_sent_at=timezone.now() if status == 'accepted' else None)
    appointment.refresh_from_db()
    return status
