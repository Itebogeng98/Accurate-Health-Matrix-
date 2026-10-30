# Project restructuring report

## Outcome

The existing project now has one canonical application implementation in `health_ai`, separate configuration in `config`, and ML inference/recommendation code in `ml`. Five installed local apps became three: the main app (historical label `accounts`) plus the minimal `predictions` and `wellness` migration apps. No application feature, route, template, stylesheet or database record was removed.

## Old structure

```text
manage.py
health_ai/       settings.py, urls.py, asgi.py, wsgi.py (project package)
accounts/        all concrete models, auth forms/views/admin/URLs, api/, migrations/
dashboard/       dashboard/dataset/appointment/notification views, forms, URLs
predictions/     forms, views, URLs, admin, ml_utils, model exports, api/, migrations/
recommendations/ diet engine, view, URLs, empty model scaffolding
wellness/        views, URLs, admin, model exports, static data, migrations/
templates/       base/, accounts/, dashboard/, predictions/, recommendations/, wellness/
static/css/style.css
scripts/train_models.py
datasets/, ml_models/, env/, output/, tmp_pdf_text/
.env, db.sqlite3, requirements.txt, README.md, AHM_Assignment_2_Submission.docx
```

## New structure

```text
config/
  settings.py, urls.py, asgi.py, wsgi.py, test_settings.py
health_ai/
  apps.py        canonical app, label remains accounts
  models.py      seven database model definitions
  forms.py       four form classes
  admin.py       all seven model registrations
  serializers.py three serializer classes
  views.py       browser/API handlers grouped by feature
  urls.py        all 20 application routes, plus legacy URL adapter
  services.py    dataset previews, patient context, prediction persistence
  wellness_data.py
  tests/test_regression.py
  settings.py, asgi.py, wsgi.py  compatibility entrypoints
ml/
  model_loader.py, preprocessing.py, prediction.py, recommendation.py
accounts/
  migrations/    unchanged
  models.py      compatibility exports
  other modules  small wrappers and retained scaffolding/helpers
predictions/, wellness/
  apps.py, models.py, migrations/  preserved migration app identities
  other modules  compatibility wrappers
 dashboard/, recommendations/    uninstalled, compatibility modules/scaffolding retained
templates/, static/, datasets/, ml_models/  unchanged
scripts/
  train_models.py                unchanged
  verify_restructuring.py        read-only baseline verifier
docs/
  PROJECT_RESTRUCTURING_PLAN.md, PROJECT_RESTRUCTURING_REPORT.md
  original_source.zip, original_file_hashes.json
  restructuring_baseline.json, restructuring_file_manifest.json
.env                           unchanged
.env.example                   placeholders only
README.md                      corrected setup and architecture documentation
```

## Code relocation and imports

No physical file rename/deletion was needed: implementations were relocated and old import paths were retained as wrappers.

| Original implementation | Canonical location |
| --- | --- |
| health_ai settings, ASGI, WSGI, MySQL adapter | config/ |
| accounts/models.py | health_ai/models.py |
| accounts, dashboard and predictions forms | health_ai/forms.py |
| accounts, predictions and wellness admin | health_ai/admin.py |
| accounts/api/serializers.py | health_ai/serializers.py |
| all five feature views and both API views | health_ai/views.py |
| root and seven feature/API URLconfs | config/urls.py and health_ai/urls.py |
| dashboard dataset/patient helpers and predictions persistence helper | health_ai/services.py |
| predictions/ml_utils.py model loading | ml/model_loader.py |
| predictions/ml_utils.py pipeline input adapter | ml/preprocessing.py |
| predictions/ml_utils.py scoring/inference | ml/prediction.py |
| recommendations/engine.py | ml/recommendation.py |
| wellness/data.py | health_ai/wellness_data.py |

Canonical code imports models/forms/serializers/services from health_ai and ML functions from ml. Legacy modules forward to those same objects. The API no longer imports prediction persistence from a browser view module. Local and downloaded CSV previews share their row-count/preview loop. No unnecessary utils module or additional feature app was introduced.

## Models and migration safety

Consolidated Role, CustomUser, Appointment, Notification, PredictionRecord, DoctorContact and ExercisePlan into health_ai/models.py. CustomUserManager and ensure_default_roles also moved, with compatibility exports retained.

- AUTH_USER_MODEL remains `accounts.CustomUser`.
- AppConfig.name is `health_ai`, AppConfig.label is `accounts`.
- MIGRATION_MODULES maps `accounts` to `accounts.migrations`.
- PredictionRecord retains label `predictions`; DoctorContact and ExercisePlan retain label `wellness`.
- All table names, fields, relationships, M2M tables, content types, permissions and model identities remain unchanged.
- All eight numbered project migrations and all migration package initializers are unchanged.
- No new migrations were generated. No migrate, fake, reset or schema-edit command was run against the existing database.
- Combining all three database labels was deliberately avoided because it would affect the custom user, historical migrations, foreign keys, content types and permissions.

## Views, routes, authentication and UI

All 20 request handlers (15 browser handlers and five API endpoints) are implemented in health_ai/views.py. Authentication, dashboard, health data, predictions, recommendations and wellness are grouped with section comments. Browser login/signup retain their existing HTTP calls to the local API, approval behavior, session handling and messages. Retraining keeps its admin permission check.

