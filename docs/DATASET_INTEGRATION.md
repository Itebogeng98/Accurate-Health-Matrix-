# Kaggle dataset integration ? 2026-10-05

## Installed sources

| Local file | Kaggle source | Records | Source archive filename |
| --- | --- | ---: | --- |
| healthcare-dataset-stroke-data.csv | [Stroke Prediction Dataset](https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset) | 5,110 | healthcare-dataset-stroke-data.csv |
| lung cancer.csv | [Lung Cancer](https://www.kaggle.com/datasets/mysarahmadbhat/lung-cancer) | 309 | survey lung cancer.csv |
| food_nutrition.csv | [Nutritional values for common foods and products](https://www.kaggle.com/datasets/trolukovich/nutritional-values-for-common-foods-and-products) | 8,789 | nutrition.csv |

CSV contents remain as supplied; local filenames are chosen for this project. datasets/manifest.json records SHA-256 hashes, row counts, original columns, source URLs and download timestamps. Public metadata identifies version 1 for all three sources. Kaggle labels the stroke source ?Data files ? Original Authors?; it is not labelled CC0. The lung and nutrition sources are labelled ?CC0: Public Domain?. Attribution and source links are retained; review the stroke author's terms before redistributing that dataset.

## Integration

- ml/datasets.py defines the canonical filenames, Kaggle sources and required schemas.
- scripts/download_datasets.py downloads only the designated CSV member, validates its header and row count, and saves atomically within datasets/. It reads existing credentials without printing them. Existing CSVs are skipped unless --force is passed. No new packages were installed.
- Training fixes the Residence_type/residence_type mismatch, normalizes lung whitespace/capitalization, validates binary targets, strips unused ID columns by selecting the exact feature schema, and deduplicates before the split. Raw CSVs remain unchanged. Thirty-three duplicate lung rows are excluded from training.
- Missing CSVs or invalid schemas now fail training explicitly; the admin retraining endpoint reports failure rather than success after a skipped model.
- The trained pipelines are saved in ml_models/ and used by existing browser and API prediction paths. Existing URLs, names, permissions and prediction JSON keys are preserved.
- Dashboard previews use the local CSVs, including the food guide, and the Kaggle archive filename remains correctly mapped for remote previews.
- The food guide at /diet/ supports name search over all 8,789 foods. Existing food suggestions use exact reference matches to avoid substituting prepared dishes for raw ingredients. Nutrient values carry their source food name and serving basis. Units are explicitly parsed, missing values stay missing, and cache refreshes when the CSV changes. Prediction results and API food objects include the same calorie/protein/fibre/sodium values.
- Prediction UI labels the displayed value as a model score because these scores have not been clinically calibrated. Existing API probability keys remain compatible.

## Training results

Both models use the existing 200-tree random forest pipeline, an 80/20 stratified split, and random state 42. Imputation, scaling and categorical encoding are fitted only on the training split. Duplicate feature/target rows are removed before splitting. Model metrics and package versions are saved beside each artifact.

| Model | Train/test rows | Accuracy | Balanced accuracy | Positive recall |
| --- | --- | ---: | ---: | ---: |
| Stroke | 4,088 / 1,022 | 93.5% | 54.9% | 12.0% |
| Lung cancer | 220 / 56 | 91.1% | 79.2% | 95.8% |

Stroke is highly imbalanced (249 positive cases among 5,110 records). Its low positive recall makes the current model unsuitable for clinical screening despite high overall accuracy. Lung performance is measured on only 56 held-out records; neither evaluation is external clinical validation. Food data is used as a nutrition reference lookup, not as an invented disease-treatment training target.

## Validation

Django checks pass; makemigrations --check --dry-run reports no changes. All 23 tests pass in isolated SQLite, including seven new tests for column normalization, duplicate removal, malformed labels, real artifact inference using validated form values, nutrition units/cache refresh, food search rendering and all three dataset previews. Read-only verification confirms all 20 existing database tables still match the captured baseline, and the 33 protected environment/database/dependency/static/migration files retain their original bytes. No database rows or secrets were printed. The evolving training script is no longer treated as an immutable restructuring resource by the verifier.

## Commands

```powershell
.\env\Scripts\Activate.ps1
python scripts/download_datasets.py
python scripts/train_models.py
python manage.py runserver --settings=config.settings.development
```

The datasets and model artifacts have already been downloaded/trained. Only the runserver command is needed to use this installation. Open /diet/ for the food guide, /dashboard/ for dataset previews, and the existing prediction forms to use the trained models.
