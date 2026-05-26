"""
Structural tests for the four models defined in the exercise.

The exam description fixes the *names* and *types* of the fields, not the exact
Django field options (e.g. max_length). These tests only verify what the spec
demands.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models as dj_models
from .base import HospitalTestCase as TestCase
from django.utils import timezone

from hospital_app.models import (
    Appointment,
    AppointmentAssignment,
    Doctor,
    Patient,
)


def _field(model, name):
    return model._meta.get_field(name)


class DoctorModelStructureTest(TestCase):
    def test_has_user_one_to_one_to_auth_user(self):
        f = _field(Doctor, "user")
        self.assertIsInstance(f, dj_models.OneToOneField)
        self.assertIs(f.related_model, User)

    def test_has_full_name_charfield(self):
        f = _field(Doctor, "full_name")
        self.assertIsInstance(f, dj_models.CharField)

    def test_specialty_choices_cover_three_specialties(self):
        f = _field(Doctor, "specialty")
        self.assertIsInstance(f, dj_models.CharField)
        keys = {k for k, _ in (f.choices or [])}
        self.assertIn("cardiologist", keys)
        self.assertIn("dermatologist", keys)
        self.assertIn("neurologist", keys)

    def test_has_image_field(self):
        f = _field(Doctor, "image")
        self.assertIsInstance(f, dj_models.ImageField)

    def test_has_institution_charfield(self):
        f = _field(Doctor, "institution")
        self.assertIsInstance(f, dj_models.CharField)

    def test_has_completed_appointments_integer_default_zero(self):
        f = _field(Doctor, "completed_appointments")
        self.assertIsInstance(
            f, (dj_models.PositiveIntegerField, dj_models.IntegerField)
        )
        self.assertEqual(f.default, 0)

    def test_has_email_field(self):
        f = _field(Doctor, "email")
        self.assertIsInstance(f, dj_models.EmailField)

    def test_has_phone_charfield(self):
        f = _field(Doctor, "phone")
        self.assertIsInstance(f, dj_models.CharField)

    def test_create_doctor_persists(self):
        u = User.objects.create_user(username="dr1", password="x")
        d = Doctor.objects.create(
            user=u,
            full_name="Dr. Smith",
            specialty="cardiologist",
            institution="GH",
            email="a@b.c",
            phone="070",
        )
        self.assertEqual(Doctor.objects.count(), 1)
        self.assertEqual(d.completed_appointments, 0)


class PatientModelStructureTest(TestCase):
    def test_has_full_name_charfield(self):
        f = _field(Patient, "full_name")
        self.assertIsInstance(f, dj_models.CharField)

    def test_has_birth_date_field(self):
        f = _field(Patient, "birth_date")
        self.assertIsInstance(f, dj_models.DateField)

    def test_gender_choices_cover_at_least_male_female(self):
        f = _field(Patient, "gender")
        self.assertIsInstance(f, dj_models.CharField)
        keys = {k for k, _ in (f.choices or [])}
        self.assertIn("male", keys)
        self.assertIn("female", keys)

    def test_has_email_field(self):
        f = _field(Patient, "email")
        self.assertIsInstance(f, dj_models.EmailField)

    def test_has_institution_field_for_bonus(self):
        # Required so the "3+ patients from same institution" bonus signal
        # has somewhere to read the institution from.
        f = _field(Patient, "institution")
        self.assertIsInstance(f, dj_models.CharField)


class AppointmentModelStructureTest(TestCase):
    def test_appointment_type_choices_cover_three_types(self):
        f = _field(Appointment, "appointment_type")
        self.assertIsInstance(f, dj_models.CharField)
        keys = {k for k, _ in (f.choices or [])}
        # Accept either the {specialty}/{specialty} convention or
        # cardiology/dermatology/neurology naming.
        self.assertEqual(len(keys), 3)

    def test_has_description_textfield(self):
        f = _field(Appointment, "description")
        self.assertIsInstance(f, (dj_models.TextField, dj_models.CharField))

    def test_status_choices_and_default_scheduled(self):
        f = _field(Appointment, "status")
        keys = {k for k, _ in (f.choices or [])}
        self.assertIn("scheduled", keys)
        self.assertIn("in_progress", keys)
        self.assertIn("completed", keys)
        self.assertEqual(f.default, "scheduled")

    def test_has_datetime_field(self):
        f = _field(Appointment, "datetime")
        self.assertIsInstance(f, dj_models.DateTimeField)

    def test_note_is_optional_text(self):
        f = _field(Appointment, "note")
        self.assertTrue(f.blank)
        self.assertTrue(f.null)

    def test_patient_foreign_key(self):
        f = _field(Appointment, "patient")
        self.assertIsInstance(f, dj_models.ForeignKey)
        self.assertIs(f.related_model, Patient)

    def test_responsible_doctor_foreign_key(self):
        f = _field(Appointment, "responsible_doctor")
        self.assertIsInstance(f, dj_models.ForeignKey)
        self.assertIs(f.related_model, Doctor)


class AppointmentAssignmentModelStructureTest(TestCase):
    def test_appointment_foreign_key(self):
        f = _field(AppointmentAssignment, "appointment")
        self.assertIsInstance(f, dj_models.ForeignKey)
        self.assertIs(f.related_model, Appointment)

    def test_doctor_foreign_key(self):
        f = _field(AppointmentAssignment, "doctor")
        self.assertIsInstance(f, dj_models.ForeignKey)
        self.assertIs(f.related_model, Doctor)

    def test_unique_together_appointment_doctor(self):
        # Either a UniqueConstraint or unique_together is acceptable.
        unique_pairs = set()
        for ut in AppointmentAssignment._meta.unique_together:
            unique_pairs.add(tuple(sorted(ut)))
        for c in AppointmentAssignment._meta.constraints:
            if isinstance(c, dj_models.UniqueConstraint):
                unique_pairs.add(tuple(sorted(c.fields)))
        self.assertIn(("appointment", "doctor"), unique_pairs)

    def test_create_assignment_persists(self):
        u = User.objects.create_user(username="dr2", password="x")
        d = Doctor.objects.create(
            user=u,
            full_name="Dr. A",
            specialty="cardiologist",
            institution="X",
            email="a@b.c",
            phone="07",
        )
        p = Patient.objects.create(
            full_name="P",
            birth_date=timezone.now().date(),
            gender="male",
            email="p@x.c",
            institution="Y",
        )
        a = Appointment.objects.create(
            appointment_type="cardiologist",
            description="ok",
            status="scheduled",
            datetime=timezone.now() + timedelta(days=1),
            patient=p,
            responsible_doctor=d,
        )
        AppointmentAssignment.objects.create(appointment=a, doctor=d)
        self.assertEqual(AppointmentAssignment.objects.count(), 1)
