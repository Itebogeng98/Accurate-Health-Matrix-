from django.test import SimpleTestCase
from django.template.loader import render_to_string
from apps.core.wellness_data import prediction_doctor_support


class PredictionDoctorTests(SimpleTestCase):
    def test_matches_two_doctors_for_each_condition(self):
        for disease, specialty in [('lung_cancer', 'Pulmonologist'), ('stroke', 'Neurologist')]:
            support = prediction_doctor_support(disease, 'High Risk')
            self.assertEqual(len(support['doctors']), 2)
            self.assertTrue(support['high_risk'])
            for doctor in support['doctors']:
                self.assertIn(specialty, doctor['specialty'])
            html = render_to_string('core/predictions/doctor_support.html', {'support': support})
            self.assertIn('High-risk result: professional review', html)
            self.assertIn('speciality=' + support['specialty'], html)
            for doctor in support['doctors']:
                self.assertIn(doctor['website'], html)

    def test_low_risk_still_offers_doctors_without_high_risk_message(self):
        support = prediction_doctor_support('lung_cancer', 'Low Risk')
        html = render_to_string('core/predictions/doctor_support.html', {'support': support})
        self.assertFalse(support['high_risk'])
        self.assertIn('Doctors you can contact', html)
        self.assertNotIn('High-risk result: professional review', html)

    def test_unknown_condition_does_not_suggest_unrelated_doctors(self):
        self.assertEqual(prediction_doctor_support('unknown', 'High Risk')['doctors'], [])
