from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / 'ml_models'

def _load_model(name):
    path = MODEL_DIR / name
    if path.exists():
        return joblib.load(path)
    return None
