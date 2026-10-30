from .nutrition import nutrition_for

# Exact reference entries avoid matching a prepared dish to a raw ingredient.
FOOD_REFERENCES = {
    'Oats': 'Oats',
    'Spinach': 'Spinach, raw',
    'Apples': 'Apples, with skin, raw',
    'Avocado': 'Avocados, all commercial varieties, raw',
    'Brown rice': 'Rice, cooked, long-grain, brown',
    'Beans': 'Beans, without salt, boiled, cooked, mature seeds, black',
    'Banana': 'Bananas, raw',
    'Broccoli': 'Broccoli, raw',
    'Carrots': 'Carrots, raw',
    'Berries': 'Blueberries, raw',
    'Green tea': 'Beverages, regular, brewed, green, tea',
}


def recommend_diet(disease, risk_level):
    common = [
        {'food':'Oats', 'benefit':'Supports cholesterol control and heart health'},
        {'food':'Spinach', 'benefit':'Rich in vitamins, minerals and antioxidants'},
        {'food':'Apples', 'benefit':'High fibre fruit for daily healthy eating'},
    ]
    if disease == 'stroke':
        items = [
            {'food':'Avocado', 'benefit':'Healthy fats that support heart health'},
            {'food':'Brown rice', 'benefit':'Whole grain energy with fibre'},
            {'food':'Beans', 'benefit':'Plant protein and fibre'},
            {'food':'Banana', 'benefit':'Potassium-rich option'},
        ]
    else:
        items = [
            {'food':'Broccoli', 'benefit':'Cruciferous vegetable with antioxidants'},
            {'food':'Carrots', 'benefit':'Beta-carotene rich vegetable'},
            {'food':'Berries', 'benefit':'Antioxidant-rich fruit'},
            {'food':'Green tea', 'benefit':'Supports antioxidant intake'},
        ]
    selected = items + common if risk_level == 'High Risk' else common + items[:2]
    enriched = []
    for item in selected:
        reference = nutrition_for(FOOD_REFERENCES[item['food']])
        enriched.append({
            **item,
            **({
                'nutrition': reference['nutrition'],
                'serving_size': reference['serving_size'],
                'reference_food': reference['food'],
                'source_url': reference['source_url'],
            } if reference else {}),
        })
    return enriched
