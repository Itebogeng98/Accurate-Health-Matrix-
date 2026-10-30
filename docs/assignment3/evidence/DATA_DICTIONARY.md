# Model-derived data dictionary

Generated from Django model metadata, not live database rows. All seven domain models are defined in `health_ai/models.py`. Inherited authentication fields are included. Empty values are allowed only where stated. Choice validation occurs in forms/model validation; it is not automatically a SQL CHECK constraint.

## Role — `accounts_role`

| Field | Type | Constraints / purpose |
| --- | --- | --- |
| id | BigAutoField | primary key; unique; not null; form blank allowed |
| role | CharField | unique; not null; form required; max length 100 |

## CustomUser — `accounts_customuser`

| Field | Type | Constraints / purpose |
| --- | --- | --- |
| id | BigAutoField | primary key; unique; not null; form blank allowed |
| password | CharField | not null; form required; max length 128 |
| last_login | DateTimeField | nullable; form blank allowed |
| is_superuser | BooleanField | not null; form required; default False |
| email | EmailField (SQL character field) | unique; not null; form required; max length 254 |
| first_name | CharField | not null; form required; max length 100 |
| last_name | CharField | not null; form required; max length 100 |
| role | ForeignKey | not null; form required; references Role; delete PROTECT |
| phone_number | CharField | nullable; form blank allowed; max length 14 |
| join_date | DateTimeField | not null; form required; default now |
| is_active | BooleanField | not null; form required; default True |
| is_staff | BooleanField | not null; form required; default False |
| is_approved | BooleanField | not null; form required; default False |
| reset_token | CharField | nullable; form blank allowed; max length 100 |
| groups | ManyToManyField | not null; form blank allowed; references Group |
| user_permissions | ManyToManyField | not null; form blank allowed; references Permission |

## PredictionRecord — `predictions_predictionrecord`

| Field | Type | Constraints / purpose |
| --- | --- | --- |
| id | BigAutoField | primary key; unique; not null; form blank allowed |
| user | ForeignKey | nullable; form blank allowed; references CustomUser; delete CASCADE |
| disease | CharField | not null; form required; max length 30; choices stroke, lung_cancer |
| risk_level | CharField | not null; form required; max length 20 |
| probability | FloatField | not null; form required; default 0 |
| input_data | JSONField | not null; form required; default dict |
| recommendation | TextField | not null; form blank allowed |
| created_at | DateTimeField | not null; form blank allowed; creation timestamp |

## Appointment — `accounts_appointment`

| Field | Type | Constraints / purpose |
| --- | --- | --- |
| id | BigAutoField | primary key; unique; not null; form blank allowed |
| user | ForeignKey | not null; form required; references CustomUser; delete CASCADE |
| reason | CharField | not null; form required; max length 160 |
| preferred_date | DateField | not null; form required |
| notes | TextField | not null; form blank allowed |
| status | CharField | not null; form required; max length 20; choices pending, approved, completed, cancelled; default pending |
| created_at | DateTimeField | not null; form blank allowed; creation timestamp |

## Notification — `accounts_notification`

| Field | Type | Constraints / purpose |
| --- | --- | --- |
| id | BigAutoField | primary key; unique; not null; form blank allowed |
| user | ForeignKey | not null; form required; references CustomUser; delete CASCADE |
| title | CharField | not null; form required; max length 120 |
| message | TextField | not null; form required |
| is_read | BooleanField | not null; form required; default False |
| created_at | DateTimeField | not null; form blank allowed; creation timestamp |

## DoctorContact — `wellness_doctorcontact`

| Field | Type | Constraints / purpose |
| --- | --- | --- |
| id | BigAutoField | primary key; unique; not null; form blank allowed |
| name | CharField | not null; form required; max length 120 |
| specialty | CharField | not null; form required; max length 40; choices neurologist, pulmonologist, gp |
| province | CharField | not null; form required; max length 80; default Gauteng |
| city | CharField | not null; form blank allowed; max length 80 |
| address | CharField | not null; form blank allowed; max length 255 |
| phone | CharField | not null; form blank allowed; max length 80 |
| email | EmailField (SQL character field) | not null; form blank allowed; max length 254 |
| website | URLField (SQL character field) | not null; form blank allowed; max length 200 |
| notes | TextField | not null; form blank allowed |

## ExercisePlan — `wellness_exerciseplan`

| Field | Type | Constraints / purpose |
| --- | --- | --- |
| id | BigAutoField | primary key; unique; not null; form blank allowed |
| title | CharField | not null; form required; max length 120 |
| category | CharField | not null; form required; max length 40; choices stroke, lung_cancer, general |
| difficulty | CharField | not null; form required; max length 50; default Beginner |
| duration | CharField | not null; form required; max length 80; default 10-20 minutes |
| instructions | TextField | not null; form required |
| safety_note | TextField | not null; form blank allowed |