All 20 application URL paths/names and the full admin URL tree match the inspection baseline. Legacy feature URLconfs derive routes from the canonical list instead of duplicating definitions. Existing template URL names and feature template folders remain unchanged. Templates and CSS are byte-identical; page-rendering tests pass. No visual redesign was attempted.

## Validation evidence

Commands ran with `env/Scripts/python.exe` because system Python has no Django:

- `manage.py check`: no issues, both before and after restructuring and at intermediate checkpoints.
- `manage.py makemigrations --check`: no changes detected.
- `manage.py showmigrations`: all existing migrations remain applied; uninstalled model-free apps no longer appear.
- `manage.py test health_ai.tests --settings=config.test_settings --noinput`: **16 tests passed**.
- `scripts/verify_restructuring.py`: **all 20 active MySQL tables match original row counts and content hashes; all 34 protected files are byte-identical**.
- Protected files include `.env`, `db.sqlite3`, requirements, training script, every migration file, every template and CSS.
- `git status`, `git diff`, and final `git diff --stat` were attempted: unavailable because the supplied `.git` directory is empty. File hashes, source ZIP and the generated manifest provide an alternative audit trail.

Regression coverage includes exact route/name and model/field/table comparison; legacy imports and URLconfs; signup/password storage and approval gating; API/browser login/logout; authenticated pages and dataset pages; profile changes; appointment creation; per-user notifications; both browser/API predictions; invalid input; database-error fallback; admin and retraining permissions; fallback risk thresholds; pipeline DataFrame input and model loading; and CSV preview behavior.

Tests created and destroyed only a separate in-memory SQLite database. They did not modify the existing MySQL database or db.sqlite3. Historical MySQL-specific repair migrations were preserved, not replayed by tests. No CSVs or trained artifacts were supplied, so real model training/accuracy and real artifact inference could not be validated; fallback scoring and pipeline interfaces were tested. External Kaggle traffic and live browser-to-API HTTP transport were mocked/not exercised.

## Deliberately retained and cleanup limits

Automatic approval review rejected the broad source-file deletion command due to irreversible-damage risk. The safe alternative retains old paths as small compatibility modules; no deletion command succeeded. There is one implementation of each model/form/handler/admin registration, despite the retained legacy filenames. Old AppConfig and empty model/admin scaffolding in uninstalled apps are retained.

Also retained: unused `accounts/api/authentication.py` and `accounts/api/email.py` (no internal callers found), all caches and empty directories, both assignment DOCX files, `output/`, and `tmp_pdf_text/`. Their ownership or future use is uncertain. No templates or URLs were found to be unused; predictions/result.html is included by both prediction pages. The template navigation duplication remains to avoid unnecessary UI work. Existing wellness data-map text and all existing security/authentication policies were kept outside this structural change.

## Manual steps

No migration or data restoration is required. Restart the development server using the existing virtual environment and existing .env. Existing WSGI/ASGI/settings import paths still work; use config entrypoints for new deployment configuration. Use the documented isolated-test command. Restore/connect the real Git metadata separately if Git history is needed; it was not initialized or changed here.

Datasets and trained models remain optional as before. Download the expected CSVs and run scripts/train_models.py only if actual model training is desired. Do not overwrite the existing .env with the example.

The baseline verifier is a point-in-time audit: legitimate later user activity will change database hashes. The source ZIP excludes credentials and database contents and is not a database backup.

## Files deleted

None.

## Files created

- `.env.example`
- `config/__init__.py`
- `config/asgi.py`
- `config/settings.py`
- `config/test_settings.py`
- `config/urls.py`
- `config/wsgi.py`
- `docs/PROJECT_RESTRUCTURING_PLAN.md`
- `docs/PROJECT_RESTRUCTURING_REPORT.md`
- `docs/original_file_hashes.json`
- `docs/original_source.zip`
- `docs/restructuring_baseline.json`
- `docs/restructuring_file_manifest.json`
- `health_ai/admin.py`
- `health_ai/apps.py`
- `health_ai/forms.py`
- `health_ai/models.py`
- `health_ai/serializers.py`
- `health_ai/services.py`
- `health_ai/tests/__init__.py`
- `health_ai/tests/test_regression.py`
- `health_ai/views.py`
- `health_ai/wellness_data.py`
- `ml/__init__.py`
- `ml/model_loader.py`
- `ml/prediction.py`
- `ml/preprocessing.py`
- `ml/recommendation.py`
- `scripts/verify_restructuring.py`

## Existing files modified

- `README.md`
- `accounts/admin.py`
- `accounts/api/serializers.py`
- `accounts/api/urls.py`
- `accounts/api/views.py`
- `accounts/forms.py`
- `accounts/models.py`
- `accounts/urls.py`
- `accounts/views.py`
- `dashboard/forms.py`
- `dashboard/urls.py`
- `dashboard/views.py`
- `health_ai/__init__.py`
- `health_ai/asgi.py`
- `health_ai/settings.py`
- `health_ai/urls.py`
- `health_ai/wsgi.py`
- `manage.py`
- `predictions/admin.py`
- `predictions/api/urls.py`
- `predictions/api/views.py`
- `predictions/forms.py`
- `predictions/ml_utils.py`
- `predictions/models.py`
- `predictions/urls.py`
- `predictions/views.py`
- `recommendations/engine.py`
- `recommendations/urls.py`
- `recommendations/views.py`
- `wellness/admin.py`
- `wellness/data.py`
- `wellness/models.py`
- `wellness/urls.py`
- `wellness/views.py`
