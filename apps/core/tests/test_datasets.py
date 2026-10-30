"""Check dataset schemas, trained inference, and nutrition integration."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import skipUnless
from unittest.mock import patch

import pandas as pd
from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse

from ml.datasets import DATASET_SOURCES, STROKE_FEATURES, LUNG_FEATURES
from ml.model_loader import _load_model
from ml.nutrition import get_foods, nutrient_value, search_foods
from ml.preprocessing import _predict_with_pipeline
from ml.recommendation import recommend_diet
from scripts.train_models import prepare_training_data
from .test_regression import STROKE, LUNG


class NutritionTests(SimpleTestCase):
    def test_units_missing_values_and_zero(self):
        self.assertEqual(nutrient_value('0.2 g', 'mg'), 200)
        self.assertEqual(nutrient_value('250 mg', 'g'), .25)
        self.assertEqual(nutrient_value('0', 'g'), 0)
        for value in ('', 'unknown', 'nan', '-1 g', '12 oz'):
            self.assertIsNone(nutrient_value(value, 'g'))

    def test_food_lookup_preserves_serving_basis_and_refreshes_changed_csv(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'food.csv'
            header = 'name,serving_size,calories,protein,fiber,sodium\n'
            path.write_text(header + 'Oats,100 g,389,16.89 g,10.6 g,2 mg\nApple,100 g,52,0.2 g,2.4 g,1 mg\n')
            with patch('ml.nutrition.DATASET_PATH', path):
                result = search_foods('oats')
                self.assertEqual(result['total_count'], 2)
                self.assertEqual(result['match_count'], 1)
                oat = result['foods'][0]
                self.assertEqual(oat['serving_size'], '100 g')
                self.assertEqual(oat['nutrition']['fiber_g'], 10.6)
                self.assertEqual(search_foods('unknown')['foods'], [])
                enriched = recommend_diet('stroke', 'Low Risk')[0]
                self.assertEqual(enriched['reference_food'], 'Oats')
                self.assertEqual(enriched['nutrition']['sodium_mg'], 2)
                path.write_text(header + 'Oats,100 g,390,17 g,11 g,3 mg\n')
                self.assertEqual(get_foods()[0]['nutrition']['calories_kcal'], 390)

    def test_food_guide_renders_search_and_missing_data(self):
        response = self.client.get(reverse('diet_home'), {'q': 'oats'})
        self.assertContains(response, 'Food Guide')
        self.assertContains(response, 'name="q"')
        self.assertEqual(response.context['query'], 'oats')
        with TemporaryDirectory() as folder, patch('ml.nutrition.DATASET_PATH', Path(folder) / 'missing.csv'):
            response = self.client.get(reverse('diet_home'))
            self.assertContains(response, 'Food nutrition data is currently unavailable.')
            self.assertEqual(response.context['food_guide']['total_count'], 0)
            self.assertTrue(response.context['foods'])


class TrainingDataTests(SimpleTestCase):
    def test_stroke_header_normalization_and_duplicate_removal(self):
        rows = []
        for label in (0, 1):
            for index in range(6):
                rows.append({**STROKE, 'age': 30 + index + 10 * label, 'stroke': label})
        df = pd.DataFrame(rows + [rows[0]]).rename(columns={'residence_type': 'Residence_type'})
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'stroke.csv'
            df.to_csv(path, index=False)
            X, y, original = prepare_training_data(path, STROKE_FEATURES, 'stroke')
            self.assertEqual(list(X.columns), list(STROKE_FEATURES))
            self.assertEqual(original, 13)
            self.assertEqual(len(X), 12)
            self.assertEqual(set(y), {0, 1})
            df.drop(columns=['age']).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, 'age'):
                prepare_training_data(path, STROKE_FEATURES, 'stroke')

    def test_lung_labels_and_whitespace_are_normalized(self):
        rows = [{**LUNG, 'age': 30 + i + 10 * label, 'lung_cancer': ' YES ' if label else 'NO'}
                for label in (0, 1) for i in range(6)]
        df = pd.DataFrame(rows)
        df.columns = [column.upper().replace('_', ' ') + ' ' for column in df.columns]
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'lung.csv'
            df.to_csv(path, index=False)
            X, y, _ = prepare_training_data(path, LUNG_FEATURES, 'lung_cancer')
            self.assertEqual(list(X.columns), list(LUNG_FEATURES))
            self.assertEqual(set(y), {0, 1})
            df.loc[0, 'LUNG CANCER '] = 'INVALID'
            df.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, 'binary classes'):
                prepare_training_data(path, LUNG_FEATURES, 'lung_cancer')


@skipUnless((settings.BASE_DIR / 'ml_models/stroke_model.pkl').exists()
            and (settings.BASE_DIR / 'ml_models/lung_cancer_model.pkl').exists()
            and (settings.BASE_DIR / 'datasets/food_nutrition.csv').exists(),
            'Download datasets and train models to exercise the local artifacts.')
class DownloadedArtifactTests(SimpleTestCase):
    def test_trained_models_accept_actual_form_values_without_fallback(self):
        from apps.core.forms import StrokePredictionForm, LungCancerPredictionForm
        for artifact, values, features in (
            ('stroke_model.pkl', STROKE, STROKE_FEATURES),
            ('lung_cancer_model.pkl', LUNG, LUNG_FEATURES),
        ):
            model = _load_model(artifact)
            self.assertEqual(list(model.feature_names_in_), list(features))
            form_class = StrokePredictionForm if artifact == 'stroke_model.pkl' else LungCancerPredictionForm
            form = form_class(values)
            self.assertTrue(form.is_valid(), form.errors)
            score = _predict_with_pipeline(model, form.cleaned_data)
            self.assertIsNotNone(score)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)

    def test_all_datasets_are_visible_and_recommendations_have_nutrients(self):
        from apps.core.services import get_dashboard_datasets, read_dataset_preview
        entries = {dataset['slug']: dataset for dataset in get_dashboard_datasets()}
        for source in DATASET_SOURCES:
            self.assertEqual(entries[source['slug']]['status'], 'Available')
            preview = read_dataset_preview(source['filename'], limit=2)
            self.assertEqual(len(preview['rows']), 2)
            self.assertGreater(preview['total_rows'], 2)
        for disease in ('stroke', 'lung_cancer'):
            for food in recommend_diet(disease, 'High Risk'):
                self.assertIn('nutrition', food, food['food'])
                self.assertEqual(food['serving_size'], '100 g')
