"""Domain models retain their historical labels and table identities."""
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class PredictionRecord(models.Model):
    DISEASE_CHOICES = [
        ('stroke', 'Stroke'),
        ('lung_cancer', 'Lung Cancer'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    disease = models.CharField(max_length=30, choices=DISEASE_CHOICES)
    risk_level = models.CharField(max_length=20)
    probability = models.FloatField(default=0)
    input_data = models.JSONField(default=dict)
    recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'predictions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.disease} - {self.risk_level}'


class DoctorContact(models.Model):
    SPECIALTY_CHOICES = [
        ('neurologist', 'Neurologist / Stroke'),
        ('pulmonologist', 'Pulmonologist / Lung'),
        ('gp', 'General Practitioner'),
    ]

    name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=40, choices=SPECIALTY_CHOICES)
    province = models.CharField(max_length=80, default='Gauteng')
    city = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        app_label = 'wellness'
        ordering = ['specialty', 'name']

    def __str__(self):
        return f'{self.name} - {self.get_specialty_display()}'


class ExercisePlan(models.Model):
    RISK_CHOICES = [
        ('stroke', 'Stroke Risk'),
        ('lung_cancer', 'Lung Health'),
        ('general', 'General Wellness'),
    ]

    title = models.CharField(max_length=120)
    category = models.CharField(max_length=40, choices=RISK_CHOICES)
    difficulty = models.CharField(max_length=50, default='Beginner')
    duration = models.CharField(max_length=80, default='10-20 minutes')
    instructions = models.TextField()
    safety_note = models.TextField(blank=True)

    class Meta:
        app_label = 'wellness'
        ordering = ['category', 'title']

    def __str__(self):
        return self.title


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    reason = models.CharField(max_length=160)
    preferred_date = models.DateField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.reason}'


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DailyCheckIn(models.Model):
    MOOD_CHOICES = [('great', 'Great'), ('good', 'Good'), ('okay', 'Okay'),
                    ('low', 'Low'), ('difficult', 'Difficult')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    mood = models.CharField(max_length=12, choices=MOOD_CHOICES)
    sleep_hours = models.DecimalField(max_digits=3, decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(24)])
    activity_minutes = models.PositiveSmallIntegerField(validators=[MaxValueValidator(1440)])
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        constraints = [models.UniqueConstraint(fields=['user', 'date'], name='one_daily_checkin_per_user')]


class PersonalGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    target_days = models.PositiveSmallIntegerField(default=7,
        validators=[MinValueValidator(1), MaxValueValidator(365)])
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.CheckConstraint(condition=models.Q(target_days__gte=1, target_days__lte=365),
                                              name='goal_target_between_1_and_365')]


class GoalProgress(models.Model):
    goal = models.ForeignKey(PersonalGoal, on_delete=models.CASCADE, related_name='progress')
    date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        constraints = [models.UniqueConstraint(fields=['goal', 'date'], name='one_goal_tick_per_day')]
