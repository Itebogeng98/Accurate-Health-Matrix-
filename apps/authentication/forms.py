from django import forms
from .models import CustomUser


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }




class ManagedUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Administrator privileges are managed through Django admin, not roles.
        self.fields['role'].queryset = self.fields['role'].queryset.exclude(role__iexact='Admin')
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ActivityFilterForm(forms.Form):
    q = forms.CharField(required=False, max_length=100, label='Search activity')
    user = forms.CharField(required=False, max_length=254, label='User name or email')
    start_date = forms.DateField(required=False, label='From date', widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, label='To date', widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
        data = super().clean()
        if data.get('start_date') and data.get('end_date') and data['start_date'] > data['end_date']:
            raise forms.ValidationError('From date must be on or before To date.')
        return data
