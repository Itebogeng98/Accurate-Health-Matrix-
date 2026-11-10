import logging

from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def send_welcome_email(to_email, subject, content):
    """Send HTML email through the configured Django email backend."""
    email = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=None,
        to=[to_email],
    )
    email.attach_alternative(content, "text/html")
    try:
        return email.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send welcome email to %s", to_email)
        return None



def build_appointment_email(appointment, pdf):
    """Build the patient's appointment request with their selected PDF attached."""
    from django.conf import settings
    from django.core.mail import EmailMessage
    patient = (' '.join(filter(None, [appointment.user.first_name, appointment.user.last_name])) or appointment.user.email)
    body = (
        f'Dear {appointment.doctor_name},\n\n'
        f'{patient} is requesting an appointment following an AHM screening.\n\n'
        f'Patient: {patient}\nPatient email: {appointment.user.email}\n'
        f'Preferred date: {appointment.preferred_date:%d %B %Y}\n'
        f'Reason: {appointment.reason}\nNotes: {appointment.notes or "None provided"}\n\n'
        f'The patient has agreed to share the attached report #{appointment.report_id}.\n'
        'Please reply to the patient to confirm availability and arrangements. '
        'This is an appointment request, not a confirmed booking.\n\n'
        'Academic Website\nUse results for learning and wellness support, not medical diagnosis.\n'
        'Model scores are not clinically validated probabilities. '
        'Discuss health concerns with a qualified healthcare professional.\n\n'
        f'Accurate HealthMatrix | Request #{appointment.pk}'
    )
    email = EmailMessage(
        subject=f'AHM appointment request #{appointment.pk} - {appointment.preferred_date:%d %b %Y}',
        body=body, from_email=settings.DEFAULT_FROM_EMAIL, to=[appointment.doctor_email],
        reply_to=[appointment.user.email],
    )
    email.attach(f'AHM-screening-report-{appointment.report_id}.pdf', pdf, 'application/pdf')
    return email
