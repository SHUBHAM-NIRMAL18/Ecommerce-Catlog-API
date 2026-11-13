import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.importer import CatalogError, clean_catalog, load_catalog


class Command(BaseCommand):
    help = "Import catalog.json into the database. Safe to run repeatedly (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--file", default=settings.CATALOG_FILE, help="Path to catalog.json")

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.is_file():
            raise CommandError(f"Catalog file not found: {path}")

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"{path} is not valid JSON: {exc}") from exc

        try:
            clean = clean_catalog(raw)
        except CatalogError as exc:
            raise CommandError(str(exc)) from exc

        counts = load_catalog(clean)

        expected = {
            "products": len(clean.products),
            "variants": len(clean.variants),
            "reviews": len(clean.reviews),
        }
        mismatches = {name: (counts[name], want) for name, want in expected.items() if counts[name] != want}
        if mismatches:
            raise CommandError(f"Counts after seeding don't match the file (db, file): {mismatches}")

        self.stdout.write(self.style.SUCCESS(
            "Seeded: " + ", ".join(f"{count} {name}" for name, count in counts.items())
        ))
        self._report("Data fixes", clean.fixes)
        self._report("Notes (left as-is, handled in the API/UI)", clean.notes)

    def _report(self, title, lines):
        self.stdout.write(f"\n{title} ({len(lines)}):")
        for line in lines:
            self.stdout.write(f"  - {line}")
