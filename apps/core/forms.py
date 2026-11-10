from django import forms
from django.utils import timezone
import uuid
from .models import Appointment, DailyCheckIn, PersonalGoal, PredictionRecord
from .appointment_contacts import appointment_contacts


class DailyCheckInForm(forms.ModelForm):
    class Meta:
        model = DailyCheckIn
        fields = ['mood', 'sleep_hours', 'activity_minutes', 'note']
        labels = {'sleep_hours': 'Sleep last night (hours)',
                  'activity_minutes': 'Movement today (minutes)', 'note': 'A note for yourself (optional)'}
        widgets = {
            'sleep_hours': forms.NumberInput(attrs={'step': '0.5', 'min': 0, 'max': 24}),
            'activity_minutes': forms.NumberInput(attrs={'min': 0, 'max': 1440}),
            'note': forms.Textarea(attrs={'rows': 3, 'maxlength': 500,
                                         'placeholder': 'What went well? What would you like to remember?'}),
        }


class PersonalGoalForm(forms.ModelForm):
    class Meta:
        model = PersonalGoal
        fields = ['title', 'target_days']
        labels = {'title': 'What would you like to do?', 'target_days': 'Number of days to practise'}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Take a short walk or make time to unwind',
                                           'maxlength': 100}),
            'target_days': forms.NumberInput(attrs={'min': 1, 'max': 365}),
        }

class AppointmentForm(forms.ModelForm):
    doctor_email = forms.ChoiceField(label='Doctor / email contact', choices=(),
        help_text='Test contacts are for testing only. A listed email does not confirm appointment availability.')
    report = forms.ModelChoiceField(queryset=PredictionRecord.objects.none(),
        label='Screening report to attach', empty_label='Choose your report')
    share_report = forms.BooleanField(label='I agree to email my selected screening report and appointment details to this contact.')
    request_token = forms.UUIDField(widget=forms.HiddenInput, initial=uuid.uuid4)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.contacts = {contact['email']: contact for contact in appointment_contacts()}
        self.fields['doctor_email'].choices = [('', 'Select a doctor or test contact')] + [
            (email, f"{'TEST - ' if contact.get('is_test') else ''}{contact['name']} ({email})")
            for email, contact in self.contacts.items()
        ]
        if user is not None:
            self.fields['report'].queryset = PredictionRecord.objects.filter(user=user)
        self.fields['report'].label_from_instance = lambda record: (
            f"{record.get_disease_display()} - {timezone.localtime(record.created_at):%d %b %Y %H:%M} "
            f"- {record.probability_percent:.2f}% (report #{record.pk})"
        )
        self.order_fields(['doctor_email', 'report', 'reason', 'preferred_date', 'notes',
                           'share_report', 'request_token'])

    def clean_preferred_date(self):
        date = self.cleaned_data['preferred_date']
        if date < timezone.localdate():
            raise forms.ValidationError('Choose today or a future date.')
        return date

    class Meta:
        model = Appointment
        fields = ['reason', 'preferred_date', 'notes']
        widgets = {
            'reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Follow-up after a high risk result',
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Symptoms, questions, or anything the health professional should know',
            }),
        }


class StrokePredictionForm(forms.Form):
    gender = forms.ChoiceField(choices=[('Male','Male'),('Female','Female'),('Other','Other')])
    age = forms.FloatField(min_value=1, max_value=120)
    hypertension = forms.ChoiceField(choices=[(0,'No'),(1,'Yes')])
    heart_disease = forms.ChoiceField(choices=[(0,'No'),(1,'Yes')])
    ever_married = forms.ChoiceField(choices=[('Yes','Yes'),('No','No')])
    work_type = forms.ChoiceField(choices=[('Private','Private'),('Self-employed','Self-employed'),('Govt_job','Government Job'),('children','Children'),('Never_worked','Never Worked')])
    residence_type = forms.ChoiceField(choices=[('Urban','Urban'),('Rural','Rural')])
    avg_glucose_level = forms.FloatField(min_value=30, max_value=350)
    bmi = forms.FloatField(min_value=10, max_value=80)
    smoking_status = forms.ChoiceField(choices=[('formerly smoked','Formerly Smoked'),('never smoked','Never Smoked'),('smokes','Smokes'),('Unknown','Unknown')])


class LungCancerPredictionForm(forms.Form):
    gender = forms.ChoiceField(choices=[('M','Male'),('F','Female')])
    age = forms.IntegerField(min_value=1, max_value=120)
    smoking = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    yellow_fingers = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    anxiety = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    peer_pressure = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    chronic_disease = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    fatigue = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    allergy = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    wheezing = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    alcohol_consuming = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    coughing = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    shortness_of_breath = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    swallowing_difficulty = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
    chest_pain = forms.ChoiceField(choices=[(1,'No'),(2,'Yes')])
