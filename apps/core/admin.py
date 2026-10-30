from django.contrib import admin
from .models import Appointment, Notification, PredictionRecord, DoctorContact, ExercisePlan

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'reason', 'preferred_date', 'status', 'created_at')
    list_filter = ('status', 'preferred_date')
    search_fields = ('user__email', 'reason', 'notes')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')


admin.site.register(PredictionRecord)


@admin.register(DoctorContact)
class DoctorContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'city', 'phone', 'email')
    search_fields = ('name', 'city', 'specialty')


@admin.register(ExercisePlan)
class ExercisePlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'duration')
    search_fields = ('title', 'category')
