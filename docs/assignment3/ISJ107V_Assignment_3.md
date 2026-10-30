# ISJ107V Assignment 3 — Semester 2, 2026

**Author:** Itebogeng Eugene Sebapu  
**Project:** Accurate Health Matrix (AHM) — AI-Powered Health Risk Prediction and Wellness Recommendation Web System  
**Version:** 0.1 — evidence-based draft; approved baseline confirmation outstanding  
**Prepared:** 30 September 2026 (Africa/Johannesburg)

This report describes inspected code and executed checks. The available Assignment 2 contains seven emerging-technology requirements, while the supplied Assignment 3 request specifies exactly three. The approved selection and lecturer approval record are **Evidence not available**. All seven are preserved provisionally; none is represented as an approved substitute. See [EVIDENCE_GAPS.md](EVIDENCE_GAPS.md).

## Question 1 — Final project baseline [6]

### 1.1 Project identity and executive summary [2]

The title follows section 1 of the available [Assignment 2 submission](../../AHM_Assignment_2_Submission.docx). AHM is an educational web application for preliminary stroke/lung-cancer risk awareness, report history and wellness information. Intended users are patients, staff administrators and, in the proposal, health professionals. A dedicated health-professional patient-review workflow is not implemented merely because that role exists.

The selected emerging technology is AI/ML. `scripts/train_models.py::train_stroke/train_lung` implement scikit-learn RandomForest pipelines. `ml/prediction.py::predict_stroke/predict_lung_cancer` load Joblib models when present and otherwise calculate heuristic scores. Both `datasets/` and `ml_models/` were empty. Available execution therefore demonstrates **fallback scoring**, not a verified trained AI model. Diet recommendations are fixed lists in `ml/recommendation.py::recommend_diet`.

The Django system implements registration, approval-gated browser login, profile editing, dashboard/history, two disease forms and prediction APIs, appointment requests, notifications, wellness pages, dataset previews and admin management. MySQL is configured; evaluation used isolated SQLite. Optional Kaggle download code exists in `health_ai/services.py::read_dataset_from_kaggle`; live access was **Not tested**.

### 1.2 Aim, objectives, scope and changes [2]

**Aim:** provide an educational workflow for submitting health indicators, obtaining preliminary risk results and reviewing reports and wellness information.

Measurable objectives are to: complete registration/approval/login with rejected unauthorised access; validate both disease forms and persist reports; restrict history, appointments and notifications to their owner; meet Assignment 2's 3-second page target under a defined workload; and evaluate trained-model accuracy and speed against confirmed targets. Operational acceptance criteria are derived in 2.1, not claimed as lecturer-approved.

| Change since available Assignment 2 | Implementation evidence and reason | Lecturer approval |
| --- | --- | --- |
| Appointments and notifications were planned | `appointments_view`, `notifications_view`, `accounts/migrations/0005_appointment_notification.py` now support follow-up requests; not verified clinician scheduling. | Evidence not available |
| Prediction/retraining APIs were planned | Actual `/predict/api/stroke/`, `/predict/api/lung/`, `/predict/api/admin/retrain-models/` expose existing functions; proposed `/api/...` paths differ. | Evidence not available |
| Five feature apps consolidated | Restructuring report records canonical `health_ai/`, `config/`, `ml/` with compatibility imports and retained model labels; reduces duplicate code but changes supportability wording. | Evidence not available |
| Trained AI remains unavailable | No CSV/model artifacts; fallback enables a demonstration, not a verified accuracy result. | Evidence not available |

Current scope includes the functions in 1.1. Clinical diagnosis, emergency triage, trend analysis, doctor dashboard, medical-record exchange, email password reset, automatic preview-to-training refresh, verified cloud hosting and nutrition-model personalisation are outside implemented scope. A `reset_token` field alone does not establish a reset workflow.

The earlier project-description extraction uses another AHM subtitle, inference below 50 ms and accuracy at least 85%. The DOCX submission uses under 1 second and 80–85% where dataset quality allows. This report uses the DOCX provisionally and preserves the conflict rather than declaring an approved change.

### 1.3 Document control [2]

| Version | Date | Author | Revision |
| --- | --- | --- | --- |
| 0.1 | 30 September 2026 | Itebogeng Eugene Sebapu | First preparation of this Assignment 3 package; no earlier revisions asserted. |

| Term | Meaning |
| --- | --- |
| AHM / AI/ML | Accurate Health Matrix / artificial intelligence and machine learning |
| DRF / ORM | Django REST Framework / object-relational mapper |
| CSV / ETL | Comma-separated values / extraction, transformation and loading |
| UML / ERD | Unified Modeling Language / entity relationship diagram |
| UAT | User acceptance testing with actual intended users |
| Fallback | Hand-coded demonstration score, distinct from trained inference |
| Pass / Partial / Not met | Assessed compliance within stated evidence boundaries |
| Not tested | Compliance has not been evaluated |

Project artefacts: [Assignment 2](../../AHM_Assignment_2_Submission.docx), [proposal extraction](../../tmp_pdf_text/Accurate_Health_Matrix_Project_Document(1).txt), [Assignment 2 brief](../../tmp_pdf_text/ISJ107V%20Assignment%202%20ver(1).txt), [README](../../README.md), [restructuring report](../PROJECT_RESTRUCTURING_REPORT.md), canonical source/migrations and `health_ai/tests/test_regression.py`. Supporting outputs are inventoried in [evidence/README.md](evidence/README.md). No AGENTS.md was found in inspected project/ancestor locations; `.agents` was empty. Git did not recognise the supplied `.git` as a repository, so no commit identifier is asserted.

