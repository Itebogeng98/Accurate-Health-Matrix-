"""Dataset sources and schemas shared by downloading, previews and training."""
STROKE_FEATURES = (
    'gender', 'age', 'hypertension', 'heart_disease', 'ever_married',
    'work_type', 'residence_type', 'avg_glucose_level', 'bmi', 'smoking_status',
)
LUNG_FEATURES = (
    'gender', 'age', 'smoking', 'yellow_fingers', 'anxiety', 'peer_pressure',
    'chronic_disease', 'fatigue', 'allergy', 'wheezing', 'alcohol_consuming',
    'coughing', 'shortness_of_breath', 'swallowing_difficulty', 'chest_pain',
)

DATASET_SOURCES = (
    {
        'slug': 'stroke-dataset',
        'name': 'Stroke Prediction',
        'filename': 'healthcare-dataset-stroke-data.csv',
        'archive_filename': 'healthcare-dataset-stroke-data.csv',
        'source': 'Kaggle',
        'kaggle_slug': 'fedesoriano/stroke-prediction-dataset',
        'required_columns': (*STROKE_FEATURES, 'stroke'),
    },
    {
        'slug': 'lung-cancer-dataset',
        'name': 'Lung Cancer Survey',
        'filename': 'lung cancer.csv',
        'archive_filename': 'survey lung cancer.csv',
        'source': 'Kaggle',
        'kaggle_slug': 'mysarahmadbhat/lung-cancer',
        'required_columns': (*LUNG_FEATURES, 'lung_cancer'),
    },
    {
        'slug': 'food-guide-dataset',
        'name': 'Food Nutrition Guide',
        'filename': 'food_nutrition.csv',
        'archive_filename': 'nutrition.csv',
        'source': 'Kaggle',
        'kaggle_slug': 'trolukovich/nutritional-values-for-common-foods-and-products',
        'required_columns': ('name', 'serving_size', 'calories', 'protein', 'fiber', 'sodium'),
    },
)


def normalize_column(name):
    return name.strip().lower().replace(' ', '_')
