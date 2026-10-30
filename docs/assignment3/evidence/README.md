# Evidence index

Prepared 30 September 2026. Paths relative to this directory. All executed application checks used `config.test_settings` and in-memory SQLite; original MySQL and `db.sqlite3` were not accessed for evaluation.

| File | Purpose / limits |
| --- | --- |
| regression-tests.txt | Exact verbosity-2 output: 16 existing regression tests, 30.115 seconds, OK; migration/application checks use SQLite; mocks identified in report. |
| django-check.txt | `env/Scripts/python.exe manage.py check --settings=config.test_settings`: no issues. |
| migration-check.txt | `env/Scripts/python.exe manage.py makemigrations --check --dry-run --settings=config.test_settings`: no changes detected. |
| measure.py | Reproducible, isolated synthetic measurement runner; blocks outbound GETs; never runs normal DB settings. Synthetic test credentials in executable fixture are not real account credentials. |
| measurements.json | Environment/package versions; empty data/model inventory; raw timing summaries; auth results; sanitised synthetic API response. |
| measurement-run.txt | Original captured runner output, including harmless docstring escape warning and expected anonymous 403 log. Warning later corrected in runner; measurements unchanged. |
| DATA_DICTIONARY.md | ORM-derived full domain-field metadata, including inherited auth fields; no database rows. |
| SCREENSHOTS.md | Exact outstanding screenshot states/captions and capture conditions. No screenshots fabricated. |
| build_diagrams.py | Regenerates the eight editable sources. Requires subsequent PlantUML rendering/visual verification. |
| source_manifest.json | SHA-256 hashes of inspected application and baseline artefacts; excludes secret files, databases and original records. |
| validate_package.py | Re-runnable package link/numbering/reference/source-structure validator; does not execute application tests. |
| validation.json | Numbering, local links, diagram inventory/source structure and requirement/test cross-reference checks; not PlantUML syntax or visual QA. |

Run commands from repository root; prerequisite installed environment and private DB variable configuration are described in 4.4. `measure.py` migrates only its in-memory database, creates synthetic fixtures, performs 100 samples plus one excluded warm-up for each timing group, and writes these evidence files. Subsequent reruns replace the measurements; update reported numbers accordingly. M02's returned 200 is evidence of an approval-control failure, not a success criterion.

No live Kaggle call, real trained inference, real UAT, production security certification, MySQL verification or browser screenshot is implied by passing regression tests. The original PowerShell-captured logs are UTF-16; structured JSON/Markdown are UTF-8.

Final source review: both Assignment 2 DOCX copies have identical SHA-256 hashes. All 20 required subsection headings, 28 requirement rows and 19 test/measurement/proposed-test IDs are present. All Markdown file links resolve. Eight PlantUML sources have matching start/end markers and single-line quoted labels. Python evidence scripts parse successfully. These checks do not replace outstanding visual/UAT/ML evaluation.
