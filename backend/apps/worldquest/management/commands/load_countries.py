"""
Management command to load countries from the dataset into the database.
Usage: python manage.py load_countries
"""

import json
import pycountry
from django.core.management.base import BaseCommand
from django.conf import settings
from backend.apps.worldquest.models import Country, Category


# Manual overrides for countries pycountry doesn't find
# Includes variations from the dataset naming conventions
# Also includes common countries to avoid fuzzy matching errors
MANUAL_ISO_CODES = {
    # Major countries (avoid fuzzy matching errors)
    "France": "FR",
    "UK": "GB",
    "United Kingdom": "GB",
    "Germany": "DE",
    "Italy": "IT",
    "Spain": "ES",
    "Portugal": "PT",
    "Netherlands": "NL",
    "Belgium": "BE",
    "Switzerland": "CH",
    "Austria": "AT",
    "Poland": "PL",
    "Sweden": "SE",
    "Norway": "NO",
    "Denmark": "DK",
    "Finland": "FI",
    "Ireland": "IE",
    "Greece": "GR",
    "Turkey": "TR",
    "Japan": "JP",
    "China": "CN",
    "India": "IN",
    "Brazil": "BR",
    "Mexico": "MX",
    "Canada": "CA",
    "Australia": "AU",
    "New Zealand": "NZ",
    "South Africa": "ZA",
    "Nigeria": "NG",
    "Kenya": "KE",
    "Morocco": "MA",
    "Argentina": "AR",
    "Chile": "CL",
    "Colombia": "CO",
    "Peru": "PE",
    "Thailand": "TH",
    "Indonesia": "ID",
    "Malaysia": "MY",
    "Philippines": "PH",
    "Singapore": "SG",
    "Saudi Arabia": "SA",
    "Israel": "IL",
    "United Arab Emirates": "AE",

    # Countries with naming variations
    "Russia": "RU",
    "South Korea": "KR",
    "North Korea": "KP",
    "Korea, Rep.": "KR",
    "Korea, Dem. Rep.": "KP",
    "Vietnam": "VN",
    "Laos": "LA",
    "Lao": "LA",
    "Iran": "IR",
    "Syria": "SY",
    "Venezuela": "VE",
    "Bolivia": "BO",
    "Tanzania": "TZ",
    "Czech Republic": "CZ",
    "Czechia": "CZ",
    "Moldova": "MD",
    "Kosovo": "XK",
    "Taiwan": "TW",
    "Macau": "MO",
    "Hong Kong": "HK",
    "Palestine": "PS",
    "Ivory Coast": "CI",
    "Cote d'Ivoire": "CI",
    "Democratic Republic of the Congo": "CD",
    "Congo, Dem. Rep.": "CD",
    "Republic of the Congo": "CG",
    "Congo, Rep.": "CG",
    "Brunei": "BN",
    "East Timor": "TL",
    "Timor-Leste": "TL",
    "Cape Verde": "CV",
    "Cabo Verde": "CV",
    "Micronesia": "FM",
    "Micronesia, Fed. Sts.": "FM",
    "Saint Kitts and Nevis": "KN",
    "St. Kitts and Nevis": "KN",
    "Saint Lucia": "LC",
    "St. Lucia": "LC",
    "Saint Vincent and the Grenadines": "VC",
    "St. Vincent and the Grenadines": "VC",
    "Sao Tome and Principe": "ST",
    "eSwatini": "SZ",
    "Swaziland": "SZ",
    "Burma": "MM",
    "Myanmar": "MM",
    "Turks and Caicos": "TC",
    "British Virgin Islands": "VG",
    "US Virgin Islands": "VI",
    "Virgin Islands (U.S.)": "VI",
    "Curacao": "CW",
    "Sint Maarten": "SX",
    "South Sudan": "SS",
    "Egypt": "EG",
    "Egypt, Arab Rep.": "EG",
    "Yemen": "YE",
    "Yemen, Rep.": "YE",
    "Gambia": "GM",
    "Gambia, The": "GM",
    "Bahamas": "BS",
    "Bahamas, The": "BS",
    "Kyrgyzstan": "KG",
    "Kyrgyz Republic": "KG",
    "Slovakia": "SK",
    "Slovak Republic": "SK",
    "United States": "US",
    "USA": "US",
}

# Entries to skip - territories/regions that would conflict with real countries
SKIP_ENTRIES = {
    "Clipperton",  # Would overwrite France (FR)
    "French Southern and Antarctic Lands",  # No ISO code
    "St. Martin (French part)",  # Would conflict
    "Channel Islands",  # Would conflict with UK
    "World",  # Not a country
    "Africa",  # Continent
    "Asia",  # Continent
    "Europe",  # Continent
    "North America",  # Continent
    "South America",  # Continent
    "Oceania",  # Continent
}


def get_iso_code(country_name):
    """Try to find ISO2 code for a country name."""
    # Check manual overrides first
    if country_name in MANUAL_ISO_CODES:
        return MANUAL_ISO_CODES[country_name]

    # Try exact match
    try:
        country = pycountry.countries.get(name=country_name)
        if country:
            return country.alpha_2
    except (KeyError, AttributeError):
        pass

    # Try fuzzy search
    try:
        results = pycountry.countries.search_fuzzy(country_name)
        if results:
            return results[0].alpha_2
    except LookupError:
        pass

    return None


class Command(BaseCommand):
    help = "Load countries and categories from the dataset JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing countries before loading",
        )

    def handle(self, *args, **options):
        # Create categories first
        self.stdout.write("Creating categories...")
        for choice in Category.Names.choices:
            Category.objects.get_or_create(name=choice[0])
        self.stdout.write(self.style.SUCCESS("Categories created."))

        # Load dataset
        dataset_path = settings.DATASET_PATH
        self.stdout.write(f"Loading dataset from {dataset_path}...")

        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Dataset not found at {dataset_path}"))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON: {e}"))
            return

        if options["clear"]:
            self.stdout.write("Clearing existing countries...")
            Country.objects.all().delete()

        # Load countries
        created_count = 0
        updated_count = 0
        skipped = []
        order_index = 0

        for country_name in data.keys():
            # Skip entries that are clearly not countries
            if not country_name or len(country_name) < 2:
                continue

            # Skip entries that would conflict with real countries
            if country_name in SKIP_ENTRIES:
                continue

            iso2 = get_iso_code(country_name)
            if not iso2:
                skipped.append(country_name)
                continue

            country, created = Country.objects.update_or_create(
                iso2=iso2,
                defaults={
                    "name": country_name,
                    "order_index": order_index,
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            order_index += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Created {created_count} countries, updated {updated_count}."
            )
        )

        if skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped {len(skipped)} entries (no ISO code found): {skipped[:20]}..."
                )
            )
