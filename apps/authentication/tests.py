from django.test import SimpleTestCase
from apps.authentication.serializers import SignupSerializer


class SignupPasswordTests(SimpleTestCase):
    def validate_password(self, password, **details):
        return SignupSerializer().validate(dict(password=password, confirm_password=password, email='sam@example.com', first_name='Sam', last_name='Example', **details))

    def test_rejects_weak_passwords(self):
        from rest_framework.serializers import ValidationError
        for password in ('short', '1234567890123456', 'password123456', 'sam@example.com'):
            with self.subTest(password=password), self.assertRaises(ValidationError):
                self.validate_password(password)

    def test_accepts_long_passphrase_and_preserves_spaces(self):
        password = '  Orchard! river 72 lantern  '
        self.assertEqual(self.validate_password(password)['password'], password)
        field = SignupSerializer().fields['password']
        self.assertEqual(field.run_validation(password), password)


    def test_rejects_missing_or_mismatched_confirmation(self):
        from rest_framework.serializers import ValidationError
        for confirmation in (None, 'Different! phrase 123'):
            with self.subTest(confirmation=confirmation), self.assertRaises(ValidationError):
                SignupSerializer().validate(dict(password='Orchard! river 72 lantern', confirm_password=confirmation))

    def test_confirmation_is_required_and_write_only(self):
        field = SignupSerializer().fields['confirm_password']
        self.assertTrue(field.required)
        self.assertTrue(field.write_only)

    def test_confirmation_is_removed_before_user_creation(self):
        data = self.validate_password('Orchard! river 72 lantern')
        self.assertNotIn('confirm_password', data)

    def test_accepts_six_character_password(self):
        password = 'Q7!vZ2'
        self.assertEqual(self.validate_password(password)['password'], password)
        self.assertEqual(SignupSerializer().fields['password'].run_validation(password), password)
