"""
Base TestCase that points MEDIA_ROOT at a per-process tempdir so test image
uploads don't end up in the project's real media/ folder.
"""
import tempfile

from django.test import TestCase, override_settings

_TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="hospital_test_media_")


@override_settings(MEDIA_ROOT=_TEST_MEDIA_ROOT)
class HospitalTestCase(TestCase):
    """Base for every test case in this app.

    The tempdir is intentionally not cleaned up after each class - it lives
    in the OS tempdir and is cheap, and cleaning between classes would break
    other classes that share the same MEDIA_ROOT.
    """