## Question 2 — Requirements and traceability [8]

### 2.1 Prioritised requirements [3]

Assignment 2 supplies names but no requirement IDs. The following labels preserve its names/order. Priorities and operational criteria are newly derived for traceability, not proven approved priorities: **Must** = core/control; **Should** = important quality/support; **Could** = optional extension. D-prefixed requirements are newly derived for implemented additions.

| ID | Requirement | Priority | Measurable acceptance criterion |
| --- | --- | --- | --- |
| FR01 | User registration | Must | Valid signup returns 201 and creates pending account; invalid input returns 400. |
| FR02 | User login | Must | Approved credentials succeed; unapproved non-admin users cannot access protected workflows through any supported authentication method. |
| FR03 | Patient dashboard | Must | Authenticated page returns 200 with own identity, report count and latest result. |
| FR04 | Stroke prediction | Must | Valid input yields score/risk/advice; invalid API input returns 400. |
| FR05 | Lung cancer prediction | Must | Valid input yields score/risk/advice; invalid API input returns 400. |
| FR06 | Prediction history | Must | Successful persistence creates one associated record; dashboard shows latest 10 own reports. |
| FR07 | Dataset viewer | Should | Show columns, total row count and at most 50 preview rows; explain missing input. |
| FR08 | Kaggle API fetch | Should | Configured download yields ZIP CSV preview; missing credentials/request errors are handled. |
| FR09 | Diet recommendations | Should | Return implemented disease/risk food list. |
| FR10 | Wellness support | Should | Doctor/exercise pages render and filter static lists. |
| FR11 | Admin management | Must | Authorised staff manage seven models; ordinary users cannot invoke staff retraining. |
| NFR01 | Usability | Should | Proposed criterion: users complete main workflow without clipped controls or assistance on agreed mobile/desktop viewports. |
| NFR02 | Reliability | Must | Missing datasets/credentials show informative state rather than unhandled exception. |
| NFR03 | Performance | Should | Dashboard and prediction pages load within 3 seconds under defined school-project usage; distinguish backend from full-page timing. |
| NFR04 | Security | Must | Hash passwords; require authentication for protected pages/APIs; apply approval consistently. |
| NFR05 | Supportability | Should | Separate code into the five feature apps named in Assignment 2 with understandable responsibilities. |
| NFR06 | Scalability | Could | Demonstrate adding a disease/dataset without rewriting unrelated workflows. |
| NFR07 | Maintainability | Should | Trace clearly named models/APIs/views/templates; verify imports/routes/schema consistency. |
| ET01 | Model inference speed | Should | Assignment 2 response target under 1 second; report trained and fallback timing separately. |
| ET02 | Model accuracy target | Should | At least 80–85% where dataset quality allows; exact threshold unconfirmed, so report both cut-offs and per-class metrics. |
| ET03 | Dataset API access | Must | Configure `KAGGLE_USERNAME`, `KAGGLE_KEY` through environment/configuration without exposing values. |
| ET04 | Training data | Must | Both specified Kaggle/local CSVs available, documented and accepted by trainer. |
| ET05 | Model retraining | Should | Script exports both models and evaluation output; missing inputs cannot count as completed training. |
| ET06 | Explainability | Should | Display risk, probability and practical advice; Assignment 2 output criterion, not validated model explanation. |
| ET07 | Fallback operation | Must | Missing model files still yield deterministic demonstration scoring. |
| D01 | Profile editing | Should | Persist own names/phone without modifying another user's profile. |
| D02 | Appointment request | Should | Valid request creates own pending appointment and notification. |
| D03 | Notification reading | Should | Mark-read affects only current user's notifications. |

### 2.2 Traceability matrix [3]

UML files are in [diagrams/](diagrams/): UC = use_cases, C = classes, S = sequence, A = activity, CMP = components, DEP = deployment. Test IDs appear in 5.1. Partial is assessed partial compliance, not a blanket pass. T evidence is [regression-tests.txt](evidence/regression-tests.txt) with assertions in `health_ai/tests/test_regression.py`; M evidence is [measurements.json](evidence/measurements.json) and [measure.py](evidence/measure.py). P IDs are proposed checks.

