"""
Admin-panel rule tests. Exercises the methods on the registered ModelAdmin
classes for Doctor / Patient / Appointment.
"""
from datetime import timedelta

from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.test import RequestFactory

from .base import HospitalTestCase as TestCase
from django.utils import timezone

from hospital_app.models import (
    Appointment,
    AppointmentAssignment,
    Doctor,
    Patient,
)
from .factories import (
    assign_doctor,
    make_appointment,
    make_doctor,
    make_patient,
    make_user,
)


def _admin_for(model):
    """Return the ModelAdmin instance registered for `model`."""
    return site._registry.get(model)


def _request(user):
    rf = RequestFactory()
    req = rf.get("/admin/")
    req.user = user
    return req


class AdminRegistrationTest(TestCase):
    def test_doctor_registered(self):
        self.assertIsNotNone(_admin_for(Doctor))

    def test_patient_registered(self):
        self.assertIsNotNone(_admin_for(Patient))

    def test_appointment_registered(self):
        self.assertIsNotNone(_admin_for(Appointment))


class DoctorAddPermissionTest(TestCase):
    def test_only_superuser_can_add_doctor(self):
        admin = _admin_for(Doctor)
        super_user = make_user("super1", is_superuser=True)
        normal_user = make_user("normal1", is_superuser=False)
        self.assertTrue(admin.has_add_permission(_request(super_user)))
        self.assertFalse(admin.has_add_permission(_request(normal_user)))


class PatientAddPermissionTest(TestCase):
    def test_only_superuser_can_add_patient(self):
        admin = _admin_for(Patient)
        super_user = make_user("super2", is_superuser=True)
        normal_user = make_user("normal2", is_superuser=False)
        self.assertTrue(admin.has_add_permission(_request(super_user)))
        self.assertFalse(admin.has_add_permission(_request(normal_user)))


class AppointmentAddPermissionTest(TestCase):
    def test_doctor_or_superuser_can_add(self):
        admin = _admin_for(Appointment)
        super_user = make_user("supA", is_superuser=True)
        doctor = make_doctor(username="docA")
        non_doctor = make_user("nondocA", is_superuser=False)

        self.assertTrue(admin.has_add_permission(_request(super_user)))
        self.assertTrue(admin.has_add_permission(_request(doctor.user)))
        self.assertFalse(admin.has_add_permission(_request(non_doctor)))


class AppointmentChangePermissionTest(TestCase):
    def setUp(self):
        self.admin = _admin_for(Appointment)
        self.super = make_user("supC", is_superuser=True)
        self.responsible = make_doctor(username="docC1")
        self.other = make_doctor(username="docC2", email="c2@x.c")
        self.patient = make_patient()
        self.appt = make_appointment(
            self.responsible, self.patient, when_offset_days=2
        )

    def test_superuser_can_change_anything(self):
        self.assertTrue(
            self.admin.has_change_permission(
                _request(self.super), self.appt
            )
        )

    def test_responsible_doctor_can_change(self):
        self.assertTrue(
            self.admin.has_change_permission(
                _request(self.responsible.user), self.appt
            )
        )

    def test_other_doctor_cannot_change(self):
        self.assertFalse(
            self.admin.has_change_permission(
                _request(self.other.user), self.appt
            )
        )


class AppointmentDeletePermissionTest(TestCase):
    def setUp(self):
        self.admin = _admin_for(Appointment)
        self.super = make_user("supD", is_superuser=True)
        self.doctor = make_doctor(username="docD")
        self.patient = make_patient()

    def test_scheduled_appointment_can_be_deleted(self):
        a = make_appointment(
            self.doctor, self.patient, when_offset_days=2, status="scheduled"
        )
        self.assertTrue(
            self.admin.has_delete_permission(_request(self.super), a)
        )

    def test_in_progress_cannot_be_deleted(self):
        a = make_appointment(
            self.doctor,
            self.patient,
            when_offset_days=0,
            status="in_progress",
        )
        # Even the superuser is denied - the appointment has started.
        self.assertFalse(
            self.admin.has_delete_permission(_request(self.super), a)
        )

    def test_completed_cannot_be_deleted(self):
        a = make_appointment(
            self.doctor,
            self.patient,
            when_offset_days=-5,
            status="completed",
        )
        self.assertFalse(
            self.admin.has_delete_permission(_request(self.super), a)
        )


class AppointmentSaveModelTest(TestCase):
    def setUp(self):
        self.admin = _admin_for(Appointment)
        self.doctor = make_doctor(username="docSM")
        self.patient = make_patient()

    def test_responsible_doctor_auto_set_to_current_doctor_on_create(self):
        # Build an unsaved Appointment with NO responsible_doctor set.
        appt = Appointment(
            appointment_type="cardiologist",
            description="x",
            status="scheduled",
            datetime=timezone.now() + timedelta(days=2),
            patient=self.patient,
        )
        self.admin.save_model(
            _request(self.doctor.user), appt, form=None, change=False
        )
        appt.refresh_from_db()
        self.assertEqual(appt.responsible_doctor, self.doctor)

    def test_in_progress_to_completed_increments_counter(self):
        a = make_appointment(
            self.doctor,
            self.patient,
            when_offset_days=-2,
            status="in_progress",
        )
        before = self.doctor.completed_appointments
        a.status = "completed"
        self.admin.save_model(
            _request(self.doctor.user), a, form=None, change=True
        )
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.completed_appointments, before + 1)


class AppointmentQuerysetVisibilityTest(TestCase):
    def setUp(self):
        self.super = make_user("supQ", is_superuser=True)
        self.doctor = make_doctor(username="docQ")
        self.other = make_doctor(username="docQ2", email="q2@x.c")
        self.p = make_patient()

        self.own = make_appointment(
            self.doctor, self.p, when_offset_days=2
        )
        self.assisted = make_appointment(
            self.other, self.p, when_offset_days=2
        )
        assign_doctor(self.assisted, self.doctor)
        self.unrelated = make_appointment(
            self.other,
            make_patient(full_name="Q", email="q@x.c"),
            when_offset_days=2,
        )

    def test_superuser_sees_all_appointments(self):
        admin = _admin_for(Appointment)
        qs = admin.get_queryset(_request(self.super))
        self.assertEqual(qs.count(), 3)

    def test_doctor_sees_only_own_and_assigned(self):
        admin = _admin_for(Appointment)
        qs = admin.get_queryset(_request(self.doctor.user))
        ids = set(qs.values_list("id", flat=True))
        self.assertIn(self.own.id, ids)
        self.assertIn(self.assisted.id, ids)
        self.assertNotIn(self.unrelated.id, ids)
