"""
A friendlier wrapper around `manage.py test` for the hospital_system
exercise.

Runs the same test suite as `python manage.py test hospital_app.tests`,
but groups results by category, runs a pre-flight check for the kind of
problem that prevents *any* test from even starting, and for every failing
test prints the underlying requirement plus a "where to look" pointer.

Usage:
    python manage.py check_solution
    python manage.py check_solution --no-color
"""
import importlib
import io
import os
import sys
import traceback
import unittest

from django.core.management.base import BaseCommand


# ---------------------------------------------------------------------------
# Categorisation
# ---------------------------------------------------------------------------

# (Display name, dotted-path to test module, default "where" pointer)
CATEGORIES = [
    ("Models",  "hospital_app.tests.test_models",  "hospital_app/models.py"),
    ("Forms",   "hospital_app.tests.test_forms",   "hospital_app/forms.py"),
    ("URLs",    "hospital_app.tests.test_urls",    "hospital_system/urls.py"),
    ("Signals", "hospital_app.tests.test_signals", "hospital_app/signals.py"),
    ("Admin",   "hospital_app.tests.test_admin",   "hospital_app/admin.py"),
    ("Views",   "hospital_app.tests.test_views",   "hospital_app/views.py"),
]


# Per-test metadata: { "ClassName.test_method": (requirement, where) }
TEST_HINTS = {
    # --- Doctor model -------------------------------------------------------
    "DoctorModelStructureTest.test_has_user_one_to_one_to_auth_user": (
        "Doctor must be linked to Django's built-in User via a "
        "OneToOneField",
        "Doctor.user in hospital_app/models.py",
    ),
    "DoctorModelStructureTest.test_has_full_name_charfield": (
        "Doctor must expose a `full_name` CharField",
        "Doctor.full_name in hospital_app/models.py",
    ),
    "DoctorModelStructureTest.test_specialty_choices_cover_three_specialties": (
        "Doctor.specialty must have choices for 'cardiologist', "
        "'dermatologist' and 'neurologist'",
        "Doctor.specialty + SPECIALTY_CHOICES in hospital_app/models.py",
    ),
    "DoctorModelStructureTest.test_has_image_field": (
        "Doctor must have an `image` ImageField",
        "Doctor.image in hospital_app/models.py",
    ),
    "DoctorModelStructureTest.test_has_institution_charfield": (
        "Doctor must expose an `institution` CharField",
        "Doctor.institution in hospital_app/models.py",
    ),
    "DoctorModelStructureTest.test_has_completed_appointments_integer_default_zero": (
        "Doctor.completed_appointments must be an integer field defaulting "
        "to 0",
        "Doctor.completed_appointments in hospital_app/models.py",
    ),
    "DoctorModelStructureTest.test_has_email_field": (
        "Doctor must expose an EmailField named `email`",
        "Doctor.email in hospital_app/models.py",
    ),
    "DoctorModelStructureTest.test_has_phone_charfield": (
        "Doctor must expose a CharField named `phone`",
        "Doctor.phone in hospital_app/models.py",
    ),
    "DoctorModelStructureTest.test_create_doctor_persists": (
        "A Doctor object must be storable via Doctor.objects.create(...)",
        "the Doctor model + a migration in hospital_app/migrations/",
    ),

    # --- Patient model ------------------------------------------------------
    "PatientModelStructureTest.test_has_full_name_charfield": (
        "Patient must expose a `full_name` CharField",
        "Patient.full_name in hospital_app/models.py",
    ),
    "PatientModelStructureTest.test_has_birth_date_field": (
        "Patient must expose a DateField named `birth_date`",
        "Patient.birth_date in hospital_app/models.py "
        "(make sure it is NOT auto_now_add - a real birth date must be "
        "settable by the admin)",
    ),
    "PatientModelStructureTest.test_gender_choices_cover_at_least_male_female": (
        "Patient.gender must have at least 'male' and 'female' as choices",
        "Patient.gender + GENDER_CHOICES in hospital_app/models.py",
    ),
    "PatientModelStructureTest.test_has_email_field": (
        "Patient must expose an EmailField named `email`",
        "Patient.email in hospital_app/models.py",
    ),
    "PatientModelStructureTest.test_has_institution_field_for_bonus": (
        "Patient must expose an `institution` field - the bonus signal "
        "reads it",
        "Patient.institution in hospital_app/models.py",
    ),

    # --- Appointment model --------------------------------------------------
    "AppointmentModelStructureTest.test_appointment_type_choices_cover_three_types": (
        "Appointment.appointment_type must have exactly three choices "
        "matching the three specialties",
        "Appointment.appointment_type in hospital_app/models.py",
    ),
    "AppointmentModelStructureTest.test_has_description_textfield": (
        "Appointment must expose a `description` text/char field",
        "Appointment.description in hospital_app/models.py",
    ),
    "AppointmentModelStructureTest.test_status_choices_and_default_scheduled": (
        "Appointment.status must have choices 'scheduled', 'in_progress', "
        "'completed' and default to 'scheduled'",
        "Appointment.status + STATUS_CHOICES in hospital_app/models.py",
    ),
    "AppointmentModelStructureTest.test_has_datetime_field": (
        "Appointment must expose a `datetime` DateTimeField that the user "
        "can set (NOT auto_now / auto_now_add)",
        "Appointment.datetime in hospital_app/models.py",
    ),
    "AppointmentModelStructureTest.test_note_is_optional_text": (
        "Appointment.note must be a text/char field with blank=True and "
        "null=True",
        "Appointment.note in hospital_app/models.py",
    ),
    "AppointmentModelStructureTest.test_patient_foreign_key": (
        "Appointment must hold a ForeignKey to Patient",
        "Appointment.patient in hospital_app/models.py",
    ),
    "AppointmentModelStructureTest.test_responsible_doctor_foreign_key": (
        "Appointment must hold a ForeignKey to Doctor as "
        "`responsible_doctor`",
        "Appointment.responsible_doctor in hospital_app/models.py",
    ),

    # --- AppointmentAssignment ---------------------------------------------
    "AppointmentAssignmentModelStructureTest.test_appointment_foreign_key": (
        "AppointmentAssignment must hold a ForeignKey to Appointment",
        "AppointmentAssignment.appointment in hospital_app/models.py",
    ),
    "AppointmentAssignmentModelStructureTest.test_doctor_foreign_key": (
        "AppointmentAssignment must hold a ForeignKey to Doctor",
        "AppointmentAssignment.doctor in hospital_app/models.py",
    ),
    "AppointmentAssignmentModelStructureTest.test_unique_together_appointment_doctor": (
        "(appointment, doctor) must be unique together - the same doctor "
        "cannot be assisting twice on the same appointment",
        "AppointmentAssignment.Meta.unique_together / UniqueConstraint",
    ),
    "AppointmentAssignmentModelStructureTest.test_create_assignment_persists": (
        "AppointmentAssignment must be storable via .objects.create()",
        "AppointmentAssignment + a migration",
    ),

    # --- Signals: status auto-adjust ---------------------------------------
    "AppointmentStatusAutoAdjustTest.test_completed_in_future_is_flipped_to_scheduled": (
        "pre_save: status='completed' + future datetime must flip to "
        "'scheduled'",
        "appointment_status_adjustment in hospital_app/signals.py",
    ),
    "AppointmentStatusAutoAdjustTest.test_scheduled_in_past_is_flipped_to_completed": (
        "pre_save: status='scheduled' + past datetime must flip to "
        "'completed'",
        "appointment_status_adjustment in hospital_app/signals.py",
    ),
    "AppointmentStatusAutoAdjustTest.test_completed_in_past_stays_completed": (
        "pre_save must NOT touch status='completed' with a past datetime",
        "appointment_status_adjustment in hospital_app/signals.py - "
        "check the conditions are not too broad",
    ),
    "AppointmentStatusAutoAdjustTest.test_scheduled_in_future_stays_scheduled": (
        "pre_save must NOT touch status='scheduled' with a future datetime",
        "appointment_status_adjustment in hospital_app/signals.py - "
        "check the conditions are not too broad",
    ),

    # --- Signals: high-workload bonus --------------------------------------
    "HighWorkloadBonusSignalTest.test_note_set_when_threshold_reached": (
        "Bonus: when a doctor already has 3+ distinct patients from the "
        "same institution as the new patient, the new appointment's `note` "
        "must contain 'High workload with patients from institution X'",
        "the bonus block of appointment_status_adjustment in "
        "hospital_app/signals.py",
    ),
    "HighWorkloadBonusSignalTest.test_note_not_set_when_under_threshold": (
        "Bonus note must NOT fire when the doctor has fewer than 3 "
        "patients from the same institution",
        "the bonus block of appointment_status_adjustment - check the "
        "threshold and that you compare DISTINCT patients",
    ),
    "HighWorkloadBonusSignalTest.test_note_not_set_for_other_institution": (
        "Bonus note must be tied to the SAME institution as the new "
        "patient, not just to the doctor's overall workload",
        "the bonus block - your filter must include "
        "patient__institution=instance.patient.institution",
    ),

    # --- Signals: patient deletion -----------------------------------------
    "PatientDeletionCascadeTest.test_scheduled_appointments_are_deleted": (
        "When a patient is deleted, every still-scheduled appointment of "
        "theirs must be deleted",
        "cleanup_appointments_*_patient_deletion in hospital_app/signals.py",
    ),
    "PatientDeletionCascadeTest.test_in_progress_appointments_are_preserved_with_note": (
        "When a patient is deleted, in-progress appointments must SURVIVE "
        "with a 'Patient record missing ... audit purposes' note set",
        "use pre_delete (NOT post_delete) and consider Appointment.patient "
        "on_delete=SET_NULL with null=True, otherwise CASCADE will wipe "
        "the in-progress rows before your signal can save them",
    ),

    # --- Admin: registration -----------------------------------------------
    "AdminRegistrationTest.test_doctor_registered": (
        "Doctor must be registered in the admin",
        "admin.site.register(Doctor, ...) in hospital_app/admin.py",
    ),
    "AdminRegistrationTest.test_patient_registered": (
        "Patient must be registered in the admin",
        "admin.site.register(Patient, ...) in hospital_app/admin.py",
    ),
    "AdminRegistrationTest.test_appointment_registered": (
        "Appointment must be registered in the admin",
        "admin.site.register(Appointment, ...) in hospital_app/admin.py",
    ),

    # --- Admin: add permissions --------------------------------------------
    "DoctorAddPermissionTest.test_only_superuser_can_add_doctor": (
        "Only superusers may add Doctor objects via the admin",
        "DoctorAdmin.has_add_permission in hospital_app/admin.py",
    ),
    "PatientAddPermissionTest.test_only_superuser_can_add_patient": (
        "Only superusers may add Patient objects via the admin",
        "PatientAdmin.has_add_permission in hospital_app/admin.py",
    ),
    "AppointmentAddPermissionTest.test_doctor_or_superuser_can_add": (
        "Any user that has a linked Doctor record (or is a superuser) "
        "must be able to add appointments",
        "AppointmentAdmin.has_add_permission in hospital_app/admin.py",
    ),

    # --- Admin: change permissions -----------------------------------------
    "AppointmentChangePermissionTest.test_superuser_can_change_anything": (
        "Superusers may edit any appointment",
        "AppointmentAdmin.has_change_permission in hospital_app/admin.py",
    ),
    "AppointmentChangePermissionTest.test_responsible_doctor_can_change": (
        "The responsible doctor must be able to edit their own "
        "appointment",
        "AppointmentAdmin.has_change_permission in hospital_app/admin.py",
    ),
    "AppointmentChangePermissionTest.test_other_doctor_cannot_change": (
        "A doctor must NOT be able to edit an appointment they are not "
        "responsible for",
        "AppointmentAdmin.has_change_permission in hospital_app/admin.py",
    ),

    # --- Admin: delete permissions -----------------------------------------
    "AppointmentDeletePermissionTest.test_scheduled_appointment_can_be_deleted": (
        "A 'scheduled' (not yet started) appointment must be deletable",
        "AppointmentAdmin.has_delete_permission in hospital_app/admin.py",
    ),
    "AppointmentDeletePermissionTest.test_in_progress_cannot_be_deleted": (
        "An 'in_progress' appointment must NOT be deletable - even by a "
        "superuser",
        "AppointmentAdmin.has_delete_permission in hospital_app/admin.py",
    ),
    "AppointmentDeletePermissionTest.test_completed_cannot_be_deleted": (
        "A 'completed' appointment must NOT be deletable",
        "AppointmentAdmin.has_delete_permission in hospital_app/admin.py",
    ),

    # --- Admin: save_model -------------------------------------------------
    "AppointmentSaveModelTest.test_responsible_doctor_auto_set_to_current_doctor_on_create": (
        "When a doctor creates a new appointment, save_model must set "
        "responsible_doctor to the Doctor record linked to request.user",
        "AppointmentAdmin.save_model in hospital_app/admin.py "
        "(the `if not change:` branch)",
    ),
    "AppointmentSaveModelTest.test_in_progress_to_completed_increments_counter": (
        "When the status transitions from 'in_progress' to 'completed', "
        "the responsible doctor's completed_appointments counter must be "
        "incremented by 1",
        "AppointmentAdmin.save_model in hospital_app/admin.py "
        "(the `else:` / change branch - compare the OLD status from the "
        "DB to the new one)",
    ),

    # --- Admin: appointment queryset ---------------------------------------
    "AppointmentQuerysetVisibilityTest.test_superuser_sees_all_appointments": (
        "Superusers must see all appointments in the changelist",
        "AppointmentAdmin.get_queryset in hospital_app/admin.py",
    ),
    "AppointmentQuerysetVisibilityTest.test_doctor_sees_only_own_and_assigned": (
        "A doctor must see only appointments where they are responsible "
        "OR assigned as assistant via AppointmentAssignment",
        "AppointmentAdmin.get_queryset - use Q(responsible_doctor=...) | "
        "Q(appointmentassignment__doctor=...)",
    ),

    # --- Forms -------------------------------------------------------------
    "AppointmentFormTest.test_excludes_responsible_doctor_and_appointment_type": (
        "AppointmentForm must NOT expose responsible_doctor or "
        "appointment_type (the view sets them automatically)",
        "AppointmentForm.Meta.exclude in hospital_app/forms.py",
    ),
    "AppointmentFormTest.test_widgets_have_bootstrap_form_control_class": (
        "Every visible widget must carry the Bootstrap 'form-control' "
        "class",
        "AppointmentForm.__init__ in hospital_app/forms.py - loop over "
        "self.fields and set widget.attrs['class']",
    ),
    "AppointmentFormTest.test_form_includes_minimum_required_fields": (
        "AppointmentForm must expose at least description, datetime and "
        "patient",
        "AppointmentForm.Meta in hospital_app/forms.py",
    ),

    # --- URLs --------------------------------------------------------------
    "UrlRoutingTest.test_index_route_exists": (
        "There must be a route for the home page (the list of doctors)",
        "hospital_system/urls.py - path('', views.index, name='index')",
    ),
    "UrlRoutingTest.test_doctor_detail_route_exists_with_id_kwarg": (
        "There must be a route /doctors/<int:doctor_id>/ named "
        "'doctor_detail'",
        "hospital_system/urls.py - "
        "path('doctors/<int:doctor_id>/', views.doctor_detail, "
        "name='doctor_detail')",
    ),
    "UrlRoutingTest.test_admin_route_exists": (
        "There must be a route /admin/",
        "hospital_system/urls.py - path('admin/', admin.site.urls)",
    ),

    # --- Views -------------------------------------------------------------
    "IndexViewTest.test_index_returns_200": (
        "GET / must render without errors and return HTTP 200",
        "views.index in hospital_app/views.py + templates/index.html",
    ),
    "IndexViewTest.test_index_groups_doctors_by_specialty": (
        "views.index must put cardiologists, dermatologists and "
        "neurologists into separate context lists",
        "views.index in hospital_app/views.py - context keys "
        "`cardiologists`, `dermatologists`, `neurologists`",
    ),
    "IndexViewTest.test_index_doctor_names_appear": (
        "The home page must actually render the doctor names from each "
        "specialty group",
        "templates/index.html - {% for doctor in cardiologists %} "
        "{{ doctor.full_name }} ...",
    ),
    "DoctorDetailViewTest.test_returns_200_for_valid_doctor": (
        "GET /doctors/<id>/ for an existing doctor must return HTTP 200",
        "views.doctor_detail in hospital_app/views.py",
    ),
    "DoctorDetailViewTest.test_404_for_unknown_doctor": (
        "GET /doctors/<id>/ for a missing doctor must return HTTP 404",
        "views.doctor_detail - use get_object_or_404(Doctor, ...)",
    ),
    "DoctorDetailViewTest.test_context_lists_split_into_past_today_future": (
        "The doctor-detail context must hold three lists: "
        "past_appointments, today_appointments, future_appointments",
        "views.doctor_detail - filter Appointment by datetime relative "
        "to timezone.now()",
    ),
    "DoctorDetailViewTest.test_post_creates_appointment_with_correct_doctor_and_type": (
        "POST /doctors/<id>/ must create an Appointment with that doctor "
        "as responsible AND appointment_type set to that doctor's "
        "specialty",
        "views.doctor_detail - on form.is_valid() do "
        "appointment.responsible_doctor = doctor; "
        "appointment.appointment_type = doctor.specialty",
    ),
    "DoctorDetailViewTest.test_post_creates_appointment_assignment_for_doctor": (
        "POST /doctors/<id>/ must also create an AppointmentAssignment "
        "row linking the new appointment to the responsible doctor",
        "views.doctor_detail - "
        "AppointmentAssignment.objects.create(appointment=..., doctor=...)",
    ),
}


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

