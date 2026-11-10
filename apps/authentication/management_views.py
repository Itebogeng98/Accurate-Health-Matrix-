from functools import wraps
from datetime import datetime, time, timedelta
from urllib.parse import urlencode

from django.core import signing
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from rest_framework.authtoken.models import Token

from .activity import record_activity
from .forms import ManagedUserForm, ActivityFilterForm
from .models import ACTIVITY_PAGE_NAMES, CustomUser, UserActivity


def manager_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.can_manage_users:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


@manager_required
def user_management(request):
    if request.GET.get('tab') == 'logs' or request.POST.get('tab') == 'logs':
        return activity_log(request)
    users = CustomUser.objects.select_related('role').order_by('-join_date', '-pk')
    query = request.GET.get('q', '').strip()[:100]
    state = request.GET.get('status', 'all')
    if query:
        users = users.filter(Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
    if state == 'pending':
        users = users.filter(is_active=True, is_approved=False)
    elif state == 'approved':
        users = users.filter(is_active=True, is_approved=True)
    elif state == 'declined':
        users = users.filter(is_active=False)
    return render(request, 'authentication/user_management.html', {
        'page': Paginator(users, 20).get_page(request.GET.get('page')), 'query': query, 'state': state,
    })


@manager_required
@require_http_methods(['GET', 'POST'])
def manage_user(request, user_id, action):
    if action not in ('edit', 'approve', 'decline', 'delete'):
        raise PermissionDenied
    target = get_object_or_404(CustomUser, pk=user_id)
    # Prevent self lockout and changes to privileged accounts from this interface.
    if target.pk == request.user.pk or target.is_staff or target.is_superuser:
        messages.error(request, 'Administrator accounts are protected here. Use Django admin for administrator changes.')
        return redirect('user_management')
    form = ManagedUserForm(request.POST or None, instance=target) if action == 'edit' else None
    if request.method == 'POST' and (form is None or form.is_valid()):
        with transaction.atomic():
            target = CustomUser.objects.select_for_update().get(pk=user_id)
            if target.is_staff or target.is_superuser:
                raise PermissionDenied
            email = target.email
            if action == 'edit':
                for name, value in form.cleaned_data.items():
                    setattr(target, name, value)
                target.save()
            elif action == 'delete':
                target.delete()
            else:
                target.is_approved = action == 'approve'
                target.is_active = action == 'approve'
                target.save(update_fields=['is_approved', 'is_active'])
                if action == 'decline':
                    Token.objects.filter(user=target).delete()
            record_activity(request.user, {'edit': 'Edited user', 'approve': 'Approved user', 'decline': 'Declined user', 'delete': 'Deleted user'}[action], target_email=email, route='manage_user', method='POST', response_status=302)
        messages.success(request, f'User {action} completed for {email}.')
        return redirect('user_management')
    return render(request, 'authentication/manage_user.html', {'target': target, 'action': action, 'form': form})



def filtered_activity(data):
    entries = UserActivity.objects.all()
    query = data.get('q', '')
    if query:
        entries = entries.filter(Q(actor_email__icontains=query) | Q(target_email__icontains=query) | Q(action__icontains=query) | Q(route__icontains=query) | Q(route__in=[key for key, label in ACTIVITY_PAGE_NAMES.items() if query.lower() in label.lower()]))
    user = data.get('user', '')
    if user:
        entries = entries.filter(Q(actor_email__icontains=user) | Q(actor__first_name__icontains=user) | Q(actor__last_name__icontains=user))
    if data.get('start_date'):
        entries = entries.filter(created_at__gte=timezone.make_aware(datetime.combine(data['start_date'], time.min)))
    if data.get('end_date'):
        entries = entries.filter(created_at__lt=timezone.make_aware(datetime.combine(data['end_date'] + timedelta(days=1), time.min)))
    return entries


@manager_required
@require_http_methods(['GET', 'POST'])
def activity_log(request):
    filter_data = request.POST if request.method == 'POST' else request.GET
    form = ActivityFilterForm(filter_data)
    valid = form.is_valid()
    cleaned = form.cleaned_data if valid else {}
    entries = filtered_activity(cleaned) if valid else UserActivity.objects.none()
    params = {key: value.isoformat() if hasattr(value, 'isoformat') else value for key, value in cleaned.items() if value}
    return_url = reverse('user_management') + '?' + urlencode({'tab': 'logs', **params})
    if request.method == 'POST' and request.POST.get('operation') == 'confirm':
        try:
            payload = signing.loads(request.POST.get('confirmation', ''), salt='bulk-delete-user-logs', max_age=900)
            if payload['administrator'] != request.user.pk:
                raise signing.BadSignature
            snapshot_form = ActivityFilterForm(payload['filters'])
            if not snapshot_form.is_valid():
                raise signing.BadSignature
            selected = filtered_activity(snapshot_form.cleaned_data).filter(pk__lte=payload['latest_id'])
            if payload['ids'] is not None:
                selected = selected.filter(pk__in=payload['ids'])
            with transaction.atomic():
                count = selected.count()
                selected.delete()
                record_activity(request.user, f'Deleted {count} user logs', route='activity_log', method='POST', response_status=302)
            messages.success(request, f'{count} user logs deleted.')
            return redirect(reverse('user_management') + '?' + urlencode({'tab': 'logs', **payload['filters']}))
        except (signing.BadSignature, KeyError, TypeError, ValueError):
            messages.error(request, 'This confirmation has expired or is invalid. Select the logs again.')
            return redirect('user_management')
    if request.method == 'POST' and valid:
        mode = request.POST.get('operation')
        ids = None
        if mode == 'selected':
            try:
                ids = [int(value) for value in request.POST.getlist('log_ids')]
            except ValueError:
                ids = []
            entries = entries.filter(pk__in=ids)
        elif mode != 'filtered':
            messages.error(request, 'Choose the logs you want to delete.')
            return redirect(return_url)
        latest_id = entries.order_by('-pk').values_list('pk', flat=True).first() or 0
        count = entries.filter(pk__lte=latest_id).count()
        if not count:
            messages.warning(request, 'No logs selected. Tick some logs or adjust your filters.')
            return redirect(return_url)
        confirmation = signing.dumps({'administrator': request.user.pk, 'filters': params, 'ids': ids, 'latest_id': latest_id}, salt='bulk-delete-user-logs', compress=True)
        return render(request, 'authentication/delete_logs.html', {'count': count, 'confirmation': confirmation, 'return_url': return_url, 'active_tab': 'logs'})
    return render(request, 'authentication/activity_log.html', {
        'page': Paginator(entries, 30).get_page(request.GET.get('page')), 'query': cleaned.get('q', ''),
        'active_tab': 'logs', 'filter_form': form, 'filter_values': params,
    })