| Requirement ID | UML reference | Implementation module/file | Test case ID | Completion status | Evidence |
| --- | --- | --- | --- | --- | --- |
| FR01 | UC01,C | `health_ai/views.py::signup_api`; `serializers.py::SignupSerializer` | T01 | Partial | Valid signup tested; invalid signup not tested. |
| FR02 | UC01,A | `views.py::obtain_token/login_view` | T01,T02,M02 | Not met | Browser gate passes; unapproved Basic-auth prediction returns 200. |
| FR03 | UC03,C | `views.py::dashboard` | T03,M01 | Partial | Rendering tested; cross-user history assertion missing. |
| FR04 | UC02,S | `views.py::stroke_predict/stroke_prediction_api`; `ml/prediction.py` | T04,T05 | Pass | Fallback response/persistence and invalid input tested; not clinical accuracy. |
| FR05 | UC02,S | `views.py::lung_predict/lung_prediction_api` | T04,T05 | Partial | Valid path tested; invalid lung-specific case missing. |
| FR06 | UC03,C | `services.py::_save_prediction`; `views.py::dashboard` | T05 | Partial | Persistence tested; swallowed DB errors return None; history order/ownership not asserted. |
| FR07 | UC07,CMP | `services.py::read_dataset_preview`; `views.py::dataset_detail` | T03,T06 | Partial | Synthetic preview tested; actual dataset absent. |
| FR08 | UC07,architecture | `services.py::read_dataset_from_kaggle` | M04,P03 | Partial | Missing credentials handled; live download/errors Not tested. |
| FR09 | UC08,CMP | `ml/recommendation.py::recommend_diet` | T03,T05 | Partial | Paths execute; exact list assertions missing. |
| FR10 | UC08,C | `views.py::doctors/exercises`; `wellness_data.py` | T03 | Partial | Pages render; filters/contact accuracy Not tested. |
| FR11 | UC09,UC10 | `health_ai/admin.py`; `views.py::retrain_models_api` | T07,T08 | Partial | Registration/admin/staff guard checked; full CRUD permissions missing. |
| NFR01 | UC02,A | `templates/`; `static/css/style.css` | P01,P02 | Not tested | Screenshots/UAT Evidence not available. |
| NFR02 | UC07,CMP | `services.py` preview functions | T06,M04 | Pass | Missing file and credentials handled in tested branches; outage/ZIP testing outstanding. |
| NFR03 | S,DEP | `views.py::dashboard/stroke_predict` | M01 | Partial | 100 backend requests per route below 3 s; browser/MySQL Not tested. |
| NFR04 | UC01,DEP | `models.py::CustomUserManager`; settings/views | T01,T08,M02 | Partial | Hashing/anonymous rejection pass; approval bypass confirmed. |
| NFR05 | CMP | `health_ai/` plus feature wrappers | T09 | Not met | Literal five-app structure changed; rationale is not approval. |
| NFR06 | CMP | `ml/prediction.py`; routing | P04 | Not tested | No extension exercise performed. |
| NFR07 | C,CMP | Canonical modules and compatibility imports | T09 | Partial | Structural checks pass; explainability in project defence not evaluated. |
| ET01 | S,DEP | `ml/prediction.py` | M03 | Partial | Fallback only; trained timing Not tested. |
| ET02 | CMP | `scripts/train_models.py` | P05 | Not tested | No CSV/model/held-out results. |
| ET03 | UC07 | `services.py::get_kaggle_credentials` | M04,P03 | Partial | Names/source confirmed; missing-key branch tested, live access not tested. |
| ET04 | CMP | `scripts/train_models.py`; empty `datasets/` | P05 | Not met | Required training files absent. |
| ET05 | UC10 | `views.py::retrain_models_api`; trainer | T07,P05 | Partial | Mock dispatch passes; real training/export Not tested. |
| ET06 | UC02,S | `views.py::_prediction_response` and prediction views | T05,M03 | Partial | Outputs exist; no feature explanation/clinical validation. |
| ET07 | UC02,S | `ml/prediction.py`; preprocessing | T04 | Pass | Fallback thresholds/missing models/pipeline incompatibility tested. |
| D01 | UC04,C | `forms.py::ProfileUpdateForm`; `profile_view` | T10 | Partial | Own update tested; attempted cross-user write not tested. |
| D02 | UC05,C | `AppointmentForm`; `appointments_view` | T10 | Pass | Pending request/notification tested. |
| D03 | UC06,C | `views.py::notifications_view` | T10 | Pass | Other user's notification remains unread. |

Unqualified `views.py`, `models.py`, `forms.py`, `serializers.py`, `services.py` above mean canonical files under `health_ai/`.

### 2.3 Emerging technology-specific requirements [2]

The exact **approved three** cannot be identified: **Evidence not available**. Clarification was requested. This provisional mapping retains every technology requirement in Assignment 2 section 10, rather than substituting easier targets.

| Requirement | Implementation | Method / available result | Remaining gap |
| --- | --- | --- | --- |
| ET01 Under 1-second response | Joblib load/named DataFrame inference or heuristic | M03: 100 fallback calls, median 0.052 ms, maximum 0.1213 ms | Trained timing Not tested; earlier 50 ms proposal target conflicts. |
| ET02 Accuracy 80–85% where quality allows | RandomForest, stratified 80/20 split, printed metrics | P05: Not tested | CSVs, held-out results and exact approved threshold absent. |
| ET03 Environment-configured dataset API | Credential lookup, HTTPS GET, ZIP preview | M04 missing-key state observed; code reads both names | Real access/error scenarios Not tested. |
| ET04 Kaggle/local training data | Trainer reads named local CSVs | Zero files present | Remote preview remains in memory, not trainer input. |
| ET05 Retraining script | Two training functions and staff endpoint | T07 mocked dispatch passes | No exports; endpoint can report success after missing-file messages. |
| ET06 Risk/probability/advice | Response helper and result views | Synthetic JSON in measurements.json | Scores uncalibrated; no model-feature explanation. |
| ET07 Missing-model fallback | Hand-coded scoring | T04 passes; real available fallback timed | Backend mode not clearly disclosed; corrupt Joblib load uncaught. |