class _C:
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def _strip(text):
    """Strip ANSI escapes - used when --no-color is passed."""
    import re
    return re.sub(r"\033\[[0-9;]*m", "", text)


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = (
        "Run the auto-grader for the hospital_system exercise with "
        "human-friendly output."
    )

    # `--no-color` is provided automatically by BaseCommand.

    # ---- entry point ------------------------------------------------------

    def handle(self, *args, **options):
        # Django's BaseCommand exposes `no_color` (set by --no-color and by
        # piping output to a non-TTY when --force-color is not given).
        self.use_color = (
            not options.get("no_color", False) and sys.stdout.isatty()
        )

        self._title("Pre-flight checks")
        if not self._preflight():
            self._line(
                f"{_C.RED}Cannot run tests until the project starts "
                f"importing cleanly.{_C.RESET}"
            )
            sys.exit(1)

        self._title("Running tests")
        results = self._run_all_categories()

        self._summary(results)
        self._print_failures(results)

        passed = sum(r["passed"] for r in results)
        total = sum(r["total"] for r in results)
        sys.exit(0 if passed == total else 1)

    # ---- output helpers ---------------------------------------------------

    def _emit(self, text):
        if not self.use_color:
            text = _strip(text)
        self.stdout.write(text)

    def _title(self, text):
        bar = "=" * 60
        self._emit("")
        self._emit(f"{_C.BOLD}{_C.CYAN}{bar}{_C.RESET}")
        self._emit(f"{_C.BOLD}{_C.CYAN}  {text}{_C.RESET}")
        self._emit(f"{_C.BOLD}{_C.CYAN}{bar}{_C.RESET}")

    def _line(self, text=""):
        self._emit(text)

    # ---- pre-flight -------------------------------------------------------

    def _preflight(self):
        modules = [
            "hospital_app.models",
            "hospital_app.admin",
            "hospital_app.signals",
            "hospital_app.forms",
            "hospital_app.views",
            "hospital_system.urls",
        ]
        ok = True
        for mod in modules:
            try:
                # importlib.reload is unnecessary - Django has already
                # loaded these once during setup; we just verify the
                # module object exists and didn't raise.
                if mod not in sys.modules:
                    importlib.import_module(mod)
                self._line(f"  {_C.GREEN}OK{_C.RESET}   {mod}")
            except Exception as exc:
                ok = False
                self._line(f"  {_C.RED}FAIL{_C.RESET} {mod}")
                tb = traceback.format_exception_only(type(exc), exc)
                for tline in tb:
                    self._line(f"       {_C.DIM}{tline.rstrip()}{_C.RESET}")
        # Detect model-vs-migration drift (the common "I added a field but
        # forgot to run makemigrations" mistake).
        try:
            from django.apps import apps
            from django.db.migrations.autodetector import MigrationAutodetector
            from django.db.migrations.loader import MigrationLoader
            from django.db.migrations.questioner import (
                NonInteractiveMigrationQuestioner,
            )
            from django.db.migrations.state import ProjectState
            from django.db import connection

            loader = MigrationLoader(None, ignore_no_migrations=True)
            autodetector = MigrationAutodetector(
                loader.project_state(),
                ProjectState.from_apps(apps),
                NonInteractiveMigrationQuestioner(specified_apps=None),
            )
            changes = autodetector.changes(graph=loader.graph)
            drifted = sorted(changes.keys())
            if drifted:
                self._line(
                    f"  {_C.YELLOW}WARN{_C.RESET} models in "
                    f"{', '.join(drifted)} have changes not yet captured "
                    f"in a migration"
                )
                self._line(
                    f"       {_C.DIM}run `python manage.py makemigrations`"
                    f"{_C.RESET}"
                )
            else:
                self._line(
                    f"  {_C.GREEN}OK{_C.RESET}   models match migrations"
                )
        except Exception as exc:
            self._line(
                f"  {_C.YELLOW}WARN{_C.RESET} could not verify migrations: "
                f"{exc}"
            )
        return ok

    # ---- running tests ----------------------------------------------------

    def _run_all_categories(self):
        from django.test.runner import DiscoverRunner

        runner = DiscoverRunner(verbosity=0, interactive=False)
        runner.setup_test_environment()
        old_config = runner.setup_databases()
        try:
            results = []
            for idx, (label, dotted, fallback_where) in enumerate(
                CATEGORIES, start=1
            ):
                results.append(
                    self._run_one_category(
                        runner, idx, label, dotted, fallback_where
                    )
                )
        finally:
            runner.teardown_databases(old_config)
            runner.teardown_test_environment()
        return results

    def _run_one_category(
        self, runner, idx, label, dotted, fallback_where
    ):
        loader = unittest.defaultTestLoader
        result = unittest.TestResult()
        try:
            suite = loader.loadTestsFromName(dotted)
        except Exception as exc:
            tb = traceback.format_exc()
            label_str = f"{label:<10}"
            self._line(
                f"  [{idx}/{len(CATEGORIES)}] {label_str} "
                f"{_C.RED}IMPORT ERROR{_C.RESET}"
            )
            return {
                "label": label,
                "total": 1,
                "passed": 0,
                "failures": [
                    {
                        "test_id": dotted,
                        "requirement": (
                            f"the {label.lower()} test module must import "
                            f"cleanly"
                        ),
                        "where": fallback_where,
                        "error": tb.strip().splitlines()[-1],
                    }
                ],
            }

        # Tee stdout/stderr so test output (print statements from views,
        # signals, etc) does not pollute the report.
        buf = io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = buf
        try:
            suite.run(result)
        finally:
            sys.stdout, sys.stderr = old_out, old_err

        total = result.testsRun
        # In unittest, failures are AssertionErrors; errors are everything
        # else (ImportError, KeyError, ...). We treat both as failures.
        bad = result.failures + result.errors
        passed = total - len(bad)

        status = (
            f"{_C.GREEN}OK{_C.RESET}"
            if passed == total
            else f"{_C.RED}FAIL{_C.RESET}"
        )
        label_str = f"{label:<10}"
        bar = self._bar(passed, total)
        self._line(
            f"  [{idx}/{len(CATEGORIES)}] {label_str} {bar} "
            f"{status} {passed}/{total}"
        )

        failures = []
        for test, tb in bad:
            test_id = test.id() if hasattr(test, "id") else str(test)
            # ClassName.method
            short = ".".join(test_id.split(".")[-2:])
            hint = TEST_HINTS.get(short, None)
            requirement, where = (
                hint if hint else (short, fallback_where)
            )
            failures.append(
                {
                    "test_id": test_id,
                    "requirement": requirement,
                    "where": where,
                    "error": _last_assertion_line(tb),
                }
            )

        return {
            "label": label,
            "total": total,
            "passed": passed,
            "failures": failures,
        }

    # ---- reporting --------------------------------------------------------

    def _bar(self, passed, total, width=24):
        if total == 0:
            return f"{_C.DIM}{'.' * width}{_C.RESET}"
        filled = int(round(width * passed / total))
        green = _C.GREEN + "#" * filled + _C.RESET
        empty = _C.DIM + "." * (width - filled) + _C.RESET
        return green + empty

    def _summary(self, results):
        passed = sum(r["passed"] for r in results)
        total = sum(r["total"] for r in results)
        self._line("")
        if passed == total:
            self._line(
                f"  {_C.BOLD}{_C.GREEN}ALL {total} TESTS PASS"
                f"{_C.RESET}"
            )
        else:
            self._line(
                f"  {_C.BOLD}{passed}/{total} tests passing "
                f"({total - passed} failing){_C.RESET}"
            )

    def _print_failures(self, results):
        all_failures = [
            (cat["label"], f) for cat in results for f in cat["failures"]
        ]
        if not all_failures:
            return

        self._title("Failures - what to fix")
        for category, f in all_failures:
            self._line("")
            self._line(
                f"  {_C.RED}FAIL{_C.RESET} {_C.BOLD}{category}{_C.RESET} "
                f"-> {f['test_id'].split('.')[-1]}"
            )
            self._line(
                f"        {_C.BOLD}Requirement:{_C.RESET} {f['requirement']}"
            )
            self._line(
                f"        {_C.BOLD}Error:{_C.RESET}       "
                f"{_C.DIM}{f['error']}{_C.RESET}"
            )


def _last_assertion_line(tb_string):
    """
    Squeeze a traceback into something a student can read at a glance:
    the final line, which is normally `AssertionError: ...` or
    `ImportError: ...`. Falls back to the last non-empty line.
    """
    if not tb_string:
        return ""
    for line in reversed(tb_string.strip().splitlines()):
        s = line.strip()
        if s:
            return s
    return ""
