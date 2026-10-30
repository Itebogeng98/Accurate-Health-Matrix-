from pathlib import Path
import re
p=Path('docs/assignment3/diagrams')
diagrams={
'architecture': '''actor "Patient / approved user" as User
actor "Staff administrator" as Admin
component "Browser: Django templates + Bootstrap" as UI
component "Django / DRF\nhealth_ai.views" as Web
component "services.py\npersistence + dataset preview" as Services
component "ml.prediction\nML adapter / fallback scoring" as ML
database "Configured MySQL" as DB
folder "Local CSVs\ncurrently empty" as CSV
artifact "Joblib pipelines\ncurrently absent" as Models
cloud "Kaggle download API\noptional; not verified live" as Kaggle
User --> UI
Admin --> Web : /admin/
UI --> Web : HTTP forms / sessions
Web --> Services
Web --> ML
Services --> DB : Django ORM
Web --> DB : Django ORM
ML --> Models : load if present
Services --> CSV : preview first
Services --> Kaggle : requests.get if CSV absent\nand credentials set
note bottom of ML
Current available execution is heuristic fallback.
Training code implements RandomForest pipelines;
no trained artifacts found in this workspace.
end note''',
'use_cases': '''left to right direction
actor "Patient / approved user" as User
actor "Staff administrator" as Admin
actor "Developer / data analyst" as Dev
actor "Kaggle download API" as Kaggle
rectangle AHM {
usecase "UC01 Register / log in" as UC01
usecase "UC02 Submit stroke / lung inputs\nand receive risk result" as UC02
usecase "UC03 View dashboard / history" as UC03
usecase "UC04 Update profile" as UC04
usecase "UC05 Request appointment" as UC05
usecase "UC06 Read notifications" as UC06
usecase "UC07 Preview dataset" as UC07
usecase "UC08 Browse diet / wellness" as UC08
usecase "UC09 Manage records / approve users" as UC09
usecase "UC10 Trigger retraining" as UC10
}
User --> UC01
User --> UC02
User --> UC03
User --> UC04
User --> UC05
User --> UC06
User --> UC07
User --> UC08
Admin --> UC09
Admin --> UC10
Dev --> UC10 : training script
Kaggle -- UC07 : conditional download
note bottom of UC10
Training requires local CSVs.
Admin endpoint does not download datasets.
end note''',
'classes': '''hide empty members
class Role {
 id: BigAutoField
 role: CharField(100) {unique}
 __str__()
}
class CustomUser {
 id: BigAutoField
 email: EmailField {unique}
 first_name, last_name: CharField(100)
 phone_number: CharField(14) {nullable}
 join_date: DateTime
 is_active, is_staff, is_approved: bool
 reset_token: CharField(100) {nullable}
 __str__()
 set_password() [inherited]
 check_password() [inherited]
}
class CustomUserManager {
 create_user(email, password, extra_fields)
 create_superuser(email, password, extra_fields)
}
class PredictionRecord {
 id: BigAutoField
 disease: CharField(30)
 risk_level: CharField(20)
 probability: FloatField
 input_data: JSONField
 recommendation: TextField
 created_at: DateTime
 __str__()
}
class Appointment {
 id: BigAutoField
 reason: CharField(160)
 preferred_date: DateField
 notes: TextField
 status: CharField(20)
 created_at: DateTime
 __str__()
}
class Notification {
 id: BigAutoField
 title: CharField(120)
 message: TextField
 is_read: bool
 created_at: DateTime
 __str__()
}
class DoctorContact {
 name: CharField(120)
 specialty: CharField(40)
 province, city: CharField(80)
 address: CharField(255)
 phone: CharField(80)
 email: EmailField
 website: URLField
 notes: TextField
 __str__()
}
class ExercisePlan {
 title: CharField(120)
 category: CharField(40)
 difficulty: CharField(50)
 duration: CharField(80)
 instructions, safety_note: TextField
 __str__()
}
Role "1" -- "0..*" CustomUser : PROTECT
CustomUser "0..1" -- "0..*" PredictionRecord : CASCADE
CustomUser "1" -- "0..*" Appointment : CASCADE
CustomUser "1" -- "0..*" Notification : CASCADE
CustomUserManager ..> CustomUser : creates
class Group <<Django>>
class Permission <<Django>>
CustomUser "0..*" -- "0..*" Group
CustomUser "0..*" -- "0..*" Permission
note bottom of DoctorContact
DoctorContact and ExercisePlan exist in admin.
Public wellness views use static Python lists.
end note''',
'sequence': '''actor "Patient / approved user" as U
boundary "stroke.html / browser" as UI
control "stroke_predict" as V
control "StrokePredictionForm" as F
control "predict_stroke" as P
control "_load_model / _predict_with_pipeline" as M
control "recommend_diet" as R
control "_save_prediction" as S
database "PredictionRecord / database" as D
U -> UI : submit indicators
UI -> V : POST /predict/stroke/
alt unauthenticated
 V --> UI : 302 login
else authenticated
 V -> F : is_valid()
 alt invalid fields
  F --> V : errors
  V --> UI : 200 form with errors
 else valid
  F --> V : cleaned_data
  V -> P : predict_stroke(data)
  P -> M : load Joblib if file exists
  alt compatible model present
   M --> P : predict_proba(DataFrame)[0][1]
  else absent model or pipeline failure
   M --> P : None
   P -> P : heuristic score
  else joblib deserialisation fails
   M --> V : unhandled exception (500)
  end
  P --> V : probability, risk_label
  V -> R : recommend_diet(disease, risk)
  R --> V : fixed food list
  V -> S : save cleaned data + result
  S -> D : objects.create()
  alt saved
   D --> S : record
   S --> V : record
  else OperationalError / ProgrammingError
   S --> V : None
   V -> V : warning; result still displayed
  end
  V --> UI : 200 result, advice, foods
 end
end''',
'activity': '''start
:Open account registration;
:Submit account details;
if (Valid signup?) then (yes)
 :Create unapproved account;
 :Staff reviews account in admin;
 if (Approved?) then (yes)
  :Log in;
 else (no)
  :Login denied; await review;
  stop
 endif
else (no)
 :Display validation errors;
 stop
endif
if (Authentication succeeds?) then (yes)
 :Open stroke or lung form;
 :Submit health indicators;
 if (Valid input?) then (yes)
  if (Model artifact exists?) then (yes)
   :Load Joblib pipeline;
   if (Load succeeds?) then (yes)
    :Try named-column inference;
    if (Inference succeeds?) then (yes)
     :Use model probability;
    else (no)
     :Use heuristic fallback;
    endif
   else (no)
    :Unhandled server error;
    stop
   endif
  else (no)
   :Use heuristic fallback;
  endif
  :Assign risk label and diet advice;
  :Attempt report persistence;
  if (Database operation supported?) then (yes)
   :Report available in dashboard history;
  else (no)
   :Warn report not saved;
  endif
  :Display result;
  :Optionally request appointment;
  :Review pending request and notification;
 else (no)
  :Show form errors; correct and resubmit;
 endif
else (no)
 :Show login/API connection error;
endif
stop''',
'components': '''component "config\nsettings / URL root / WSGI / ASGI" as Config
component "health_ai.urls + views" as Views
component "forms + serializers" as Forms
component "models + admin" as Models
component "services" as Services
component "templates + static CSS" as Templates
component "ml: prediction, preprocessing,\nmodel_loader, recommendation" as ML
component "scripts/train_models.py" as Train
component "legacy app wrappers + migrations" as Legacy
component "Django / DRF" as Framework
component "pandas / sklearn / joblib" as Libraries
artifact "CSV inputs" as CSV
artifact "Joblib pipelines" as Artifacts
Config --> Views
Views --> Forms
Views --> Models
Views --> Services
Views --> Templates
Views --> ML
Views --> Train : staff retrain endpoint
Services --> Models
Legacy --> Models : compatibility exports
Views --> Framework
Models --> Framework
ML --> Libraries
Train --> Libraries
Train --> CSV : reads
Train --> Artifacts : writes
ML --> Artifacts : reads if present''',
'deployment': '''node "Observed local host\nWindows / Python 3.14.5" as Host {
 node "Isolated verification process" as Tests {
  artifact "Django test client\nconfig.test_settings" as Client
  database "SQLite :memory:\nsynthetic fixtures" as SQLite
 }
 artifact "Repository source / env" as Source
 folder "datasets / ml_models\nempty at inspection" as Files
}
Client --> SQLite
Client --> Source
node "Configured application runtime\nnot verified as a live service" as Runtime {
 artifact "config.wsgi / config.asgi\nDjango + DRF" as App
}
database "MySQL endpoint from environment\nnot connected for this evaluation" as MySQL
node "User browser" as Browser
cloud "Kaggle download API\noptional / not live-tested" as Kaggle
cloud "jsDelivr Bootstrap CDN" as CDN
Browser --> App : HTTP locally; HTTPS recommended
Browser --> CDN : CSS / JS
App --> MySQL : Django ORM
App --> Kaggle : HTTPS when preview needs it
App --> Files
note bottom of Runtime
Production proposal only: reverse proxy + TLS,
production WSGI/ASGI server, protected MySQL,
static collection and scheduled backups.
No cloud deployment evidence available.
end note''',
'erd': '''hide circle
entity accounts_role {
 * id : bigint PK
 --
 role : varchar(100) UNIQUE
}
entity accounts_customuser {
 * id : bigint PK
 --
 email : varchar(254) UNIQUE
 role_id : bigint FK NOT NULL
 password : varchar(128)
 is_approved : boolean
}
entity predictions_predictionrecord {
 * id : bigint PK
 --
 user_id : bigint FK NULL
 disease : varchar(30)
 probability : float
 input_data : JSON
}
entity accounts_appointment {
 * id : bigint PK
 --
 user_id : bigint FK NOT NULL
 preferred_date : date
 status : varchar(20)
}
entity accounts_notification {
 * id : bigint PK
 --
 user_id : bigint FK NOT NULL
 is_read : boolean
}
entity wellness_doctorcontact {
 * id : bigint PK
 --
 name : varchar(120)
 specialty : varchar(40)
}
entity wellness_exerciseplan {
 * id : bigint PK
 --
 title : varchar(120)
 category : varchar(40)
}
accounts_role ||--o{ accounts_customuser
accounts_customuser |o--o{ predictions_predictionrecord
accounts_customuser ||--o{ accounts_appointment
accounts_customuser ||--o{ accounts_notification
note bottom of accounts_customuser
Inherited auth fields and M:N group/permission
join tables are detailed in DATA_DICTIONARY.md.
This diagram shows the domain-table schema;
Django session, token, admin and auth tables also exist.
end note'''
}
for name,body in diagrams.items():
 body = re.sub(r'"[^"]*"', lambda m: m.group(0).replace('\n', r'\n'), body)
 body = body.replace('if CSV absent\nand credentials set', r'if CSV absent\nand credentials set')
 body = body.replace('   M --> V : unhandled exception (500)', '   break deserialisation failure ends request\n    M --> V : unhandled exception (500)\n   end')
 (p/(name+'.puml')).write_text('@startuml\n!pragma layout smetana\nskinparam shadowing false\nskinparam defaultFontSize 14\nskinparam wrapWidth 180\ntitle AHM - '+name.replace('_',' ').title()+'\n'+body+'\n@enduml\n',encoding='utf-8')
(p/'README.md').write_text('''# PlantUML sources

Eight editable diagrams accompany sections 3.1–3.6 and 4.2. Java, PlantUML and Graphviz were not found on PATH; no PlantUML JAR was found in the inspected project. Rendered exports and visual readability verification are **Evidence not available**. Sources use Smetana so Graphviz is not required by the rendering command.

From the repository root, after installing Java and obtaining an official PlantUML JAR locally:

```powershell
java -jar C:\\tools\\plantuml.jar -tsvg docs/assignment3/diagrams/*.puml
java -jar C:\\tools\\plantuml.jar -tpng docs/assignment3/diagrams/*.puml
```

Open each SVG, check labels, arrows and multiplicities at 100% zoom, and insert/export figures for submission. Command execution and syntax validation by PlantUML remain outstanding; source structure has been checked only. Diagram files use repository identifiers, not claims of deployment or lecturer approval.
''',encoding='utf-8')
print('Created',len(diagrams),'PlantUML sources')
