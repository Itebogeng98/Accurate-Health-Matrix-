"""Django email backend using SendGrid's HTTPS Mail Send API."""
import base64
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend


class EmailDeliveryUnknown(Exception):
    """The provider may have accepted the email; do not automatically resend."""


class SendGridAPIBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not settings.SENDGRID_API_KEY:
            raise ImproperlyConfigured('SendGrid credentials are missing.')
        sent = 0
        for message in email_messages:
            name, sender = parseaddr(message.from_email)
            payload = {
                'personalizations': [{'to': [{'email': address} for address in message.to]}],
                'from': {'email': sender, 'name': name or 'Accurate HealthMatrix'},
                'subject': message.subject,
                'content': ([{'type': 'text/plain', 'value': message.body}] if message.body else [])
                           + [{'type': mimetype, 'value': content}
                              for content, mimetype in getattr(message, 'alternatives', [])],
                'tracking_settings': {'click_tracking': {'enable': False},
                                      'open_tracking': {'enable': False}},
            }
            if message.reply_to:
                payload['reply_to'] = {'email': parseaddr(message.reply_to[0])[1]}
            if message.attachments:
                payload['attachments'] = []
                for filename, content, mimetype in message.attachments:
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    payload['attachments'].append({
                        'filename': filename, 'type': mimetype, 'disposition': 'attachment',
                        'content': base64.b64encode(content).decode('ascii'),
                    })
            try:
                response = requests.post(
                    'https://api.sendgrid.com/v3/mail/send', json=payload,
                    headers={'Authorization': 'Bearer ' + settings.SENDGRID_API_KEY},
                    timeout=settings.EMAIL_TIMEOUT,
                )
            except requests.RequestException:
                # Never expose credentials, payloads, or patient details in errors.
                if self.fail_silently:
                    continue
                raise EmailDeliveryUnknown('Email delivery could not be confirmed.') from None
            if response.status_code != 202:
                if not self.fail_silently:
                    raise RuntimeError(f'SendGrid rejected the email (HTTP {response.status_code}).')
                continue
            sent += 1
        return sent
