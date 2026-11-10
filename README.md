# Health Risk Prediction and Diet Recommendation System

Accurate Health Matrix is designed to make it easier for people to access health-risk information, previous screening results, and useful wellness information in one place. The main users of the system are patients and administrators.


Django application for risk predictions, diet guidance, appointments and wellness support.

## Structure

```text
config/
  settings/{__init__,base,development,production}.py
  __init__.py, urls.py, wsgi.py, asgi.py, test_settings.py
apps/
  __init__.py
  authentication/
    __init__.py, apps.py, models.py, views.py, urls.py, admin.py, forms.py, serializers.py
    migrations/
  core/
    __init__.py, apps.py, models.py, views.py, urls.py, admin.py, forms.py, services.py
    wellness_data.py, tests/
    legacy/
      predictions/  # historical app label and migrations
      wellness/     # historical app label and migrations
      dashboard/migrations/       # original empty migration package
      recommendations/migrations/ # original empty migration package
static/
media/
templates/
  authentication/
  core/{dashboard,predictions,recommendations,wellness}/
  base/  # shared layout and home page
requirements/{base,development,production}.txt
.env, .env.example, .gitignore, manage.py
ml/, scripts/, datasets/, ml_models/, docs/, output/, tmp_pdf_text/
env/, db.sqlite3
```

The current repository directory is the project root; no additional nested `myproject` directory is needed. Authentication uses historical label `accounts`; `AUTH_USER_MODEL` remains `accounts.CustomUser`. Core models explicitly retain labels `accounts`, `predictions` and `wellness`, preserving tables, content types, permissions and relationships. Minimal historical app registrations are required for migration and admin identity. The original model tables and migration history remain unchanged. Personal wellness features add separate core tables through apps/core/migrations/0001_initial.py.

Normal settings retain the existing MySQL connection and `.env`. `db.sqlite3` is preserved and is not selected by normal settings. Tests use isolated in-memory SQLite. Source assets remain in `static/`; collectstatic writes to `staticfiles/`. Uploads use `media/`. No S3 configuration existed in the inspected source.

## Local commands (PowerShell)

```powershell
.\env\Scripts\Activate.ps1
python -m pip install -r requirements/development.txt
python manage.py check --settings=config.settings.development
python manage.py migrate --plan --settings=config.settings.development
python manage.py migrate --settings=config.settings.development
python manage.py runserver --settings=config.settings.development
```

Open http://127.0.0.1:8000/. Existing migrations are already applied in this installation. Do not overwrite the existing `.env`. On a new installation only, create a virtual environment, copy `.env.example` to `.env`, and supply real credentials.

If a prediction reports `No module named 'sklearn'`, the Python environment running Django is missing scikit-learn. Use this project's environment explicitly so an environment activated for another project is not used:

```powershell
.\env\Scripts\python.exe -m pip install -r requirements/development.txt
.\env\Scripts\python.exe manage.py runserver --settings=config.settings.development
```

The committed model artifacts were trained with scikit-learn 1.9.0; the requirements pin that version for compatible loading. Restart the server after installing dependencies.

## Deployment commands (PowerShell)

Configure the deployment environment with a strong `SECRET_KEY`, the existing database credentials, and `ALLOWED_HOSTS` containing your real domain. Use HTTPS. Preserve the current environment file locally; supply production secrets through the host environment.

```powershell
.\env\Scripts\Activate.ps1
$env:DJANGO_SETTINGS_MODULE = 'config.settings.production'
$env:ALLOWED_HOSTS = 'your-real-domain.example'
python -m pip install -r requirements/production.txt
python manage.py check --deploy
python manage.py migrate --plan
python manage.py migrate
python manage.py collectstatic --noinput
```

Configure your host's WSGI server with `config.wsgi:application`, or its ASGI server with `config.asgi:application`, then restart that server through the host's service manager. Both entrypoints default to production settings. Serve `staticfiles/` at `/static/` and uploaded `media/` at `/media/`. The repository contains no production server package or host/service configuration, so a host-specific launch/restart command cannot be determined without choosing a deployment platform. No server package was added during restructuring.

