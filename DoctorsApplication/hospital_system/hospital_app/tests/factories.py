"""
Helpers for building test data. Centralised so any change to model field names
only needs to be reflected here.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from hospital_app.models import (
    Appointment,
    AppointmentAssignment,
    Doctor,
    Patient,
)


# Smallest valid GIF (single transparent pixel). Used as a placeholder for
# the Doctor.image ImageField so templates that read ``doctor.image.url`` do
# not crash during render.
_SMALLEST_GIF = (
    b"GIF87a\x01\x00\x01\x00\x80\x01\x00\xff\xff\xff\x00\x00\x00,"
    b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"
)


def make_image(name="test.gif"):
    return SimpleUploadedFile(name, _SMALLEST_GIF, content_type="image/gif")


def make_user(username, password="pw12345!", is_superuser=False, is_staff=True):
    user = User.objects.create_user(
        username=username, password=password, is_staff=is_staff
    )
    if is_superuser:
        user.is_superuser = True
        user.is_staff = True
        user.save()
    return user


def make_doctor(
    username="doc",
    full_name="Dr. Test",
    specialty="cardiologist",
    institution="General Hospital",
    email="doc@example.com",
    phone="070000000",
    completed_appointments=0,
    user=None,
    with_image=True,
):
    if user is None:
        user = make_user(username, is_superuser=False, is_staff=True)
    kwargs = dict(
        user=user,
        full_name=full_name,
        specialty=specialty,
        institution=institution,
        email=email,
        phone=phone,
        completed_appointments=completed_appointments,
    )
    if with_image:
        kwargs["image"] = make_image(f"{username}.gif")
    return Doctor.objects.create(**kwargs)


def make_patient(
    full_name="Patient X",
    institution="ACME Corp",
    gender="male",
    email="patient@example.com",
    birth_date=None,
):
    if birth_date is None:
        birth_date = timezone.now().date() - timedelta(days=365 * 30)
    return Patient.objects.create(
        full_name=full_name,
        birth_date=birth_date,
        gender=gender,
        email=email,
        institution=institution,
    )


def make_appointment(
    doctor,
    patient,
    appointment_type=None,
    status="scheduled",
    when_offset_days=1,
    description="Regular check",
    note=None,
):
    when = timezone.now() + timedelta(days=when_offset_days)
    if appointment_type is None:
        appointment_type = doctor.specialty
    appt = Appointment(
        appointment_type=appointment_type,
        description=description,
        status=status,
        datetime=when,
        note=note,
        patient=patient,
        responsible_doctor=doctor,
    )
    appt.save()
    return appt


def assign_doctor(appointment, doctor):
    return AppointmentAssignment.objects.create(
        appointment=appointment, doctor=doctor
    )
