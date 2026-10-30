# Project restructuring plan

## Inspection and baseline

Inspected all project Python modules, eight numbered migrations, templates and URL references, CSS, training code, requirements and README before editing application code. No AGENTS.md or existing tests were found. `.env.example` is absent; `.env` is retained privately. The supplied `.git` directory is empty, so git status/diff cannot report history. System Python lacks Django; use `env/Scripts/python.exe` (Python 3.14, Django 6.0.6). Baseline check passes, makemigrations --check --dry-run reports no changes, showmigrations reports all migrations applied, and test discovery finds zero tests.

## Current architecture

```text
manage.py
health_ai/                 project settings, root URLs, ASGI/WSGI, MySQL adapter
accounts/                  all seven concrete model definitions, auth forms/views/admin
  api/                     serializers, signup/token handlers, unused email/auth helpers
  migrations/              0001 through 0005
predictions/               model re-export, forms/views/admin/URLs, ml_utils
  api/                     prediction and admin retraining endpoints
  migrations/              0001, 0002
wellness/                  model re-exports, views/admin/URLs, static directory data
  migrations/              0001
dashboard/                 views, appointment form, empty model/admin/migration scaffolding
recommendations/           diet engine/view, empty model/admin/migration scaffolding
templates/                 base, accounts, dashboard, predictions, recommendations, wellness
static/css/style.css
scripts/train_models.py
datasets/                  empty
ml_models/                 empty
db.sqlite3                 retained; NOT the configured active database
output/docx/, tmp_pdf_text/, AHM_Assignment_2_Submission.docx
env/, .env
```

Five local apps are installed. Accounts owns Role, CustomUser, Appointment and Notification. PredictionRecord explicitly uses the predictions label; DoctorContact and ExercisePlan explicitly use wellness. Their re-exports are not duplicate model definitions. Dashboard and recommendations have no models or numbered migrations. No duplicate route names or duplicate request handlers were found. HTML and API prediction handlers share inference but repeat orchestration; CSV preview helpers overlap. Dashboard templates repeat navigation intentionally; preserve UI.

## Migration and dependency decisions

- Keep AUTH_USER_MODEL = accounts.CustomUser. CustomUser references Role with PROTECT, and auth Group/Permission through many-to-many tables. Appointment, Notification and PredictionRecord reference the custom user with CASCADE. No OneToOneFields exist.
- Preserve all app labels, default table names, content types, permissions, relationship names and migration files. Accounts migrations depend on auth and admin; predictions depends on the swappable user and accounts. Wellness has an independent initial migration.
- Two existing MySQL RunPython migrations repair user foreign keys; one can null orphaned prediction user IDs. Do not rerun, edit, fake or delete these migrations.
- Move the main app's Python package to health_ai while keeping its AppConfig.label = accounts and MIGRATION_MODULES pointing at accounts.migrations. Predictions and wellness remain minimal migration apps. A single database app label is deliberately NOT attempted.
- Keep accounts.models as explicit compatibility exports, including CustomUserManager. Preserve predictions.models/wellness.models exports. Existing migration paths and third-party imports remain valid.
- Signup/login HTML handlers currently call local HTTP APIs; preserve their behavior and approval checks. API and browser routes keep names, paths and permissions.
- ML pipeline loading consumes ml_models/*.pkl; pandas provides named DataFrame columns. Keep fallback scores, recommendation rules, dataset filenames and training script behavior unchanged.

## Proposed architecture

```text
config/                    settings, project URLs, ASGI/WSGI
health_ai/                  main app (historical database label: accounts)
  models.py                all existing model definitions
  views.py                 browser and API handlers, grouped by feature
  forms.py, serializers.py, admin.py, apps.py, urls.py
  services.py              persistence and dashboard/dataset helpers
  wellness_data.py          existing static doctor/exercise data
  tests/                   regression tests
accounts/                  migrations and model import compatibility
predictions/, wellness/    migration apps and model import compatibility
ml/                        prediction, model_loader, preprocessing, recommendation
templates/, static/        unchanged
datasets/, ml_models/      unchanged data/artifact locations
scripts/, docs/            training and project documentation
```

Retain old settings/ASGI/WSGI entrypoints as compatibility wrappers. Remove obsolete feature views/forms/URLs/admin modules only after all internal references are redirected and regression checks pass. Keep uncertain helpers and academic output files documented rather than deleting them. No broad environment or cache cleanup.

## Execution and validation

1. Capture source backup and read-only database/model/route fingerprints because Git history is unavailable.
2. Separate config and consolidate model/form/admin definitions; run check and migration drift check.
3. Extract ML and services, consolidate request handlers and route definitions; run check and regression tests against an isolated in-memory SQLite test database.
4. Remove verified obsolete code; update README and create a detailed restructuring report and file manifest.
5. Run final check, makemigrations --check, showmigrations and tests. Compare active MySQL table counts/content hashes, model metadata, all route paths/names, SQLite bytes, migrations, templates, static assets and environment hashes against baseline. Never migrate the existing database or run functional write tests against it.

## Implementation adjustment

Automatic approval review rejected the proposed broad deletion of superseded source files due to irreversible-damage risk. The safe implemented alternative retains their paths as small compatibility wrappers (or existing empty scaffolding). All behavior is still implemented centrally; legacy URLconfs derive their patterns from health_ai.urls. No files or migrations were deleted. See the final report for the actual structure and inventory.