## Validation

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations --plan
python manage.py test apps.core.tests --settings=config.test_settings --noinput
python scripts/verify_restructuring.py
```

The verifier compares database rows against the existing captured baseline without printing rows or credentials. Legitimate subsequent database changes may differ from that baseline.

## Datasets, model training and food guide

The requested Kaggle datasets are installed locally:

- `datasets/healthcare-dataset-stroke-data.csv`: 5,110 stroke records.
- `datasets/lung cancer.csv`: 309 survey records, downloaded from Kaggle's `survey lung cancer.csv`.
- `datasets/food_nutrition.csv`: 8,789 food nutrition records, downloaded from Kaggle's `nutrition.csv`.

Source links, original filenames, row counts and SHA-256 fingerprints are recorded in `datasets/manifest.json`. Downloading reads the existing Kaggle credentials from `.env`; secrets are never written to the manifest. The CSV bytes are preserved, including original column headings. Training normalizes headings to the form field names and removes duplicate feature/target rows before the split.

```powershell
python scripts/download_datasets.py
python scripts/train_models.py
```

The downloader skips existing CSVs. Use `python scripts/download_datasets.py --force` only when you intend to replace them with the current Kaggle download. No Kaggle package is required. Training writes `ml_models/stroke_model.pkl`, `ml_models/lung_cancer_model.pkl` and metrics JSON beside each artifact. The application loads those artifacts automatically; the admin retraining endpoint uses the same training functions.

The dashboard previews all three local datasets. At `/diet/`, search the nutrition reference by food name. Diet suggestions and prediction results include reference calories, protein, fibre and sodium with the preparation and serving basis from the CSV. Nutrition is a reference lookup, not a trained medical recommendation model. If the food CSV is absent, existing food suggestions remain available without nutrient values.

The model scores are uncalibrated educational outputs. On this dataset holdout, stroke positive recall is only 12%, despite 93.5% accuracy; it is unsuitable for clinical decisions. Lung positive recall is 95.8% on a small 56-row holdout. These are internal holdout results, not external validation. See [dataset integration details](docs/DATASET_INTEGRATION.md).

Older assignment documents and diagram artifacts describe the historical structure and are retained as submitted evidence. See [the restructuring report](docs/LAYOUT_RESTRUCTURING_REPORT.md) for the previous layout changes.


## Personal wellness journey

The patient sidebar includes Personal goals. Health timeline and Daily check-in have been removed from the sidebar and dashboard; their saved data and existing direct routes are retained.

- Health timeline combines the current patient's saved predictions, check-ins, goal activity, and appointment requests. Category filters and 12-event pages keep it compact. Appointment statuses show their current state rather than a separate status-change history.
- Daily check-in saves mood, sleep hours, movement minutes, and an optional personal note. There is one editable entry per patient per local calendar day (Africa/Johannesburg), with paginated history and gentle milestones.
- Personal goals use a user-chosen habit and target of 1 to 365 practice days. A goal can receive one tick per local day; today's tick can be undone. Days need not be consecutive. Goals can be archived and restored, and milestone badges reflect recorded practice days.
- The dashboard suggests a goal-based next step. These are personal activity summaries, not clinical health scores.

For another installation, apply the additive migration before starting the updated app:

```powershell
.\env\Scripts\python.exe manage.py migrate core
```

The new models are DailyCheckIn, PersonalGoal, and GoalProgress under the core app label. Existing prediction, appointment, and authentication tables are preserved. No new packages or external services are required.

```powershell
.\env\Scripts\python.exe manage.py test apps.core.tests --settings=config.test_settings --noinput
```


## Appointment requests with emailed PDF reports

After a stroke or lung screening, select **Book an appointment**. The same action is available on saved reports and dashboard report rows. Choose a listed contact email, select your saved report, choose a preferred date, and agree to share the report. The request email attaches a branded PDF with the screening inputs, percentage score, saved guidance, logo, and academic disclaimer. Replies go to the patient's account email.

Only contacts with an email are offered. The two developer addresses are explicitly marked as test contacts; they are not clinical services. Directory listings do not provide live calendar availability. A request stays pending until the contact confirms arrangements directly.

For another installation:

```powershell
.\env\Scripts\python.exe -m pip install -r requirements/base.txt
.\env\Scripts\python.exe manage.py migrate accounts
```

Configure `SENDGRID_API_KEY` and a SendGrid-verified `DEFAULT_FROM_EMAIL` in `.env`. Set `EMAIL_BACKEND=apps.core.email_backend.SendGridAPIBackend`. Legacy `summit.email_backend.SendGridAPIBackend` settings and SendGrid SMTP settings are mapped to this project's HTTPS backend when credentials exist. Credentials are never embedded in source. Appointment sending is synchronous so acceptance or failure can be shown accurately.

The history distinguishes provider acceptance from confirmed booking. Failed sends can be retried without creating a second booking. Timeouts or interrupted sends remain unconfirmed and are not automatically resent. Duplicate submission tokens prevent repeat sends. Report downloads and attachments are restricted to the signed-in patient's records.

```powershell
.\env\Scripts\python.exe manage.py test apps.core.tests.test_appointments apps.core.tests.test_regression apps.core.tests.test_doctor_support --settings=config.test_settings --noinput
```
