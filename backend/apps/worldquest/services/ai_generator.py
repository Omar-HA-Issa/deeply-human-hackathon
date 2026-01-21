"""
AI-powered question generator using OpenAI GPT-3.5-turbo.
Generates creative, contextual questions and fun facts.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class AIGeneratedContent:
    """Data class for AI-generated question and fun fact."""
    question: Optional[dict] = None  # {prompt, choices, correct_index, explanation, difficulty}
    fun_fact: Optional[str] = None
    error: Optional[str] = None


# Categories from dataset to include in AI prompt
INTERESTING_METRICS = [
    # Demographics & Population
    "life_expectancy_female",
    "life_expectancy_male",
    "median_age_years",
    "population_density_per_square_km",
    "urban_population_percent_of_total",
    "population_growth_annual_percent",
    "age_at_1st_marriage_women",
    "total_population_with_projections",

    # Health & Lifestyle
    "infant_mortality_rate_per_1000_births",
    "medical_doctors_per_1000_people",
    "alcohol_consumption_per_adult_15plus_litres",
    "smoking_adults_percent_of_population_over_age_15",
    "body_mass_index_bmi_men_kgperm2",
    "body_mass_index_bmi_women_kgperm2",
    "food_supply_kilocalories_per_person_and_day",
    "sugar_per_person_g_per_day",
    "births_attended_by_skilled_health_staff_percent_of_total",

    # Economy & Wealth
    "gdppercapita_us_inflation_adjusted",
    "inequality_index_gini",
    "inflation_annual_percent",
    "exports_percent_of_gdp",
    "imports_percent_of_gdp",
    "tax_revenue_percent_of_gdp",
    "total_number_of_dollar_billionaires",
    "extreme_poverty_percent_people_below_300_a_day",

    # Employment
    "aged_15plus_unemployment_rate_percent",
    "agriculture_workers_percent_of_employment",
    "industry_workers_percent_of_employment",
    "service_workers_percent_of_employment",
    "working_hours_per_week",

    # Education
    "literacy_rate_adult",
    "mean_years_in_school_men_25_years_and_older",
    "mean_years_in_school_women_25_years_and_older",
    "children_out_of_school_primary",

    # Technology & Infrastructure
    "internet_users",
    "cell_phones_per_100_people",
    "broadband_subscribers_per_100_people",
    "cars_trucks_and_buses_per_1000_persons",
    "electricity_use_per_person",
    "roads_paved_percent_of_total_roads",

    # Environment & Energy
    "forest_coverage_percent",
    "co2_emissions_tonnes_per_person",
    "renewable_water_cu_meters_per_person",
    "agricultural_land_percent_of_land_area",

    # Safety & Security
    "murder_per_100000_people",
    "traffic_deaths_per_100000_people",
    "suicide_per_100000_people",

    # Military
    "military_expenditure_percent_of_gdp",
    "armed_forces_personnel_percent_of_labor_force",

    # Quirky & Interesting
    "pump_price_for_gasoline_us_per_liter",
    "bad_teeth_per_child_12_yr",
    "teen_fertility_rate_births_per_1000_women_ages_15_19",
    "contraceptive_use_percent_of_women_ages_15_49",
]

AI_PROMPT_TEMPLATE = """You are a trivia question generator for WorldQuest, a geography learning app.

Country: {country}
Data:
{metrics_json}

Generate {num_questions} trivia questions following this EXACT structure:

1. "did_you_know" - A hook fact to introduce the question (1 sentence)
2. "prompt" - Simple, direct question (NOT analytical like "What can be inferred...")
3. "choices" - Exactly 4 options
4. "correct_index" - Index of correct answer (0-3)
5. "surprising_fact" - Starts with "Surprising, right?" - explains WHY the answer is interesting
6. "insight" - A 5-8 word takeaway lesson

EXAMPLE:
{{
  "questions": [
    {{
      "did_you_know": "Bhutan rejected GDP as a measure of progress.",
      "prompt": "What does Bhutan measure instead of GDP?",
      "choices": ["Military strength", "Gross National Happiness", "Population growth", "Land ownership"],
      "correct_index": 1,
      "surprising_fact": "Surprising, right? Since the 1970s, Bhutan has prioritized Gross National Happiness—measuring psychological wellbeing, health, education, and environmental sustainability over economic growth.",
      "insight": "Countries can choose different definitions of success",
      "difficulty": 1
    }}
  ]
}}

RULES:
- Questions should be simple and direct
- Use real data from the metrics provided
- Cover different topics: health, economy, environment, population, etc.
- Make surprising_fact genuinely interesting and educational

Respond with ONLY valid JSON, no markdown."""


class AIQuestionGenerator:
    """Generates creative questions and fun facts using Groq (free & fast!)."""

    # Groq model - llama-3.3-70b is best quality, free tier
    MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy load Groq client."""
        if self._client is None:
            try:
                from groq import Groq
                api_key = settings.GROQ_API_KEY
                if not api_key:
                    logger.warning("GROQ_API_KEY not configured")
                    return None
                self._client = Groq(api_key=api_key)
            except ImportError:
                logger.warning("Groq package not installed")
                return None
        return self._client

    def _extract_metrics(self, country_data: dict) -> dict:
        """Extract interesting metrics from country data for the AI prompt."""
        metrics = {}

        for category_name, category_data in country_data.items():
            if not isinstance(category_data, dict):
                continue

            for metric_key in INTERESTING_METRICS:
                if metric_key in category_data:
                    metric = category_data[metric_key]
                    if isinstance(metric, dict) and "value" in metric:
                        # Clean up the metric name for display
                        display_name = metric_key.replace("_", " ").title()
                        metrics[display_name] = {
                            "value": metric["value"],
                            "year": metric.get("year"),
                        }

        return metrics

    def _validate_question(self, question: dict) -> bool:
        """Validate that a question has all required fields and valid values."""
        required_fields = ["prompt", "choices", "correct_index", "explanation"]
        if not all(field in question for field in required_fields):
            return False
        if len(question.get("choices", [])) != 4:
            return False
        if not isinstance(question.get("correct_index"), int):
            return False
        if question["correct_index"] < 0 or question["correct_index"] > 3:
            return False
        return True

    def generate_questions(self, country_name: str, country_data: dict, count: int = 5) -> list:
        """
        Generate ALL questions for a country in a single AI call.
        Returns list of question dicts.
        """
        if not self.client:
            logger.error("Groq client not available")
            return []

        # Extract relevant metrics
        metrics = self._extract_metrics(country_data)
        if not metrics:
            logger.error(f"No metrics available for {country_name}")
            return []

        # Build the prompt
        metrics_json = json.dumps(metrics, indent=2)
        prompt = AI_PROMPT_TEMPLATE.format(
            country=country_name,
            metrics_json=metrics_json,
            num_questions=count
        )

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trivia question generator. Generate engaging quiz questions based on real data. Always respond with valid JSON only, no markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=2000,  # More tokens for 5 questions
            )

            # Parse the response
            content = response.choices[0].message.content.strip()

            # Handle potential markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            data = json.loads(content)

            # Extract questions array
            questions_data = data.get("questions", [])

            # Validate each question
            valid_questions = []
            for q in questions_data:
                if self._validate_question(q):
                    valid_questions.append(q)
                else:
                    logger.warning(f"Invalid question skipped: {q}")

            logger.info(f"Generated {len(valid_questions)} questions for {country_name}")
            return valid_questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return []
