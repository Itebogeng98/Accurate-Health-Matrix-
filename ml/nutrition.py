"""Read food reference values with their recorded serving basis and units."""
import csv
from functools import lru_cache
from math import isfinite
from pathlib import Path
import re

DATASET_PATH = Path(__file__).resolve().parent.parent / 'datasets' / 'food_nutrition.csv'
SOURCE_URL = 'https://www.kaggle.com/datasets/trolukovich/nutritional-values-for-common-foods-and-products'


def nutrient_value(value, unit=''):
    """Missing/malformed values remain missing; zero is a valid recorded value."""
    if value is None:
        return None
    match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(mg|g|kcal)?\s*', str(value))
    if not match:
        return None
    number = float(match[1])
    actual_unit = match[2] or unit
    if actual_unit != unit:
        if actual_unit == 'g' and unit == 'mg':
            number *= 1000
        elif actual_unit == 'mg' and unit == 'g':
            number /= 1000
        else:
            return None
    return number if isfinite(number) else None


@lru_cache(maxsize=2)
def _read_foods(path_string, modified, size):
    foods = []
    with Path(path_string).open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        required = {'name', 'serving_size', 'calories', 'protein', 'fiber', 'sodium'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Food dataset is missing required nutrition columns.')
        for row in reader:
            if not row['name'].strip():
                continue
            foods.append({
                'food': row['name'].strip(),
                'serving_size': row['serving_size'],
                'nutrition': {
                    'calories_kcal': nutrient_value(row['calories'], 'kcal'),
                    'protein_g': nutrient_value(row['protein'], 'g'),
                    'fiber_g': nutrient_value(row['fiber'], 'g'),
                    'sodium_mg': nutrient_value(row['sodium'], 'mg'),
                },
                'source_url': SOURCE_URL,
            })
    return tuple(foods)


def get_foods():
    try:
        info = DATASET_PATH.stat()
    except FileNotFoundError:
        return ()
    return _read_foods(str(DATASET_PATH), info.st_mtime_ns, info.st_size)


def search_foods(query='', limit=24):
    foods = get_foods()
    words = query.strip().casefold().split()
    matches = [food for food in foods if all(word in food['food'].casefold() for word in words)]
    return {'foods': matches[:limit], 'match_count': len(matches), 'total_count': len(foods)}


def nutrition_for(name):
    return next((food for food in get_foods() if food['food'].casefold() == name.casefold()), None)
