"""
URL routing tests. The exam requires three reachable pages:

* the home page (list of doctors)
* a doctor-detail page parameterised by doctor id
* the standard Django admin

The URL names for the first two are not strictly mandated, but the routes
must exist.
"""
from .base import HospitalTestCase as TestCase
from django.urls import resolve, reverse


class UrlRoutingTest(TestCase):
    def test_index_route_exists(self):
        # Either named 'index' or simply '/'
        try:
            url = reverse("index")
        except Exception:
            url = "/"
        match = resolve(url)
        self.assertIsNotNone(match)

    def test_doctor_detail_route_exists_with_id_kwarg(self):
        url = reverse("doctor_detail", kwargs={"doctor_id": 1})
        match = resolve(url)
        self.assertEqual(match.kwargs.get("doctor_id"), 1)

    def test_admin_route_exists(self):
        match = resolve("/admin/")
        self.assertIsNotNone(match)
