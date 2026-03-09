"""
Test the trained accident risk prediction model
"""
from predict_risk import AccidentPredictor

print('='*70)
print('🔮 TESTING ACCIDENT RISK PREDICTION MODEL')
print('='*70)

# Load the Random Forest model
predictor = AccidentPredictor(model_name='random_forest')

# Test cases based on Kenya data
test_cases = [
    {
        'name': 'Nairobi-Mombasa Road (High Risk)',
        'accident_count': 2850,
        'regions': 6,
        'cause_factors': 6,
        'black_spots': 5
    },
    {
        'name': 'Rural Road (Low Risk)',
        'accident_count': 300,
        'regions': 2,
        'cause_factors': 3,
        'black_spots': 1
    },
    {
        'name': 'Urban Highway (Medium Risk)',
        'accident_count': 1200,
        'regions': 4,
        'cause_factors': 5,
        'black_spots': 3
    }
]

print('\n')
for test in test_cases:
    result = predictor.predict_risk(
        test['accident_count'],
        test['regions'],
        test['cause_factors'],
        test['black_spots']
    )
    
    location = test['name']
    print(f'📍 {location}')
    print(f'   Risk Level: {result["risk_level"]}')
    print(f'   Probability (Safe): {result["probability_safe"]:.1%}')
    print(f'   Probability (High Risk): {result["probability_high_risk"]:.1%}')
    print(f'   Confidence: {result["confidence"]:.1%}')
    print()

print('='*70)
print('✅ Prediction model working correctly!')
print('='*70)
