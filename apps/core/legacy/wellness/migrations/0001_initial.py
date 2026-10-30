# Generated manually for Health AI website
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='DoctorContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('specialty', models.CharField(choices=[('neurologist', 'Neurologist / Stroke'), ('pulmonologist', 'Pulmonologist / Lung'), ('gp', 'General Practitioner')], max_length=40)),
                ('province', models.CharField(default='Gauteng', max_length=80)),
                ('city', models.CharField(blank=True, max_length=80)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('phone', models.CharField(blank=True, max_length=80)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('website', models.URLField(blank=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={'ordering': ['specialty', 'name']},
        ),
        migrations.CreateModel(
            name='ExercisePlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('category', models.CharField(choices=[('stroke', 'Stroke Risk'), ('lung_cancer', 'Lung Health'), ('general', 'General Wellness')], max_length=40)),
                ('difficulty', models.CharField(default='Beginner', max_length=50)),
                ('duration', models.CharField(default='10-20 minutes', max_length=80)),
                ('instructions', models.TextField()),
                ('safety_note', models.TextField(blank=True)),
            ],
            options={'ordering': ['category', 'title']},
        ),
    ]
