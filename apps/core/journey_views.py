from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_http_methods

from .forms import DailyCheckInForm, PersonalGoalForm
from .journey import goal_cards
from .models import Appointment, DailyCheckIn, GoalProgress, PersonalGoal, PredictionRecord


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def daily_checkin(request):
    today = timezone.localdate()
    entry = DailyCheckIn.objects.filter(user=request.user, date=today).first()
    form = DailyCheckInForm(request.POST if request.method == 'POST' else None, instance=entry)
    if request.method == 'POST' and form.is_valid():
        DailyCheckIn.objects.update_or_create(user=request.user, date=today, defaults=form.cleaned_data)
        messages.success(request, 'Your check-in is saved. Every small step counts.')
        return redirect('daily_checkin')
    history = DailyCheckIn.objects.filter(user=request.user)
    total = history.count()
    return render(request, 'core/journey/checkin.html', {
        'form': form, 'today': today, 'entry': entry,
        'history': Paginator(history, 5).get_page(request.GET.get('page')),
        'total_checkins': total,
        'milestone': '30 check-ins' if total >= 30 else '7 check-ins' if total >= 7 else 'First check-in' if total else '',
    })


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def personal_goals(request):
    form = PersonalGoalForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        messages.success(request, 'Your goal is ready. Go at your own pace.')
        return redirect('personal_goals')
    archived = request.GET.get('archived') == '1'
    cards = goal_cards(request.user, archived=archived)
    return render(request, 'core/journey/goals.html', {
        'form': form, 'cards': Paginator(cards, 6).get_page(request.GET.get('page')),
        'archived': archived, 'today': timezone.localdate(),
        'completed_count': sum(card['complete'] for card in cards), 'goal_count': len(cards),
    })


@login_required
@require_POST
def goal_progress(request, goal_id):
    action = request.POST.get('action')
    if action not in ('complete', 'undo', 'archive', 'restore'):
        return HttpResponseBadRequest('Choose a valid goal action.')
    with transaction.atomic():
        goal = get_object_or_404(PersonalGoal.objects.select_for_update(), pk=goal_id, user=request.user)
        today = timezone.localdate()
        if action in ('archive', 'restore'):
            goal.archived = action == 'archive'
            goal.save(update_fields=['archived'])
        elif not goal.archived:
            if action == 'undo':
                GoalProgress.objects.filter(goal=goal, date=today).delete()
            elif goal.progress.count() < goal.target_days:
                GoalProgress.objects.get_or_create(goal=goal, date=today)
    messages.success(request, 'Goal updated.')
    return redirect('personal_goals')


@login_required
@never_cache
def health_timeline(request):
    selected = request.GET.get('kind', 'all')
    filters = [('all', 'Everything'), ('checks', 'Health checks'), ('checkins', 'Check-ins'),
               ('goals', 'Goals'), ('appointments', 'Appointments')]
    if selected not in dict(filters):
        selected = 'all'
    events = []
    def add(date, kind, title, detail, url, label):
        events.append({'date': date, 'kind': kind, 'title': title, 'detail': detail, 'url': url, 'label': label})
    if selected in ('all', 'checks'):
        for record in PredictionRecord.objects.filter(user=request.user):
            add(record.created_at, 'checks', record.get_disease_display() + ' check',
                record.risk_level + ' · Saved model result', reverse('prediction_report', args=[record.pk]), 'View report')
    if selected in ('all', 'checkins'):
        for entry in DailyCheckIn.objects.filter(user=request.user):
            date = timezone.make_aware(datetime.combine(entry.date, time.min))
            add(date, 'checkins', entry.get_mood_display() + ' · Daily check-in',
                f'{entry.sleep_hours} hours sleep · {entry.activity_minutes} minutes movement', reverse('daily_checkin'), 'My check-ins')
    if selected in ('all', 'goals'):
        for goal in PersonalGoal.objects.filter(user=request.user):
            add(goal.created_at, 'goals', 'Started: ' + goal.title,
                f'{goal.target_days} practice days' + (' · Archived' if goal.archived else ''), reverse('personal_goals'), 'My goals')
        for tick in GoalProgress.objects.filter(goal__user=request.user).select_related('goal'):
            add(tick.created_at, 'goals', 'A step towards: ' + tick.goal.title,
                'Personal goal progress recorded', reverse('personal_goals'), 'My goals')
    if selected in ('all', 'appointments'):
        for appointment in Appointment.objects.filter(user=request.user):
            add(appointment.created_at, 'appointments', appointment.reason,
                f'{appointment.preferred_date:%d %b %Y} · {appointment.get_status_display()}', reverse('appointments'), 'View appointments')
    events.sort(key=lambda event: event['date'], reverse=True)
    return render(request, 'core/journey/timeline.html', {
        'events': Paginator(events, 12).get_page(request.GET.get('page')),
        'filters': filters, 'selected': selected,
    })
