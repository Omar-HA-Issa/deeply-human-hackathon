"""
Template-based question generator - generates questions from dataset without AI (FREE).
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from django.conf import settings


@dataclass
class GeneratedQuestion:
    """Data class for a generated question before saving to DB."""
    prompt: str
    choices: list[str]
    correct_index: int
    difficulty: int
    category_name: str
    explanation: str
    source: str = "dataset"


# Map dataset categories to model category names
DATASET_TO_MODEL_CATEGORY = {
    "People & Society": "mental",
    "Economy": "economic",
    "Health": "physical",
    "Environment": "environmental",
    "Geography & Physical": "physical",
}

# Best metrics for template questions (high coverage, interesting, measurable)
TEMPLATE_METRICS = {
    # Demographics
    "life_expectancy_female": {
        "display_name": "female life expectancy",
        "unit": "years",
        "format": "{:.1f}",
        "category": "Health",
    },
    "life_expectancy_male": {
        "display_name": "male life expectancy",
        "unit": "years",
        "format": "{:.1f}",
        "category": "Health",
    },
    "median_age_years": {
        "display_name": "median age",
        "unit": "years",
        "format": "{:.1f}",
        "category": "People & Society",
    },
    "population_density_per_square_km": {
        "display_name": "population density",
        "unit": "people per km²",
        "format": "{:.0f}",
        "category": "Geography & Physical",
    },
    "urban_population_percent_of_total": {
        "display_name": "urban population",
        "unit": "%",
        "format": "{:.1f}",
        "category": "People & Society",
    },

    # Health & Lifestyle
    "infant_mortality_rate_per_1000_births": {
        "display_name": "infant mortality rate",
        "unit": "per 1000 births",
        "format": "{:.1f}",
        "category": "Health",
    },
    "medical_doctors_per_1000_people": {
        "display_name": "doctors per 1000 people",
        "unit": "",
        "format": "{:.2f}",
        "category": "Health",
    },
    "alcohol_consumption_per_adult_15plus_litres": {
        "display_name": "alcohol consumption per adult",
        "unit": "litres/year",
        "format": "{:.1f}",
        "category": "Health",
    },

    # Education
    "literacy_rate_adult": {
        "display_name": "adult literacy rate",
        "unit": "%",
        "format": "{:.1f}",
        "category": "People & Society",
    },
    "mean_years_in_school_men_25_years_and_older": {
        "display_name": "average years of schooling (men)",
        "unit": "years",
        "format": "{:.1f}",
        "category": "People & Society",
    },

    # Technology
    "internet_users": {
        "display_name": "internet usage rate",
        "unit": "%",
        "format": "{:.1f}",
        "category": "People & Society",
    },
    "cell_phones_per_100_people": {
        "display_name": "cell phones per 100 people",
        "unit": "",
        "format": "{:.0f}",
        "category": "People & Society",
    },
    "cars_trucks_and_buses_per_1000_persons": {
        "display_name": "vehicles per 1000 people",
        "unit": "",
        "format": "{:.0f}",
        "category": "Economy",
    },

    # Environment
    "forest_coverage_percent": {
        "display_name": "forest coverage",
        "unit": "%",
        "format": "{:.1f}",
        "category": "Environment",
    },
    "co2_emissions_tonnes_per_person": {
        "display_name": "CO2 emissions per capita",
        "unit": "tonnes",
        "format": "{:.1f}",
        "category": "Environment",
    },
    "agricultural_land_percent_of_land_area": {
        "display_name": "agricultural land",
        "unit": "%",
        "format": "{:.1f}",
        "category": "Environment",
    },

    # Economy
    "gdppercapita_us_inflation_adjusted": {
        "display_name": "GDP per capita",
        "unit": "USD",
        "format": "${:,.0f}",
        "category": "Economy",
    },
    "inequality_index_gini": {
        "display_name": "inequality index (Gini)",
        "unit": "",
        "format": "{:.1f}",
        "category": "Economy",
    },
    "aged_15plus_unemployment_rate_percent": {
        "display_name": "unemployment rate",
        "unit": "%",
        "format": "{:.1f}",
        "category": "Economy",
    },

    # Safety
    "murder_per_100000_people": {
        "display_name": "murder rate",
        "unit": "per 100,000",
        "format": "{:.1f}",
        "category": "People & Society",
    },
    "traffic_deaths_per_100000_people": {
        "display_name": "traffic deaths",
        "unit": "per 100,000",
        "format": "{:.1f}",
        "category": "Health",
    },

    # Military & Government
    "military_expenditure_percent_of_gdp": {
        "display_name": "military spending",
        "unit": "% of GDP",
        "format": "{:.1f}",
        "category": "Economy",
    },

    # Quirky
    "pump_price_for_gasoline_us_per_liter": {
        "display_name": "gasoline price",
        "unit": "USD/liter",
        "format": "${:.2f}",
        "category": "Economy",
    },
    "working_hours_per_week": {
        "display_name": "average working hours",
        "unit": "hours/week",
        "format": "{:.1f}",
        "category": "Economy",
    },
}


class TemplateQuestionGenerator:
    """Generates questions from dataset using templates (no AI cost)."""

    def __init__(self):
        self._dataset: Optional[dict] = None
        self._rankings: Optional[dict] = None

    @property
    def dataset(self) -> dict:
        """Lazy load the dataset."""
        if self._dataset is None:
            self._dataset = self._load_dataset()
        return self._dataset

    def _load_dataset(self) -> dict:
        """Load the country trivia dataset from JSON file."""
        dataset_path = Path(settings.DATASET_PATH)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found at {dataset_path}")

        with open(dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_country_data(self, country_name: str) -> Optional[dict]:
        """Get all data for a specific country."""
        return self.dataset.get(country_name)

    def _find_metric_value(self, country_data: dict, metric_key: str) -> Optional[tuple]:
        """
        Find a metric value across all categories for a country.
        Returns (value, year) tuple or None if not found.
        """
        for category_name, category_data in country_data.items():
            if isinstance(category_data, dict) and metric_key in category_data:
                metric = category_data[metric_key]
                if isinstance(metric, dict) and "value" in metric:
                    return (metric["value"], metric.get("year"))
        return None

    def _generate_plausible_choices(self, correct_value: float, metric_info: dict, count: int = 4) -> tuple[list[str], int]:
        """
        Generate plausible wrong choices around the correct value.
        Returns (choices_list, correct_index).
        """
        format_str = metric_info.get("format", "{:.1f}")
        unit = metric_info.get("unit", "")

        def format_choice(val: float) -> str:
            try:
                formatted = format_str.format(val)
            except (ValueError, KeyError):
                formatted = f"{val:.1f}"
            if unit and unit not in formatted:
                formatted = f"{formatted} {unit}"
            return formatted

        # Generate variations (±10-40% of the value)
        variations = []
        for pct in [-0.3, -0.15, 0.15, 0.3]:
            varied = correct_value * (1 + pct)
            if varied > 0:
                variations.append(varied)

        # Add some absolute variations for small values
        if correct_value < 10:
            variations.extend([correct_value - 2, correct_value - 1, correct_value + 1, correct_value + 2])
            variations = [v for v in variations if v > 0]

        # Remove duplicates and sort
        variations = sorted(set([round(v, 1) for v in variations if abs(v - correct_value) > 0.1]))

        # Build wrong answers ensuring formatted uniqueness
        max_attempts = 50
        wrong_values: list[float] = []
        used_formatted = {format_choice(correct_value)}

        pool = variations[:]
        random.shuffle(pool)

        attempts = 0
        while len(wrong_values) < count - 1 and attempts < max_attempts:
            attempts += 1
            if pool:
                candidate = pool.pop()
            else:
                candidate = correct_value * random.uniform(0.5, 1.5)
            if candidate <= 0:
                continue
            candidate = round(candidate, 2)
            formatted = format_choice(candidate)
            if formatted in used_formatted:
                continue
            wrong_values.append(candidate)
            used_formatted.add(formatted)

        # If still short, nudge values to create distinct formatted choices
        if len(wrong_values) < count - 1:
            precision_match = None
            try:
                import re
                precision_match = re.search(r"\.([0-9])f", format_str)
            except Exception:
                precision_match = None

            decimals = int(precision_match.group(1)) if precision_match else 0
            step = 1 if decimals == 0 else 10 ** (-decimals)

            nudge = step
            while len(wrong_values) < count - 1:
                candidate = correct_value + nudge
                formatted = format_choice(candidate)
                if formatted not in used_formatted and candidate > 0:
                    wrong_values.append(candidate)
                    used_formatted.add(formatted)
                nudge += step

        # Create all choices and shuffle
        all_values = wrong_values[:count - 1] + [correct_value]
        random.shuffle(all_values)

        choices = [format_choice(v) for v in all_values]
        correct_index = all_values.index(correct_value)

        return choices, correct_index

    def generate_value_question(self, country_name: str, country_data: dict, exclude_metrics: set = None) -> Optional[GeneratedQuestion]:
        """
        Generate a "What is X in Country?" question.
        """
        if exclude_metrics is None:
            exclude_metrics = set()

        # Try to find a metric with data
        available_metrics = []
        for metric_key, metric_info in TEMPLATE_METRICS.items():
            if metric_key in exclude_metrics:
                continue
            result = self._find_metric_value(country_data, metric_key)
            if result is not None:
                available_metrics.append((metric_key, metric_info, result))

        if not available_metrics:
            return None

        # Pick a random metric
        metric_key, metric_info, (value, year) = random.choice(available_metrics)
        exclude_metrics.add(metric_key)  # Mark as used
        display_name = metric_info["display_name"]

        # Generate question
        prompt = f"What is the {display_name} in {country_name}?"
        if year:
            prompt = f"What is the {display_name} in {country_name} (as of {year})?"

        choices, correct_index = self._generate_plausible_choices(value, metric_info)

        # Map to model category
        dataset_category = metric_info.get("category", "People & Society")
        model_category = DATASET_TO_MODEL_CATEGORY.get(dataset_category, "mental")

        format_str = metric_info.get("format", "{:.1f}")
        try:
            formatted_value = format_str.format(value)
        except (ValueError, KeyError):
            formatted_value = f"{value:.1f}"

        explanation = f"The {display_name} in {country_name} is {formatted_value} {metric_info.get('unit', '')}."
        if year:
            explanation += f" (Data from {year})"

        return GeneratedQuestion(
            prompt=prompt,
            choices=choices,
            correct_index=correct_index,
            difficulty=1,  # Value questions are easy
            category_name=model_category,
            explanation=explanation,
            source="dataset",
        )

    def generate_questions(self, country_name: str, count: int = 5) -> list[GeneratedQuestion]:
        """
        Generate template-based questions for a country.
        Returns up to `count` questions with different metrics.
        """
        country_data = self.get_country_data(country_name)
        if not country_data:
            return []

        questions = []
        used_metrics = set()

        # Generate up to count unique value questions
        for _ in range(count):
            question = self.generate_value_question(country_name, country_data, exclude_metrics=used_metrics)
            if question:
                questions.append(question)

        return questions
