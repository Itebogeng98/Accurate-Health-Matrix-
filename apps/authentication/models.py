from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group, Permission, PermissionsMixin
from django.conf import settings
from django.db import models
from django.utils import timezone


DEFAULT_ROLE_NAMES = [
    'Admin',
    'Patient',
    'Health Professional',
]


class Role(models.Model):
    role = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.role


def ensure_default_roles():
    for role_name in DEFAULT_ROLE_NAMES:
        Role.objects.get_or_create(role=role_name)


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)

        if 'role' not in extra_fields and 'role_id' not in extra_fields:
            patient_role, _ = Role.objects.get_or_create(role='Patient')
            extra_fields['role'] = patient_role

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_approved', True)

        ensure_default_roles()

        if 'role' not in extra_fields and 'role_id' not in extra_fields:
            admin_role, _ = Role.objects.get_or_create(role='Admin')
            extra_fields['role'] = admin_role

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    phone_number = models.CharField(max_length=14, blank=True, null=True)
    join_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    reset_token = models.CharField(max_length=100, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        ordering = ['email']

    @property
    def can_manage_users(self):
        return self.is_active and (self.is_staff or self.is_superuser)

    def __str__(self):
        return self.email




ACTIVITY_PAGE_NAMES = {
    'home': 'Home', 'dashboard': 'Dashboard',
    'user_management': 'User Management', 'manage_user': 'Manage a user',
    'activity_log': 'User Activity Log', 'profile': 'My Profile',
    'register': 'Registration', 'signup_api': 'Registration',
    'login': 'Sign In', 'obtain_token': 'Sign In', 'logout': 'Sign Out',
    'stroke_predict': 'Stroke Health Check', 'stroke_prediction_api': 'Stroke Health Check',
    'lung_predict': 'Lung Health Check', 'lung_prediction_api': 'Lung Health Check',
    'prediction_report': 'Health Report', 'combined_report': 'Combined Health Report',
    'diet_home': 'Diet Guide', 'doctors': 'Doctors', 'exercises': 'Exercise Plan',
    'health_timeline': 'Health Timeline', 'daily_checkin': 'Daily Check-in',
    'personal_goals': 'Personal Goals', 'goal_progress': 'Goal Progress',
    'appointments': 'Appointments', 'notifications': 'Notifications',
    'dashboard_dataset': 'Dataset Details', 'data_tables': 'Health Datasets',
    'retrain_models_api': 'Update Prediction Models',
}


class UserActivity(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='activity_events')
    actor_email = models.EmailField()
    action = models.CharField(max_length=80)
    target_email = models.EmailField(blank=True)
    route = models.CharField(max_length=100, blank=True)
    method = models.CharField(max_length=10, blank=True)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    @property
    def page_label(self):
        return ACTIVITY_PAGE_NAMES.get(self.route, 'Other page' if self.route else 'Not recorded')

    @property
    def action_label(self):
        return {'Submitted request': 'Submitted a form', 'Authentication request failed': 'Sign-in attempt failed'}.get(self.action, self.action)

    @property
    def outcome_label(self):
        code = self.response_status
        if code is None:
            return 'Not recorded'
        if 200 <= code < 300:
            return 'Successful'
        if 300 <= code < 400:
            if self.action in ('Edited user', 'Approved user', 'Declined user', 'Deleted user', 'Signed in', 'Signed out'):
                return 'Successful'
            return 'Moved to another page'
        if code in (401, 403):
            return 'Access denied'
        if code == 404:
            return 'Page not found'
        if code == 400:
            return 'Please check the entered details'
        if code == 405:
            return 'Action not allowed'
        if code == 429:
            return 'Too many attempts - try again later'
        if code >= 500:
            return 'System problem - try again later'
        return 'Could not complete'

    def __str__(self):
        return f'{self.actor_email}: {self.action}'

