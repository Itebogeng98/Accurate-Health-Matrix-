# Evidence gaps and submission blockers

Prepared 30 September 2026. **Evidence not available** means not established from inspected artefacts; **Not tested** means evaluation was not executed. An existing code path is not proof of live operation or lecturer approval.

| ID | Gap / impact | Required resolution |
| --- | --- | --- |
| G01 | Approved proposal and lecturer approval record: Evidence not available. Proposal text and Assignment 2 DOCX exist but do not prove approval. | Supply authoritative approved version/approval record before finalising baseline claims. |
| G02 | Assignment 3 asks for exact three technology requirements; DOCX lists seven, earlier description five. Latency/accuracy targets conflict (1 s and 80–85% versus 50 ms and 85%). | Identify exact approved three and targets; then update 2.1–2.3/5.2 without deleting relevant implementation gaps. Clarification requested during preparation. |
| G03 | No lecturer approval evidence for consolidation, endpoints, appointments or notifications. | Record actual approval if available; otherwise preserve unapproved/undocumented status. |
| G04 | `datasets/` and `ml_models/` contain zero files. No trained AI/accuracy evidence. | Obtain approved datasets/licences, inspect schema, train in isolated copy, retain metrics/hashes/artifacts and evaluate trained inference. |
| G05 | Heuristic output is uncalibrated; model source/feature explanations not displayed clearly. | Identify fallback explicitly; evaluate model calibration, subgroup outcomes and intended-use limits. |
| G06 | M02 reproduces pending-account Basic-auth API access (200). TokenAuthentication not configured despite issuance. | Fix in separately authorised implementation work; add gate/ownership/CSRF coverage and re-evaluate. Application left unchanged in this documentation task. |
| G07 | Normal MySQL, historical MySQL repair migrations, real self-HTTP login/signup and deployment: Not tested. | Disposable MySQL end-to-end run, migration rehearsal and actual server workflow. SQLite results cannot certify MySQL. |
| G08 | Kaggle success, request errors, malformed ZIP and missing-CSV branches: Not tested. | Run isolated integration checks with authorised credentials; retain only sanitised metadata. |
| G09 | Browser connection timed out twice, including troubleshooting attempt. No actual UI screenshots or browser timing. | Capture exact screens in evidence/SCREENSHOTS.md with synthetic records; verify desktop/mobile layout and full-page performance. |
| G10 | Java, PlantUML and Graphviz absent from PATH; no project JAR. No rendered diagrams or visual QA. | Render all eight sources using diagrams/README.md; correct syntax/layout as needed; inspect every export at readable scale. Source checks do not certify rendering. |
| G11 | No real UAT participants/feedback. | Execute proposed checklist with agreed participants/thresholds; retain consent-aware anonymised results. |
| G12 | No proven backup/restore, retention, encryption-at-rest, consent or audit controls. Development settings unsuitable for production. | Implement agreed controls separately and conduct isolated restore drill; record evidence. |
| G13 | Missing per-case tests: invalid signup/lung input; history ownership/order; doctor/exercise filters; full admin permission matrix; concurrent load and extension exercise. | Add focused tests as implementation work and update traceability only from actual results. |
| G14 | Trainer may retain stroke feature casing different from form; preview does not save training CSV; retraining can succeed with absent files. | Verify actual dataset schema; validate inputs/exports and distinguish skipped/failed training from success. |
| G15 | Prediction save errors swallowed; corrupt artifacts uncaught; appointment/notification not explicitly atomic. | Targeted error/transaction tests and clearly specified operational behaviour. |
| G16 | Public wellness pages read static lists; database admin changes do not populate those lists. Data-tables page contains stale table/CSV names. | Reconcile in future code work; report currently follows models/code rather than display text. |
| G17 | Dependency versions unpinned; hardware minimums, clinical outcomes, availability and scalability unverified. | Capture lockfile and agreed representative workload; avoid deriving capacity or medical effectiveness from this run. |
| G18 | Git command reports not a repository despite `.git` directory; no AGENTS.md found; inaccessible `tmp/pdfs/deps` subdirectories. | No commit provenance available. Source hash manifest supplies inspected-file provenance; inaccessible generated PDF dependencies are not treated as application evidence. |

Current status: complete numbered evidence-based **draft**, not a finalised approved baseline. No application source/settings/database changed; no commit or push performed. Remaining items must be resolved or clearly acknowledged in the final submission through EC.

## Diagram follow-up - 30 September 2026

G10 is now resolved for Questions 3.1-3.4: four PlantUML sources were rendered to SVG/PNG, visually reviewed and embedded as vector diagrams in [the Question 3 PDF](../../output/pdf/ISJ107V_Question_3_Diagrams.pdf). See [editable sources and answers](question3_diagrams/README.md). The earlier full-assignment PDF predates this supplement. Rendering/visual review of 3.5-3.6 and the ERD remain outstanding; other baseline and evaluation gaps are unchanged.
