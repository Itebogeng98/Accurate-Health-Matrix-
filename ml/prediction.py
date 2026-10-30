from .model_loader import _load_model
from .preprocessing import _predict_with_pipeline

def risk_label(probability):
    if probability >= 0.70:
        return 'High Risk'
    if probability >= 0.40:
        return 'Medium Risk'
    return 'Low Risk'


def predict_stroke(data):
    model = _load_model('stroke_model.pkl')
    probability = None
    if model:
        probability = _predict_with_pipeline(model, data)

    if probability is None:
        score = 0
        score += 0.25 if float(data.get('age', 0)) > 55 else 0
        score += 0.18 if int(data.get('hypertension', 0)) == 1 else 0
        score += 0.18 if int(data.get('heart_disease', 0)) == 1 else 0
        score += 0.15 if float(data.get('avg_glucose_level', 0)) > 140 else 0
        score += 0.12 if float(data.get('bmi', 0)) > 30 else 0
        score += 0.12 if data.get('smoking_status') == 'smokes' else 0
        probability = min(score, 0.95)

    return probability, risk_label(probability)


def predict_lung_cancer(data):
    model = _load_model('lung_cancer_model.pkl')
    probability = None
    if model:
        probability = _predict_with_pipeline(model, data)

    if probability is None:
        risk_keys = [
            'smoking', 'yellow_fingers', 'anxiety', 'peer_pressure',
            'chronic_disease', 'fatigue', 'allergy', 'wheezing',
            'alcohol_consuming', 'coughing', 'shortness_of_breath',
            'swallowing_difficulty', 'chest_pain'
        ]
        positive = sum(1 for k in risk_keys if int(data.get(k, 1)) == 2)
        age_factor = 1 if int(data.get('age', 0)) > 50 else 0
        probability = min((positive / len(risk_keys)) * 0.85 + age_factor * 0.10, 0.95)

    return probability, risk_label(probability)
