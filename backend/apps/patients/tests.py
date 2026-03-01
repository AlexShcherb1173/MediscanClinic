from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.patients.models import PatientProfile

User = get_user_model()


class PatientProfileModelTests(TestCase):
    def test_create_patient_profile(self):
        user = User.objects.create_user(
            phone="79990000000", password="pass1234", full_name="Alex"
        )
        profile = PatientProfile.objects.create(user=user)

        self.assertEqual(profile.user_id, user.id)
        self.assertIn("PatientProfile", str(profile))