## Question 3 — Final design as implemented [16]

Eight editable PlantUML sources are provided. Java/PlantUML were unavailable on PATH and no project JAR was located. **Rendered figures and visual readability verification: Evidence not available.** [Rendering instructions](diagrams/README.md) provide exact commands. Source checks are not a claim of successful PlantUML rendering.

### 3.1 High-level architecture [2]

**Figure 1 — [Architecture source](diagrams/architecture.puml).** Browser forms reach Django views, which call validation, ORM persistence, recommendation and inference helpers. MySQL is configured; SQLite is used only in isolated evaluation. CSVs and model artifacts are filesystem resources, presently absent. Kaggle is an actual optional download integration in `health_ai/services.py::read_dataset_from_kaggle`, not an inference service or live patient-data source. Preview checks local CSV before Kaggle. `templates/base/base.html` also requests Bootstrap from jsDelivr.

Separate ML helpers allow browser and DRF entrypoints to share prediction logic; there is no separately deployed AI microservice. Remote CSV previews are parsed in memory, not saved for training.

### 3.2 Use cases [3]

**Figure 2 — [Use-case source](diagrams/use_cases.puml).** Patient functions are distinct from staff administration and developer training. Health Professional is a role label, not an independent implemented consultation workflow.

| Core use-case field | Description |
| --- | --- |
| ID / name | UC02 — Submit indicators and receive a stroke risk result |
| Actors | Authenticated patient; application services are internal participants |
| Trigger | User submits `/predict/stroke/`. |
| Preconditions | Authenticated session and running application. Database migrations required to persist history. Model optional because fallback exists. |
| Normal flow | 1. Open form. 2. Enter indicators. 3. `StrokePredictionForm` validates. 4. `predict_stroke` attempts inference. 5. `risk_label` classifies score. 6. `recommend_diet` supplies guidance. 7. `_save_prediction` writes report. 8. View displays result; dashboard can show report. |
| Alternative flows | Absent model or incompatible pipeline uses fallback. Invalid fields redisplay errors. Lung version uses its own form/predictor. |
| Exceptions | Anonymous request redirects to login. Caught OperationalError/ProgrammingError on save returns None and browser warning. Uncaught Joblib deserialisation or other runtime failures can return 500. |
| Postconditions | Result displayed if calculation succeeds; history exists only when persistence succeeds. Prediction does not automatically create an appointment or notification. |

### 3.3 Class design [3]

**Figure 3 — [Class source](diagrams/classes.puml).** Seven domain classes reside in `health_ai/models.py`. A user has exactly one protected Role and zero or more appointments, notifications and predictions. A PredictionRecord may have no user because its FK is nullable. User deletion cascades to linked records; deletion of a referenced role is protected. There are no implemented Patient, Symptom or HealthRecord domain tables.

`CustomUserManager` creates users/superusers; password operations are inherited. Classes mainly hold data and string representations; forms/views/services perform validation and transactions. `DoctorContact` and `ExercisePlan` exist in admin, but public wellness views read `DOCTORS` and `EXERCISES` Python lists. Updating their database tables does not populate those public lists. Group/Permission many-to-many relations support Django authorisation.

### 3.4 Sequence design [3]

**Figure 4 — [Sequence source](diagrams/sequence.puml).** UC02 uses the browser/template, `stroke_predict`, form, predictor, model-loading/preprocessing helpers, diet helper and persistence service. Failure paths include authentication rejection, validation errors, absent/incompatible models, uncaught artifact-loading failure and caught database failure.

`_predict_with_pipeline` creates `pandas.DataFrame([data])` for named features. It catches prediction exceptions and returns None. `_load_model` does not catch deserialisation errors. Each request reloads the model, which must be included in cold/request timing. An artifact-load error terminates the request; rendering after successful prediction is a separate branch.

### 3.5 Activity workflow [2]

**Figure 5 — [Activity source](diagrams/activity.puml).** Registration and staff review precede login, validated submission and result display. Decisions cover approval, authentication, validation, model availability and saving. Optional appointment requests are separate actions and create pending requests/notifications, not confirmed clinician bookings. Invalid input requires correction/resubmission. A displayed result does not guarantee a saved history entry.

### 3.6 Components and deployment [3]

**Figure 6 — [Component source](diagrams/components.puml).** `config` supplies settings/entrypoints; `health_ai` owns canonical application code; `ml` supplies prediction/fallback/diet; `scripts/train_models.py` trains models. Old feature modules forward imports and retained migration packages preserve identity. `health_ai.apps.HealthAIConfig` keeps label `accounts`; `AUTH_USER_MODEL` remains `accounts.CustomUser`.

**Figure 7 — [Deployment source](diagrams/deployment.puml).** Observed execution is Windows 11, Python 3.14.5 and a local test process using in-memory SQLite. Configured MySQL was not contacted. Live web hosting, TLS and uptime were not verified. A reverse proxy, production WSGI/ASGI server, protected MySQL and backup schedule are labelled **proposed**, not deployed. Optional Kaggle and Bootstrap CDN dependencies are shown.

## Question 4 — Developer and operational documentation [10]

### 4.1 Stack, structure and interfaces [3]

