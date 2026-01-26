"""
Management command to clear cached questions so they regenerate with AI.
"""

from django.core.management.base import BaseCommand
from backend.apps.worldquest.models import Question


class Command(BaseCommand):
    help = "Clear all cached questions so they regenerate with AI on next request"

    def add_arguments(self, parser):
        parser.add_argument(
            "--country",
            type=str,
            help="Only clear questions for a specific country (ISO2 code, e.g., PT)",
        )

    def handle(self, *args, **options):
        country_code = options.get("country")

        if country_code:
            count = Question.objects.filter(country__iso2=country_code.upper()).count()
            Question.objects.filter(country__iso2=country_code.upper()).delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {count} questions for {country_code.upper()}")
            )
        else:
            count = Question.objects.count()
            Question.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted all {count} cached questions")
            )

        self.stdout.write(
            self.style.SUCCESS("Questions will regenerate with AI on next quiz request")
        )
