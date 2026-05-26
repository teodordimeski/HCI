from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from hospital_app.models import Doctor, Patient, Appointment, AppointmentAssignment
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Populate database with dummy data"

    def get_or_create_user(self, username, email, password="test123"):
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if created:
            user.set_password(password)
            user.save()
        return user

    def handle(self, *args, **kwargs):

        u1 = self.get_or_create_user('mike_reynolds', 'mike.reynolds@stlukes.org')
        Doctor.objects.get_or_create(
            user=u1,
            full_name="Dr. Mike Reynolds",
            specialty="cardiologist",
            institution="St. Luke's Medical Center",
            email="mike.reynolds@stlukes.org",
            phone="+1-555-101-0001"
        )

        u2 = self.get_or_create_user('laura_dixon', 'laura.dixon@cedarsheart.com')
        Doctor.objects.get_or_create(
            user=u2,
            full_name="Dr. Laura Dixon",
            specialty="cardiologist",
            institution="Cedars Heart Institute",
            email="laura.dixon@cedarsheart.com",
            phone="+1-555-101-0002"
        )

        u3 = self.get_or_create_user('steven_cho', 'steven.cho@midwestcardio.com')
        Doctor.objects.get_or_create(
            user=u3,
            full_name="Dr. Steven Cho",
            specialty="cardiologist",
            institution="Midwest Cardio Clinic",
            email="steven.cho@midwestcardio.com",
            phone="+1-555-101-0003"
        )

        u4 = self.get_or_create_user('rachel_green', 'rachel.green@skincare.org')
        Doctor.objects.get_or_create(
            user=u4,
            full_name="Dr. Rachel Green",
            specialty="dermatologist",
            institution="SkinCare Clinic NY",
            email="rachel.green@skincare.org",
            phone="+1-555-202-0001"
        )

        u5 = self.get_or_create_user('brian_keller', 'brian.keller@dermachicago.com')
        Doctor.objects.get_or_create(
            user=u5,
            full_name="Dr. Brian Keller",
            specialty="dermatologist",
            institution="Dermacenter Chicago",
            email="brian.keller@dermachicago.com",
            phone="+1-555-202-0002"
        )

        u6 = self.get_or_create_user('alicia_west', 'alicia.west@sunvalley.org')
        Doctor.objects.get_or_create(
            user=u6,
            full_name="Dr. Alicia West",
            specialty="dermatologist",
            institution="Sun Valley Skin Institute",
            email="alicia.west@sunvalley.org",
            phone="+1-555-202-0003"
        )

        # Neurologists
        u7 = self.get_or_create_user('john_marshall', 'john.marshall@neurohealth.org')
        Doctor.objects.get_or_create(
            user=u7,
            full_name="Dr. John Marshall",
            specialty="neurologist",
            institution="NeuroHealth Boston",
            email="john.marshall@neurohealth.org",
            phone="+1-555-303-0001"
        )

        u8 = self.get_or_create_user('emma_brooks', 'emma.brooks@brains.org')
        Doctor.objects.get_or_create(
            user=u8,
            full_name="Dr. Emma Brooks",
            specialty="neurologist",
            institution="Brain & Spine Institute",
            email="emma.brooks@brains.org",
            phone="+1-555-303-0002"
        )

        u9 = self.get_or_create_user('david_zhang', 'david.zhang@pacificneuro.com')
        Doctor.objects.get_or_create(
            user=u9,
            full_name="Dr. David Zhang",
            specialty="neurologist",
            institution="Pacific Neuro Center",
            email="david.zhang@pacificneuro.com",
            phone="+1-555-303-0003"
        )

        doctor = Doctor.objects.get(full_name="Dr. Mike Reynolds")

        patients = [
            Patient.objects.create(
                full_name="Emily Carter",
                birth_date="1985-03-12",
                gender="female",
                email="emily.carter@example.com",
                institution="General City Hospital"
            ),
            Patient.objects.create(
                full_name="James Mitchell",
                birth_date="1978-07-24",
                gender="male",
                email="james.mitchell@example.com",
                institution="General City Hospital"
            ),
            Patient.objects.create(
                full_name="Olivia Barnes",
                birth_date="1992-11-08",
                gender="female",
                email="olivia.barnes@example.com",
                institution="General City Hospital"
            ),
            Patient.objects.create(
                full_name="William Hughes",
                birth_date="1980-01-18",
                gender="male",
                email="william.hughes@example.com",
                institution="General City Hospital"
            ),
            Patient.objects.create(
                full_name="Sophia Reynolds",
                birth_date="1995-06-30",
                gender="female",
                email="sophia.reynolds@example.com",
                institution="General City Hospital"
            )
        ]

        now = timezone.now()
        times = [
            now - timedelta(days=3),
            now - timedelta(days=2),
            now - timedelta(days=1),
            now,
            now + timedelta(days=1),
            now + timedelta(days=2),
        ]

        statuses = ['completed', 'completed', 'completed', 'in_progress', 'scheduled', 'scheduled']

        for i in range(6):
            appointment = Appointment.objects.create(
                appointment_type='cardiologist',
                description=f"Routine check-up for {patients[i % 5].full_name}",
                status=statuses[i],
                datetime=times[i],
                note=f"Autogenerated note for visit {i + 1}",
                patient=patients[i % 5],
                responsible_doctor=doctor
            )

            AppointmentAssignment.objects.create(appointment=appointment, doctor=doctor)

        self.stdout.write(self.style.SUCCESS("Data successfully inserted."))