| Layer / location | Actual responsibility |
| --- | --- |
| Python 3.14.5 / Django 6.0.6 | Observed interpreter and web framework |
| DRF 3.17.1 / requests | JSON APIs, self-HTTP login/signup, optional Kaggle downloads |
| Templates / `static/css/style.css` | HTML, Bootstrap 5.3.3 CDN, CSS and browser behaviour |
| MySQL / PyMySQL 1.2.0 | Configured normal DB; adapter in `config/__init__.py`; isolated tests use SQLite |
| pandas 3.0.4, NumPy 2.5.0, scikit-learn 1.9.0, Joblib 1.5.3 | Observed packages for preprocessing/training/persistence; no TensorFlow usage found |
| `config/` | Settings, URL root, ASGI/WSGI and test isolation |
| `health_ai/` | Models, browser/API handlers, forms, serializers, admin, services, regression tests |
| `ml/`, `scripts/` | Inference/fallback/recommendation; training entrypoint |
| `accounts/`, `predictions/`, `wellness/` | Retained migrations/model identities and compatibility modules |
| `dashboard/`, `recommendations/` | Compatibility modules, not standalone installed apps |
| `datasets/`, `ml_models/` | Expected CSV inputs/model outputs; empty |

`requirements.txt` uses broad or unpinned dependencies; measured versions are not a lockfile. Views are grouped by authentication, dashboard, prediction, recommendations and wellness. No external clinical API is verified.

**Figure 8 — Registration and login: Evidence not available. Figure 9 — Dashboard: Evidence not available. Figure 10 — Prediction form/result: Evidence not available.** Browser connection attempts timed out. Template rendering tests are not visual evidence. Required screens/captions are specified in [SCREENSHOTS.md](evidence/SCREENSHOTS.md); no screenshot was fabricated.

### 4.2 Database, datasets and controls [3]

**Figure 11 — [ERD source](diagrams/erd.puml).** [DATA_DICTIONARY.md](evidence/DATA_DICTIONARY.md) contains every domain field, type, default, choice, null/blank/unique constraint, relationship and deletion policy, including inherited authentication fields. It was generated from model metadata, not personal database rows.

| Entity | Field purposes |
| --- | --- |
| Role | `role` is unique account-category name. |
| CustomUser | `email` login identity; names/phone profile; protected role FK; active/staff/approved controls; password hash; join/last-login dates; unused reset-token scaffolding; group/permission authorisation. |
| PredictionRecord | Nullable user; disease, risk label, numeric score, submitted JSON, advice, timestamp. |
| Appointment | Required user; reason, preferred date, notes, pending/approved/completed/cancelled status, timestamp. |
| Notification | Required user; title/message, read flag, timestamp. |
| DoctorContact | Name, specialty, location/contact details, notes; admin-managed, not source of public lists. |
| ExercisePlan | Title, category, difficulty/duration, instructions/safety note; admin-managed, not public-list source. |

Each has an auto-generated bigint ID. Django additionally has auth, session, token, admin and migration tables. Normal settings do not select the old `db.sqlite3`. `views.py::data_tables` contains a stale `auth_user` label and illustrative CSV names; actual table is `accounts_customuser`, and training requires filenames below. Models/migrations, not that display text, govern this schema.

| Dataset | Expected schema / preprocessing | Availability |
| --- | --- | --- |
| `healthcare-dataset-stroke-data.csv` | Target stroke; optional id dropped; intended form features: gender, age, hypertension, heart_disease, ever_married, work_type, residence_type, avg_glucose_level, bmi, smoking_status. Numeric median imputation/scaling; object most-frequent imputation/one-hot encoding. | No CSV. Configured Kaggle slug: `fedesoriano/stroke-prediction-dataset`. |
| `survey lung cancer.csv` | Names stripped/lowercased/spaces replaced with underscores; lung_cancer YES/NO mapped to integers. Form features are gender, age and 13 symptom/lifestyle fields; same preprocessing. | No CSV. Configured slug: `mysarahmadbhat/lung-cancer`. |
| Nutrition data | Diet currently uses fixed lists; no active dataset/model dependency. | Planned only. |

Both trainers use stratified 80/20 splits, random_state 42 and 200 trees; stroke has balanced class weights. Preprocessing fits on training partition. Dataset row counts, actual schema, licences, missingness, duplicates and leakage analysis are **Evidence not available**. Stroke trainer retains original feature names: a supplied `Residence_type` column would not match form `residence_type` automatically. Verify actual schema before training. Preview scans every row to count them despite displaying only 50.

Form validation: stroke age 1–120, glucose 30–350, BMI 10–80; lung integer age 1–120; choices constrain categories. Signup requires an eight-character minimum password and unique email. Profile exposes names/phone only. Appointments require typed date/reason, but have no custom future-date validation. Probability has no explicit 0–1 validator; JSON does not enforce a separate clinical schema.

Implemented controls: Django password hashing, sessions and CSRF middleware, login decorators, `IsAuthenticated` prediction APIs, `IsAdminUser` retraining, owner-filtered queries and admin permissions. No application-level encryption-at-rest, consent/retention workflow, audit trail or documented backup/restore was found. Approval is not checked consistently (M02). Signup accepts a role choice; role label alone does not set staff privilege. Actual DRF defaults are Session and Basic authentication, **not TokenAuthentication**, despite token issuance. JWT is not implemented. Normal settings enable debug, have empty allowed-host/password-validator lists and a development secret; no value is reproduced. Fast MD5 hashing in test settings must remain isolated.

