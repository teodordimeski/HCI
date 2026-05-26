"""
Tests for the auto-adjustments described in the exam:

* When an appointment is created with status='completed' but the date is in the
  future, the system flips it to 'scheduled', and vice versa.
* Bonus: when a doctor (as the responsible doctor) already has appointments
  with three or more distinct patients from the same institution, a new
  appointment for a patient from the same institution gets a "High workload"
  note.
* When a patient is removed, their not-yet-started appointments are deleted
  and their in-progress appointments get a "Patient record missing" note.
"""
from datetime import timedelta

from .base import HospitalTestCase as TestCase
from django.utils import timezone

from hospital_app.models import Appointment, Patient
from .factories import make_appointment, make_doctor, make_patient


class AppointmentStatusAutoAdjustTest(TestCase):
    def test_completed_in_future_is_flipped_to_scheduled(self):
        d = make_doctor(username="d1")
        p = make_patient()
        a = make_appointment(
            d, p, status="completed", when_offset_days=5
        )
        a.refresh_from_db()
        self.assertEqual(a.status, "scheduled")

    def test_scheduled_in_past_is_flipped_to_completed(self):
        d = make_doctor(username="d2")
        p = make_patient()
        a = make_appointment(
            d, p, status="scheduled", when_offset_days=-5
        )
        a.refresh_from_db()
        self.assertEqual(a.status, "completed")

    def test_completed_in_past_stays_completed(self):
        d = make_doctor(username="d3")
        p = make_patient()
        a = make_appointment(
            d, p, status="completed", when_offset_days=-2
        )
        a.refresh_from_db()
        self.assertEqual(a.status, "completed")

    def test_scheduled_in_future_stays_scheduled(self):
        d = make_doctor(username="d4")
        p = make_patient()
        a = make_appointment(
            d, p, status="scheduled", when_offset_days=2
        )
        a.refresh_from_db()
        self.assertEqual(a.status, "scheduled")


class HighWorkloadBonusSignalTest(TestCase):
    """
    Reference solution behaviour: the note is set on a *new* appointment when
    the doctor already has appointments with three or more distinct patients
    from the same institution as the new patient.
    """

    def setUp(self):
        self.doctor = make_doctor(username="dbonus")
        self.institution = "ACME Corp"
        # Three existing distinct patients from the same institution, with
        # appointments where the doctor is responsible.
        for i in range(3):
            p = make_patient(
                full_name=f"P{i}",
                email=f"p{i}@x.c",
                institution=self.institution,
            )
            make_appointment(
                self.doctor, p, when_offset_days=2, status="scheduled"
            )

    def test_note_set_when_threshold_reached(self):
        new_patient = make_patient(
            full_name="P_new",
            email="pn@x.c",
            institution=self.institution,
        )
        a = make_appointment(
            self.doctor, new_patient, when_offset_days=3, status="scheduled"
        )
        a.refresh_from_db()
        self.assertTrue(a.note, "expected a non-empty note")
        self.assertIn("High workload", a.note)
        self.assertIn(self.institution, a.note)

    def test_note_not_set_when_under_threshold(self):
        # Different doctor with only one prior patient from this institution.
        d2 = make_doctor(username="dlight")
        p1 = make_patient(
            full_name="X1", email="x1@x.c", institution="OTHER"
        )
        make_appointment(d2, p1, when_offset_days=2, status="scheduled")
        new_patient = make_patient(
            full_name="X2", email="x2@x.c", institution="OTHER"
        )
        a = make_appointment(d2, new_patient, when_offset_days=3)
        a.refresh_from_db()
        self.assertFalse(
            a.note and "High workload" in a.note,
            f"unexpected note set: {a.note!r}",
        )

    def test_note_not_set_for_other_institution(self):
        # Doctor has 3 from ACME but new patient is from a different place.
        new_patient = make_patient(
            full_name="P_other",
            email="po@x.c",
            institution="Other Hospital",
        )
        a = make_appointment(
            self.doctor, new_patient, when_offset_days=3, status="scheduled"
        )
        a.refresh_from_db()
        self.assertFalse(
            a.note and "High workload" in a.note,
            "note should only fire for the same institution",
        )


class PatientDeletionCascadeTest(TestCase):
    """
    Spec:
      * Scheduled appointments are removed when their patient is removed.
      * In-progress appointments are kept and marked with a 'Patient record
        missing - appointment preserved for audit purposes' note.
    """

    def test_scheduled_appointments_are_deleted(self):
        d = make_doctor(username="dpd1")
        p = make_patient()
        a = make_appointment(d, p, when_offset_days=2, status="scheduled")
        appt_id = a.id
        p.delete()
        self.assertFalse(
            Appointment.objects.filter(id=appt_id).exists(),
            "scheduled appointment should have been deleted with the patient",
        )

    def test_in_progress_appointments_are_preserved_with_note(self):
        d = make_doctor(username="dpd2")
        p = make_patient()
        a = make_appointment(d, p, when_offset_days=0, status="in_progress")
        # Sanity: signal must not have flipped status.
        a.refresh_from_db()
        self.assertEqual(a.status, "in_progress")

        p.delete()

        survived = Appointment.objects.filter(id=a.id).first()
        self.assertIsNotNone(
            survived,
            "in-progress appointment must NOT be deleted when its patient is",
        )
        self.assertTrue(survived.note, "expected a non-empty audit note")
        self.assertIn("Patient record missing", survived.note)
