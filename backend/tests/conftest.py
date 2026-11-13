import io
import json

import pytest
from django.conf import settings
from django.core.management import call_command


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Seed the real catalog.json once into the test database, before any test uses it."""
    with django_db_blocker.unblock():
        call_command("seed", stdout=io.StringIO())


@pytest.fixture(scope="session")
def catalog():
    """The raw catalog.json. API tests compute their expected answers from it independently."""
    return json.loads(settings.CATALOG_FILE.read_text(encoding="utf-8"))
