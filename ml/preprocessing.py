def _predict_with_pipeline(model, data):
    """Send one row to a scikit-learn pipeline using column names.
    The training script trains on a pandas DataFrame, so prediction should also
    use a one-row DataFrame instead of a plain list/dict.
    """
    try:
        import pandas as pd
        row = pd.DataFrame([data])
        return float(model.predict_proba(row)[0][1])
    except Exception:
        # If a trained model has a different format, fall back gracefully.
        return None
