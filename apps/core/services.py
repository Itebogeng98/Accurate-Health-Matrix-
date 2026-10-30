from pathlib import Path
import csv
from io import BytesIO
from zipfile import ZipFile

import requests
from decouple import config
from django.db import OperationalError, ProgrammingError
from django.http import Http404
from django.utils.text import slugify
from ml.datasets import DATASET_SOURCES

from .models import Notification, PredictionRecord

from django.conf import settings
BASE_DIR = settings.BASE_DIR

DATASETS_DIR = BASE_DIR / 'datasets'

EXPECTED_DATASETS = DATASET_SOURCES


def get_dashboard_datasets():
    DATASETS_DIR.mkdir(exist_ok=True)
    local_files = {path.name: path for path in DATASETS_DIR.glob('*.csv')}
    datasets = []
    kaggle_ready = bool(config('KAGGLE_USERNAME', default='') and config('KAGGLE_KEY', default=''))

    for dataset in EXPECTED_DATASETS:
        path = local_files.pop(dataset['filename'], None)
        status = 'Available' if path else ('Kaggle API' if kaggle_ready else 'Needs API Key')
        datasets.append({
            **dataset,
            'status': status,
            'size': f'{path.stat().st_size / 1024:.1f} KB' if path else 'Live API' if kaggle_ready else 'No local file',
        })

    for path in sorted(local_files.values()):
        datasets.append({
            'slug': slugify(path.stem),
            'name': path.stem.replace('_', ' ').replace('-', ' ').title(),
            'filename': path.name,
            'source': 'Local CSV',
            'status': 'Available',
            'size': f'{path.stat().st_size / 1024:.1f} KB',
        })

    return datasets


def get_kaggle_credentials():
    username = config('KAGGLE_USERNAME', default='')
    key = config('KAGGLE_KEY', default='')
    return username, key


def read_csv_preview_from_text(csv_text, limit):
    return _read_csv_preview(csv.DictReader(csv_text.splitlines()), limit)


def _read_csv_preview(reader, limit):
    """Shared preview/count logic for local files and downloaded CSV text."""
    rows = []
    total_rows = 0
    for row in reader:
        total_rows += 1
        if len(rows) < limit:
            rows.append([row.get(column, '') for column in reader.fieldnames or []])

    return {
        'exists': True,
        'columns': reader.fieldnames or [],
        'rows': rows,
        'total_rows': total_rows,
    }


def read_dataset_from_kaggle(dataset, limit):
    username, key = get_kaggle_credentials()
    if not username or not key:
        return {
            'exists': False,
            'columns': [],
            'rows': [],
            'total_rows': 0,
            'source_mode': 'Missing credentials',
            'error': 'Add KAGGLE_USERNAME and KAGGLE_KEY to your .env file to fetch this dataset from Kaggle API.',
        }

    kaggle_slug = dataset.get('kaggle_slug')
    if not kaggle_slug:
        return {
            'exists': False,
            'columns': [],
            'rows': [],
            'total_rows': 0,
            'source_mode': 'Unsupported',
            'error': 'This local dataset does not have a Kaggle API slug configured.',
        }

    url = f'https://www.kaggle.com/api/v1/datasets/download/{kaggle_slug}'
    try:
        response = requests.get(url, auth=(username, key), timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {
            'exists': False,
            'columns': [],
            'rows': [],
            'total_rows': 0,
            'source_mode': 'Kaggle API error',
            'error': 'Kaggle request failed. Check access and credentials.',
        }

    try:
        with ZipFile(BytesIO(response.content)) as archive:
            target_name = dataset.get('archive_filename', dataset['filename']).lower()
            csv_names = [name for name in archive.namelist() if name.lower().endswith('.csv')]
            selected_name = next((name for name in csv_names if name.split('/')[-1].lower() == target_name), None)
            selected_name = selected_name or (csv_names[0] if csv_names else None)
            if not selected_name:
                raise ValueError('No CSV file found inside the Kaggle dataset archive.')
            csv_text = archive.read(selected_name).decode('utf-8-sig', errors='replace')
    except Exception as exc:
        return {
            'exists': False,
            'columns': [],
            'rows': [],
            'total_rows': 0,
            'source_mode': 'Kaggle archive error',
            'error': str(exc),
        }

    preview = read_csv_preview_from_text(csv_text, limit)
    preview['source_mode'] = 'Kaggle API'
    preview['error'] = ''
    return preview


def get_patient_context(user):
    patient_name = f'{user.first_name} {user.last_name}'.strip() or user.email
    return {
        'patient': user,
        'patient_name': patient_name,
        'patient_initials': ''.join(part[0] for part in patient_name.split()[:2]).upper() or 'AH',
        'patient_role': getattr(getattr(user, 'role', None), 'role', 'Patient'),
        'datasets': get_dashboard_datasets(),
        'unread_notifications': Notification.objects.filter(user=user, is_read=False).count(),
    }


def get_dataset_by_slug(dataset_slug):
    for dataset in get_dashboard_datasets():
        if dataset['slug'] == dataset_slug:
            return dataset
    raise Http404('Dataset not found')


def read_dataset_preview(filename, limit=50):
    path = DATASETS_DIR / filename
    if not path.exists():
        return {
            'exists': False,
            'columns': [],
            'rows': [],
            'total_rows': 0,
            'source_mode': 'Local CSV missing',
            'error': '',
        }

    with path.open('r', newline='', encoding='utf-8-sig') as csv_file:
        preview = _read_csv_preview(csv.DictReader(csv_file), limit)
    return {**preview, 'source_mode': 'Local CSV', 'error': ''}


def _save_prediction(user, disease, risk, probability, data, advice):
    """Save a prediction without crashing the whole page if migrations were not run."""
    try:
        return PredictionRecord.objects.create(
            user=user,
            disease=disease,
            risk_level=risk,
            probability=probability,
            input_data=data,
            recommendation=advice,
        )
    except (OperationalError, ProgrammingError):
        return None
