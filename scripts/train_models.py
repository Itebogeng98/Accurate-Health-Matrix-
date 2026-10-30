"""Train demonstration models; held-out metrics are not clinical validation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from importlib.metadata import version

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    classification_report, confusion_matrix, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from ml.datasets import STROKE_FEATURES, LUNG_FEATURES, normalize_column

DATASETS = BASE_DIR / 'datasets'
MODELS = BASE_DIR / 'ml_models'


def prepare_training_data(path, features, target):
    """Validate the schema and remove duplicate feature/target rows before splitting."""
    df = pd.read_csv(path)
    original_rows = len(df)
    df.columns = [normalize_column(column) for column in df.columns]
    if df.columns.duplicated().any():
        raise ValueError('Dataset contains duplicate normalized column names.')
    missing = set((*features, target)) - set(df.columns)
    if missing:
        raise ValueError(f'Missing training columns: {sorted(missing)}')
    df = df.loc[:, [*features, target]].copy()
    if target == 'lung_cancer':
        df[target] = df[target].astype(str).str.strip().str.upper().map({'YES': 1, 'NO': 0})
    else:
        df[target] = pd.to_numeric(df[target], errors='raise')
    if df[target].isna().any() or set(df[target].unique()) != {0, 1}:
        raise ValueError('Training target must contain both binary classes without missing labels.')
    categorical = {'gender', 'ever_married', 'work_type', 'residence_type', 'smoking_status'}
    for column in features:
        if column in categorical:
            df[column] = df[column].str.strip()
        else:
            df[column] = pd.to_numeric(df[column], errors='raise')
        if df[column].notna().sum() == 0:
            raise ValueError(f'Training feature is entirely missing: {column}')
    df = df.drop_duplicates()
    if df[target].value_counts().min() < 5:
        raise ValueError('Insufficient minority-class rows for a stratified holdout.')
    return df.drop(columns=target), df[target].astype(int), original_rows


def _train(filename, features, target, artifact, class_weight=None):
    path = DATASETS / filename
    if not path.is_file():
        raise FileNotFoundError(f'Missing {filename}; run python scripts/download_datasets.py first.')
    X, y, original_rows = prepare_training_data(path, features, target)
    categorical = X.select_dtypes(include=['object', 'string']).columns.tolist()
    numeric = [name for name in features if name not in categorical]
    preprocessing = ColumnTransformer([
        ('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
        ]), numeric),
        ('cat', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore')),
        ]), categorical),
    ])
    model = Pipeline([
        ('preprocess', preprocessing),
        ('classifier', RandomForestClassifier(
            n_estimators=200, random_state=42, class_weight=class_weight,
        )),
    ])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=.2, random_state=42, stratify=y,
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]
    report = {
        'dataset': filename,
        'dataset_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'trained_at_utc': datetime.now(timezone.utc).isoformat(),
        'original_rows': original_rows,
        'duplicate_rows_removed': original_rows - len(X),
        'train_rows': len(X_train),
        'test_rows': len(X_test),
        'features': list(features),
        'class_counts': {str(k): int(v) for k, v in y.value_counts().items()},
        'random_state': 42,
        'package_versions': {name: version(name) for name in ('scikit-learn', 'pandas', 'numpy', 'joblib')},
        'accuracy': float(accuracy_score(y_test, predictions)),
        'balanced_accuracy': float(balanced_accuracy_score(y_test, predictions)),
        'roc_auc': float(roc_auc_score(y_test, probabilities)),
        'average_precision': float(average_precision_score(y_test, probabilities)),
        'confusion_matrix_labels': [0, 1],
        'confusion_matrix': confusion_matrix(y_test, predictions, labels=[0, 1]).tolist(),
        'classification_report': classification_report(y_test, predictions, output_dict=True, zero_division=0),
        'limitation': 'Internal dataset holdout only; uncalibrated scores, not clinically validated probabilities.',
    }
    MODELS.mkdir(exist_ok=True)
    output = MODELS / artifact
    temporary = output.with_suffix('.pkl.part')
    joblib.dump(model, temporary)
    temporary.replace(output)
    (MODELS / (output.stem + '_metrics.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(f'{target}: trained on {len(X_train):,} rows, tested on {len(X_test):,}; '
          f'accuracy={report["accuracy"]:.3f}, balanced accuracy={report["balanced_accuracy"]:.3f}, '
          f'positive recall={report["classification_report"]["1"]["recall"]:.3f}')
    return report


def train_stroke():
    return _train('healthcare-dataset-stroke-data.csv', STROKE_FEATURES, 'stroke', 'stroke_model.pkl', 'balanced')


def train_lung():
    return _train('lung cancer.csv', LUNG_FEATURES, 'lung_cancer', 'lung_cancer_model.pkl')


if __name__ == '__main__':
    train_stroke()
    train_lung()
