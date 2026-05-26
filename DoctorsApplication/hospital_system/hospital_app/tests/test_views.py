"""
View / template wiring tests:

* The home page must render and group doctors by their three specialties.
* The doctor detail page must split its appointments into past, today and
  future buckets.
* Posting the doctor-detail form must create a new appointment with the
  current doctor as the responsible doctor and an AppointmentAssignment
  record for the same doctor.
"""
from datetime import timedelta

from .base import HospitalTestCase as TestCase
from django.urls import reverse
from django.utils import timezone

from hospital_app.models import (
    Appointment,
    AppointmentAssignment,
)
from .factories import (
    make_appointment,
    make_doctor,
    make_patient,
)


class IndexViewTest(TestCase):
    def setUp(self):
        self.cardio = make_doctor(
            username="cd", full_name="Cardio Doc", specialty="cardiologist"
        )
        self.derma = make_doctor(
            username="dd",
            full_name="Derma Doc",
            specialty="dermatologist",
            email="dd@x.c",
        )
        self.neuro = make_doctor(
            username="nd",
            full_name="Neuro Doc",
            specialty="neurologist",
            email="nd@x.c",
        )

    def test_index_returns_200(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_index_groups_doctors_by_specialty(self):
        resp = self.client.get("/")
        ctx = resp.context
        # Expected three context lists keyed by reasonable names.
        self.assertIn("cardiologists", ctx)
        self.assertIn("dermatologists", ctx)
        self.assertIn("neurologists", ctx)
        self.assertIn(self.cardio, list(ctx["cardiologists"]))
        self.assertIn(self.derma, list(ctx["dermatologists"]))
        self.assertIn(self.neuro, list(ctx["neurologists"]))

    def test_index_doctor_names_appear(self):
        resp = self.client.get("/")
        self.assertContains(resp, "Cardio Doc")
        self.assertContains(resp, "Derma Doc")
        self.assertContains(resp, "Neuro Doc")


class DoctorDetailViewTest(TestCase):
    def setUp(self):
        self.doctor = make_doctor(
            username="ddoc", full_name="Detail Doc", specialty="cardiologist"
        )
        self.patient = make_patient(full_name="Det Pat")

        self.past = make_appointment(
            self.doctor,
            self.patient,
            when_offset_days=-5,
            status="completed",
        )
        # "today" - within the same calendar day as now
        self.today = Appointment.objects.create(
            appointment_type="cardiologist",
            description="today appt",
            status="scheduled",
            datetime=timezone.now().replace(hour=23, minute=30, second=0, microsecond=0)
            if timezone.now().hour < 23
            else timezone.now(),
            patient=self.patient,
            responsible_doctor=self.doctor,
        )
        self.future = make_appointment(
            self.doctor,
            self.patient,
            when_offset_days=5,
            status="scheduled",
        )

    def test_returns_200_for_valid_doctor(self):
        url = reverse("doctor_detail", kwargs={"doctor_id": self.doctor.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_404_for_unknown_doctor(self):
        url = reverse("doctor_detail", kwargs={"doctor_id": 999999})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_context_lists_split_into_past_today_future(self):
        url = reverse("doctor_detail", kwargs={"doctor_id": self.doctor.id})
        resp = self.client.get(url)
        ctx = resp.context

        self.assertIn("past_appointments", ctx)
        self.assertIn("today_appointments", ctx)
        self.assertIn("future_appointments", ctx)

        past_ids = set(a.id for a in ctx["past_appointments"])
        today_ids = set(a.id for a in ctx["today_appointments"])
        future_ids = set(a.id for a in ctx["future_appointments"])

        self.assertIn(self.past.id, past_ids)
        self.assertIn(self.today.id, today_ids)
        self.assertIn(self.future.id, future_ids)

        # Each bucket should NOT leak into the others.
        self.assertNotIn(self.past.id, future_ids)
        self.assertNotIn(self.future.id, past_ids)

    def test_post_creates_appointment_with_correct_doctor_and_type(self):
        another_patient = make_patient(
            full_name="Another", email="ap@x.c"
        )
        url = reverse("doctor_detail", kwargs={"doctor_id": self.doctor.id})
        future_dt = (timezone.now() + timedelta(days=10)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        before = Appointment.objects.count()
        resp = self.client.post(
            url,
            {
                "description": "new test",
                "status": "scheduled",
                "datetime": future_dt,
                "note": "",
                "patient": another_patient.id,
            },
            follow=True,
        )
        # form may render with errors if fields differ - tolerate redirect or
        # 200. The important assertion is that the appointment was created.
        self.assertIn(resp.status_code, (200, 302))

        after = Appointment.objects.count()
        self.assertEqual(
            after,
            before + 1,
            "POST should have created exactly one new appointment",
        )
        new_appt = Appointment.objects.latest("id")
        self.assertEqual(new_appt.responsible_doctor, self.doctor)
        self.assertEqual(new_appt.appointment_type, self.doctor.specialty)

    def test_post_creates_appointment_assignment_for_doctor(self):
        another_patient = make_patient(
            full_name="Another2", email="ap2@x.c"
        )
        url = reverse("doctor_detail", kwargs={"doctor_id": self.doctor.id})
        future_dt = (timezone.now() + timedelta(days=10)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        self.client.post(
            url,
            {
                "description": "another",
                "status": "scheduled",
                "datetime": future_dt,
                "note": "",
                "patient": another_patient.id,
            },
        )
        new_appt = Appointment.objects.filter(patient=another_patient).first()
        self.assertIsNotNone(new_appt)
        self.assertTrue(
            AppointmentAssignment.objects.filter(
                appointment=new_appt, doctor=self.doctor
            ).exists(),
            "responsible doctor should also be added as an "
            "AppointmentAssignment",
        )