`docs/original_source.zip` is a source backup, not database recovery evidence. **Recommended, not implemented:** restrict dataset/file access; use secure deployment settings/HTTPS; establish retention and consent; take encrypted MySQL logical backups with restricted access; preserve approved dataset/model versions; restore into an isolated DB, apply checks and complete a synthetic workflow before declaring recovery successful. Agree schedule, retention and recovery targets. Restore testing: **Not tested**.

### 4.3 Implemented interface [2]

| Endpoint/method | Purpose | Input | Output | Authentication | Validation | Errors |
| --- | --- | --- | --- | --- | --- | --- |
| POST `/predict/api/stroke/` | `stroke_prediction_api` calls `_prediction_response` to calculate/store result | JSON/form fields matching StrokePredictionForm | 200 JSON status/message/data: record_id, disease, risk, probability, probability_percent, advice, foods | DRF Session or Basic defaults; session writes require CSRF; issued token alone is not configured authentication | Required fields, choices and numeric ranges in 4.2 | 400 invalid fields; 403 anonymous; 405 method; uncaught load/runtime errors may give 500; caught DB failure gives 200 with null record_id |

Synthetic request (credentials and personal records omitted):

```http
POST /predict/api/stroke/
Content-Type: application/json

{"gender":"Male","age":65,"hypertension":1,"heart_disease":1,"ever_married":"Yes","work_type":"Private","residence_type":"Urban","avg_glucose_level":160,"bmi":32,"smoking_status":"smokes"}
```

Selected measured response fields, generated identity replaced:

```json
{"status":"success","data":{"record_id":"<generated integer>","disease":"stroke","risk":"High Risk","probability":0.95,"probability_percent":95.0}}
```

Full sanitised response including message/advice/foods is in measurements.json. This is fallback output, not clinical probability. Browser clients use authenticated sessions/CSRF; do not assume a Token header works. Separately, `read_dataset_from_kaggle` performs HTTPS GET `/api/v1/datasets/download/<slug>` with configured credentials, 30-second timeout and ZIP parsing. Live result: **Not tested**.

### 4.4 Installation and operation [2]

