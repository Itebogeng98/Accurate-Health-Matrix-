"""Patient-owned wellness summaries; no medical scoring or inferred diagnoses."""
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone

from .models import PersonalGoal


def goal_cards(user, archived=False):
    today = timezone.localdate()
    goals = PersonalGoal.objects.filter(user=user, archived=archived).annotate(days_done=Count('progress'))
    checked_ids = set(user_goal_ids(user, today))
    cards = []
    for goal in goals:
        percent = min(100, round(goal.days_done / goal.target_days * 100))
        badge = ('Goal reached' if goal.days_done >= goal.target_days else
                 'Halfway there' if goal.days_done * 2 >= goal.target_days else
                 'First step' if goal.days_done else 'Ready to begin')
        cards.append({'goal': goal, 'percent': percent, 'checked_today': goal.pk in checked_ids,
                      'complete': goal.days_done >= goal.target_days, 'badge': badge})
    return cards


def user_goal_ids(user, date):
    return PersonalGoal.objects.filter(user=user, progress__date=date).values_list('pk', flat=True)


def wellness_summary(user):
    cards = goal_cards(user)
    next_goal = next((card for card in cards if not card['complete'] and not card['checked_today']), None)
    if next_goal:
        next_step = {'title': 'One small step is enough', 'text': next_goal['goal'].title,
                     'label': 'Open my goals', 'url': reverse('personal_goals')}
    elif not cards:
        next_step = {'title': 'Start with something small', 'text': 'Choose a personal habit and a pace that works for you.',
                     'label': 'Set a goal', 'url': reverse('personal_goals')}
    else:
        next_step = {'title': 'Every small step counts', 'text': 'Review your progress or choose your next personal goal.',
                     'label': 'View my goals', 'url': reverse('personal_goals')}
    return {'goal_count': len(cards), 'goals_reached': sum(card['complete'] for card in cards),
            'next_step': next_step}
