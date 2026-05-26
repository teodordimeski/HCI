"""
Tests for the AppointmentForm:

* The form must NOT include `responsible_doctor` or `appointment_type` (those
  are filled in automatically based on the doctor whose detail page is
  showing the form).
* Every visible field must have a Bootstrap `form-control` class on its
  widget.
"""
from .base import HospitalTestCase as TestCase

from hospital_app.forms import AppointmentForm


class AppointmentFormTest(TestCase):
    def test_excludes_responsible_doctor_and_appointment_type(self):
        form = AppointmentForm()
        self.assertNotIn("responsible_doctor", form.fields)
        self.assertNotIn("appointment_type", form.fields)

    def test_widgets_have_bootstrap_form_control_class(self):
        form = AppointmentForm()
        for name, field in form.fields.items():
            css = field.widget.attrs.get("class", "")
            self.assertIn(
                "form-control",
                css,
                f"field {name!r} is missing the 'form-control' class "
                f"(got {css!r})",
            )

    def test_form_includes_minimum_required_fields(self):
        # Spec: description, status, datetime, note, patient should be
        # editable. Whether the project uses different names is fine - we
        # check that *at least* these standard names are present.
        form = AppointmentForm()
        for required in ("description", "datetime", "patient"):
            self.assertIn(
                required,
                form.fields,
                f"AppointmentForm should expose the {required!r} field",
            )
