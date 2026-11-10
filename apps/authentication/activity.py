"""Audit named application requests without recording request data or query strings."""
from .models import UserActivity


def record_activity(user, action, **details):
    return UserActivity.objects.create(actor=user, actor_email=user.email, action=action, **details)


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        before = request.user if request.user.is_authenticated else None
        response = self.get_response(request)
        user = request.user if request.user.is_authenticated else before
        match = getattr(request, 'resolver_match', None)
        if user and match and match.url_name and not match.app_name == 'admin':
            action = {'login': 'Signed in', 'obtain_token': 'Signed in', 'logout': 'Signed out'}.get(match.url_name)
            if action and response.status_code >= 400:
                action = 'Authentication request failed'
            if not action:
                action = 'Viewed page' if request.method == 'GET' else 'Submitted request'
            record_activity(user, action, route=match.url_name, method=request.method, response_status=response.status_code)
        return response