For a **new development installation**, from repository root:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Create MySQL database/restricted user separately. Configure `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `PORT`; optionally `KAGGLE_USERNAME`, `KAGGLE_KEY`, privately. Do not overwrite an existing `.env`. Database variables are required even when test settings import normal settings before overriding the DB.

```powershell
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/`; staff approve accounts at `/admin/`. Preserve migration history, including conditional MySQL FK repairs; do not reset existing DBs or generate replacement initial migrations. The normal-database setup/startup above is documented from repository instructions and **Not tested** here. Executed isolated commands appear in 5.1.

For training, acquire/validate the exact CSVs in 4.2 and run `python scripts/train_models.py`. Outputs are `ml_models/stroke_model.pkl` and `ml_models/lung_cancer_model.pkl`. Preserve previous approved versions before retraining. Dataset previews do not create these training inputs.

**Proposed production deployment:** prepare a deployment settings module with private secret, DEBUG=False, actual allowed hosts, secured database/TLS settings and STATIC_ROOT. Current settings do not read environment names for every option, so merely setting environment variables is insufficient. Run `python manage.py collectstatic --noinput --settings=<deployment_settings_module>` and serve collected files through the web server. STATIC_ROOT is absent now, so collection is not verified. Serve `config.wsgi:application` or `config.asgi:application` using an installed production server appropriate to the host; requirements do not declare one. Development runserver is not production evidence.

Verified environment: Windows 11 AMD64, eight logical CPUs, Python 3.14.5; package versions in measurements.json. RAM/disk minimums were not measured. **Planning estimate only:** 4 GB RAM and 2 GB free space for an initial demonstration, then measure with real data/models; not a verified minimum or production capacity claim.

## Question 5 — Evaluation and responsible use [10]

### 5.1 Tests and evidence [4]

Executed on 30 September 2026 from repository root:

```powershell
.\env\Scripts\python.exe manage.py test health_ai.tests --settings=config.test_settings --noinput --verbosity 2
.\env\Scripts\python.exe manage.py check --settings=config.test_settings
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.test_settings
.\env\Scripts\python.exe docs\assignment3\evidence\measure.py
```

Existing suite: **16 tests in 30.115 seconds, OK**. Django check: **no issues**. Migration drift: **no changes detected**. Exact outputs are preserved in evidence. The suite creates/destroys an in-memory SQLite database and applies preserved migrations there. MySQL-specific repair branches are not exercised. Browser login/registration self-HTTP calls and retraining are mocked in relevant tests; persistence tests force fallback. The measurement runner uses synthetic data, isolated DB and blocked outbound GETs; it does not alter application behaviour.

| Test ID | Test level | Requirement ID | Scenario / expected result | Actual result | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | Integration | FR01,FR02,NFR04 | Signup pending user with hashed password; deny pending token login | Assertions pass | Pass | WorkflowTests.test_signup_and_approval_gate |
| T02 | Integration | FR02 | API login; browser session/logout; browser signup API contract | Two methods pass; self-HTTP mocked | Pass | WorkflowTests.test_api_login_and_browser_login_logout; test_browser_registration_preserves_api_contract |
| T03 | Server-side system | FR03,FR07,FR09,FR10 | 12 logged-in page routes render; unknown dataset 404 | Assertions pass; no browser | Pass | WorkflowTests.test_authenticated_pages_render |
| T04 | Unit | FR04,FR05,ET07 | Fallback scores/thresholds, named DataFrame, incompatible pipeline, artifact lookup | Three methods pass; model mocked | Pass | ArchitectureTests.test_prediction_fallbacks_and_thresholds; test_pipeline_receives_named_dataframe; test_model_loader_uses_existing_artifact_path |
| T05 | Integration | FR04,FR05,FR06,ET06 | Four browser/API reports persisted; empty stroke input 400; caught DB failure returns None | Assertions pass | Pass | WorkflowTests.test_browser_and_api_predictions_are_persisted |
| T06 | Unit | FR07,NFR02 | Synthetic CSV limit/count/columns correct; missing file handled | Assertions pass | Pass | ArchitectureTests.test_csv_preview_limits_rows_and_preserves_columns |
| T07 | Integration | FR11,ET05 | Staff admin renders; both retrain functions dispatched | Pass with training mocked | Pass | WorkflowTests.test_admin_and_retraining_endpoint |
| T08 | Integration | FR11,NFR04 | Anonymous protected pages redirect; prediction and nonstaff retrain denied | Assertions pass | Pass | WorkflowTests.test_authentication_required_and_api_permissions |
| T09 | Structural unit/integration | NFR05,NFR07 | Imports/routes/schema/admin match captured restructuring baseline | Four methods pass; not proof original app-split requirement met | Pass | ArchitectureTests.test_legacy_imports_and_urlconfs_forward_to_canonical_code; test_all_route_paths_and_names_match_original; test_model_tables_fields_and_relationships_match_original; test_admin_registration_and_canonical_handlers |
| T10 | Integration | D01,D02,D03 | Own profile update; pending appointment + notification; other user's read state unchanged | Assertions pass | Pass | WorkflowTests.test_appointment_notification_and_profile_updates |
| M01 | Performance | NFR03 | 100 backend calls per route below 3 s | Dashboard max 25.6842 ms; stroke POST max 132.1985 ms | Pass for backend samples only | measurements.json; measure.py |
| M02 | Security | FR02,NFR04 | Anonymous denied, hashed password, pending users denied across supported auth | 9/9 redirects; API 403; PBKDF2 verifies; pending Basic-auth prediction 200 | Not met for consistent approval | measurements.json |
| M03 | Component measurement | ET01,ET06,ET07 | Time available predictor; capture synthetic JSON | Fallback median 0.052 ms; response fields present | Pass for fallback timing only | measurements.json |
| M04 | Unit-level check | FR08,NFR02,ET03 | Missing credentials yield informative state | exists=False; Missing credentials | Pass for this branch | measurements.json |
| P01 | User acceptance | NFR01,FR01–FR06,D02,D03 | Intended users complete main workflow without technical help | Evidence not available | Not tested | Proposed checklist below |
| P02 | Browser system | NFR01,NFR03 | Desktop/mobile workflow, layout, errors, full page timing | Evidence not available | Not tested | SCREENSHOTS.md |
| P03 | External integration | FR08,ET03 | Authorised download, HTTP failure, invalid ZIP, missing CSV | Evidence not available | Not tested | Proposed isolated integration run |
| P04 | Extension evaluation | NFR06 | Add mock disease adapter without unrelated rewrites in disposable branch | Evidence not available | Not tested | Proposed exercise; no code changed |
| P05 | ML evaluation | ET01,ET02,ET04,ET05 | Train/evaluate both pipelines and verify exports | Evidence not available | Not tested | Procedure in 5.2 |

T evidence is [regression-tests.txt](evidence/regression-tests.txt); exact methods/assertions are in `health_ai/tests/test_regression.py`. [django-check.txt](evidence/django-check.txt) and [migration-check.txt](evidence/migration-check.txt) preserve independent checks. [measurements.json](evidence/measurements.json) is the structured measurement record.

**Proposed UAT checklist:** obtain informed participation using synthetic health inputs; ask each intended user to register, wait for staff approval, log in, correct an invalid form, submit both disease forms, find history, request an appointment and read its notification. Record completion, errors, assistance, time and whether the user understands the result's preliminary nature and fallback/model distinction. Agree participant count and acceptance threshold before testing. No participants, satisfaction scores or acceptance feedback are claimed.

### 5.2 Quantitative evaluation [2]

Environment: Windows 11 AMD64, eight logical CPUs, Python 3.14.5/Django 6.0.6, in-memory SQLite, synthetic account; no browser rendering/network latency. Each timing group excludes one warm-up and then executes 100 sequential calls using `perf_counter_ns`; p95 is the 95th sorted observation. Dashboard starts without prediction history; each stroke POST adds a synthetic report. This is a single-process measurement, not a concurrent load test.

| Requirement / target | Measured result | Assessment |
| --- | --- | --- |
| NFR03: pages within 3 seconds | Dashboard median 22.05945 ms, p95 25.1737 ms, max 25.6842 ms; stroke POST median 28.2268 ms, p95 41.1487 ms, max 132.1985 ms; n=100 each | All measured backend samples below target. Full page-load compliance Partial because MySQL, network, CDN and browser excluded. |
| NFR04: hashed passwords and protected access | 9/9 anonymous pages redirect; anonymous API 403; one PBKDF2-SHA256 check differs from plaintext and verifies; one pending Basic-auth user gets 200 | Hashing/anonymous checks pass for samples; consistent approval Not met. Production-hasher check explicitly overrides the weak regression-test hasher. |
| ET01: response under 1 second | Fallback median 0.052 ms, p95 0.0823 ms, max 0.1213 ms; n=100. Stroke backend maximum 132.1985 ms. | Available demonstration path below 1 s; trained-model inference Not tested. No accuracy/clinical conclusion follows. |

**Blocked ET02/P05 procedure:** obtain approved, licensed dataset versions; record hashes, row/label counts, missingness and duplicates; confirm training/form feature correspondence. In a disposable project copy, use the specified CSV filenames and run `python scripts/train_models.py`, capturing accuracy/classification reports separately for both diseases. Record 80/20 stratified partition sizes and random_state 42. Compare accuracy to both 80% and 85% until the approved cut-off is known; also report minority-class recall/precision, confusion matrix and majority-class baseline. Do not tune on the held-out test data. Confirm artifacts exist and inference actually uses them. Repeat 100 cold-load and 100 warm trained calls with compatible inputs, recording the same timing statistics. Review subgroup performance where ethically appropriate and adequately sampled. Missing data or silent fallback invalidates trained-model claims.

**Full NFR03 procedure:** deploy an isolated MySQL instance/application with synthetic records; measure 100 complete browser navigation/submission loads per route at agreed network/viewports, including static resources. Record environment, samples and percentiles against 3 seconds. Concurrent capacity/uptime needs an agreed longer workload; the earlier proposal's 99% availability target cannot be assessed from this session.

### 5.3 User guide and troubleshooting [2]

1. Open Register and submit account details. **Figure 8a placeholder:** `/accounts/register/`, synthetic identity, empty password field.
2. Wait for staff review in Django admin, then open Login. **Figure 8b placeholder:** `/accounts/login/`; separate pending-approval message capture with no credentials.
3. On Dashboard choose Stroke or Lung Cancer and enter values within the form ranges. **Figure 9 placeholder:** `/dashboard/`, synthetic identity/reports only.
4. Submit and read label, percentage and advice. This inspected installation uses demonstration fallback. **Figures 10a–10c placeholders:** stroke input, stroke result and lung form/result. Do not treat the output as a diagnosis.
5. Return to Dashboard for saved history. Use Appointments to submit a reason/date; status is pending, not confirmed clinician availability. Open Notifications and mark read. **Figure 12 placeholder:** appointment and notification pages with synthetic data.
6. Browse Diet, Exercises or Doctors, then log out. Directory details are static and have not been verified for current accuracy.

| Problem | Action |
| --- | --- |
| Awaiting approval | Ask the project administrator to review; do not bypass the gate. |
| Validation error | Correct highlighted range/choice and resubmit. |
| Result shown, report unsaved | Developer checks DB availability/migrations; the warning assumes missing migrations but caught errors can have another DB cause. |
| Dataset unavailable | Developer verifies local filename or private Kaggle configuration; never paste credentials into evidence. |
| Login API connection error | Developer checks server/self-host HTTP reachability; login/signup call the application's own API. |
| Model error/unexpected fallback | Check trusted artifact, versions and feature names; corrupt Joblib can cause 500. |
| Styling missing | Check static serving and Bootstrap CDN reachability. |

Screenshots are **Evidence not available** because browser connection timed out. [SCREENSHOTS.md](evidence/SCREENSHOTS.md) lists exact required captures. No fabricated screenshot substitutes are provided.

### 5.4 Limitations, responsible use and maintenance [2]

Missing trained data/models prevent claims of AI effectiveness. Heuristic scores resemble probabilities without calibration; there are no clinical outcomes, subgroup fairness findings or UAT results. Thresholds and fixed advice are code choices, not validated medical guidance. The interface should identify backend mode and educational purpose and support qualified clinical interpretation. Health inputs/reports persist without demonstrated consent, retention or encryption-at-rest controls.

Observed risks include Basic-auth approval bypass, development settings, weak password-policy configuration, issued-but-unconfigured token authentication, broad dataset visibility, untrusted Joblib loading, missing rate limits and uncaught load errors. A result may succeed after failed saving, and retraining may report completion without CSVs. Appointment/notification creation is not wrapped in one explicit transaction. Admin wellness records do not feed the public lists. Verified backup/restore/production availability evidence is absent.

Maintenance should include dependency locking/upgrades, regression and disposable-MySQL migration checks, model/data versioning, contact-list review and recovery drills. Test settings must not be used for production.

Two realistic future improvements are **(1)** validate/version real datasets and models, correct feature mismatches, evaluate held-out minority-class performance and display trained/fallback provenance; **(2)** unify authentication/approval across entrypoints, add focused bypass/ownership/CSRF checks, and deploy secure settings with tested backup/restoration. These address observed gaps and are proposed, not completed or lecturer-approved.

All numbered subsections are addressed. Approved baseline confirmation, the exact three technology requirements, rendered diagrams, real screenshots, trained-model evaluation and UAT remain outstanding before EC submission, as detailed in the gap register.
