"""
AI-powered question generator using OpenAI GPT-3.5-turbo.
Generates creative, contextual questions and fun facts.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from openai import OpenAI

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

AI_PROMPT_TEMPLATE = """You are a trivia question generator for WorldQuest, a geography learning app that makes learning about countries fascinating.

Country: {country}
Data:
{metrics_json}

Generate {num_questions} trivia questions following this EXACT structure:

1. "did_you_know" - A fascinating, DETAILED hook fact (2-3 sentences) that DIRECTLY relates to the question. This should make the user curious and set up the question. Include context, comparisons to other countries, or historical background.

2. "prompt" - Simple, direct question (NOT analytical like "What can be inferred...")

3. "choices" - Exactly 4 options

4. "correct_index" - Index of correct answer (0-3)

5. "surprising_fact" - Shown when user gets it WRONG. Start with "Surprising, right?" then explain (2-3 sentences) WHY the correct answer is counterintuitive or interesting. Compare to what people might expect, explain the underlying reasons, or connect it to broader patterns.

6. "insight" - A 5-8 word takeaway lesson

7. "explanation" - 1-2 sentence explanation

8. "category" - One of: "economic", "social", "physical", "environmental"

EXAMPLE:
{{
  "questions": [
    {{
      "did_you_know": "While most countries chase economic growth, one small Himalayan kingdom decided money isn't everything. In 1972, Bhutan's young king made a radical choice that would influence global discussions about what truly makes a nation successful.",
      "prompt": "What does Bhutan measure instead of GDP?",
      "choices": ["Military strength", "Gross National Happiness", "Population growth", "Land ownership"],
      "correct_index": 1,
      "surprising_fact": "Surprising, right? While you might think economic output is the universal measure of success, Bhutan tracks citizens' psychological wellbeing, health, time use, and cultural resilience. This tiny nation of 750,000 people has inspired the UN to adopt a 'happiness resolution' and dozens of countries to create their own wellbeing indices.",
      "insight": "Countries can choose different definitions of success",
      "explanation": "Bhutan pioneered Gross National Happiness as an alternative to GDP.",
      "difficulty": 1,
      "category": "social"
    }}
  ]
}}

CRITICAL RULES FOR "did_you_know" AND "surprising_fact":
- Both MUST directly relate to the specific question being asked
- "did_you_know" should BUILD CURIOSITY before the question (shown to everyone)
- "surprising_fact" should EXPLAIN why the answer defies expectations (shown when wrong)
- Include specific details: numbers, comparisons, historical context, or cause-and-effect
- Make them genuinely interesting - imagine telling a friend something that makes them say "Wait, really?!"
- Avoid generic statements like "This country has interesting statistics"

CRITICAL: BE HONEST AND OBJECTIVE - DO NOT SPIN BAD STATISTICS POSITIVELY:
- If a statistic is poor (e.g., 67% literacy = 1 in 3 adults can't read), acknowledge it's a challenge, not an achievement
- If forest coverage is 13%, don't say it "highlights conservation efforts" - that's actually quite low
- Compare to global averages or other countries to give honest context
- Low numbers are low. High inequality is bad. Poor health outcomes are concerning.
- Be factual and educational, not a PR spokesperson for the country
- It's OK to mention challenges, struggles, or areas needing improvement
- Example of BAD framing: "Morocco's 13% forest coverage highlights their environmental efforts" (dishonest spin)
- Example of GOOD framing: "Morocco's 13% forest coverage is among the lowest in the Mediterranean region, reflecting the challenges of desertification" (honest context)

CRITICAL: DATA ACCURACY IS MANDATORY:
- The correct answer MUST use the EXACT value from the provided data (rounded to nearest whole number if needed)
- The number in "surprising_fact" and "explanation" MUST MATCH the correct answer EXACTLY
- NEVER make up or hallucinate numbers - only use what's in the data provided above
- If the data says "Service Workers Percent Of Employment: 46.2", the correct answer must be ~46%, NOT 60%
- Double-check: Does your correct_index point to the choice that matches the actual data value?
- Example of WRONG: Data says 46%, correct answer says 60%, explanation says 46% (INCONSISTENT - FAIL)
- Example of RIGHT: Data says 46%, correct answer says 46%, explanation says 46% (CONSISTENT - GOOD)

CRITICAL RULES FOR ANSWER CHOICES:
- ALL numeric choices MUST have the SAME level of precision (all whole numbers OR all with 1 decimal)
- WRONG: ["90%", "80%", "93.4%", "70%"] - the decimal makes the answer obvious!
- RIGHT: ["46%", "58%", "35%", "67%"] - all same format, similar plausibility
- The correct answer must be the ACTUAL value from the data
- Distractor answers should be plausible but WRONG values (not the real data)

CRITICAL: USE CORRECT UNITS:
- Life expectancy is in YEARS (e.g., "78 years"), NOT percent
- GDP per capita is in dollars (e.g., "$5,000"), NOT percent
- Population density is per square km (e.g., "50 per km²")
- Only use % for actual percentages (employment rate, literacy rate, etc.)

CRITICAL: DO NOT REVEAL ANSWERS IN CHOICES:
- NEVER include values in comparison question choices
- WRONG: "Which is higher?" with choices ["Female Life Expectancy (78 years)", "Male Life Expectancy (75 years)"] - answer is obvious!
- RIGHT: "What is the female life expectancy?" with choices ["72 years", "78 years", "81 years", "69 years"]
- For comparison questions, ask about ONE specific value, not which is higher/lower
- AVOID comparison questions entirely - ask direct "What is X?" questions instead

DIMENSIONAL COVERAGE - Generate questions across these categories:
1. ECONOMIC: GDP, trade, employment, inequality, inflation, billionaires, poverty
2. SOCIAL: Education, literacy, marriage age, internet access, healthcare, population
3. PHYSICAL: Life expectancy, BMI, infant mortality, alcohol, smoking, food supply
4. ENVIRONMENTAL: Forest coverage, CO2 emissions, water resources, agricultural land

You MUST include at least one question from each category.

Respond with ONLY valid JSON, no markdown."""


class AIQuestionGenerator:
    """Generates creative questions and fun facts using OpenAI GPT-3.5."""

    # OpenAI model - GPT-3.5-turbo for cost efficiency
    MODEL = "gpt-3.5-turbo"

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                api_key = settings.OPENAI_API_KEY
                if not api_key:
                    logger.warning("OPENAI_API_KEY not configured")
                    return None
                self._client = OpenAI(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                return None
        return self._client

    def _extract_metrics(self, country_data: dict) -> dict:
        """Extract interesting metrics from country data for the AI prompt."""
        import datetime
        current_year = datetime.datetime.now().year

        metrics = {}

        for category_name, category_data in country_data.items():
            if not isinstance(category_data, dict):
                continue

            for metric_key in INTERESTING_METRICS:
                if metric_key in category_data:
                    metric = category_data[metric_key]
                    if isinstance(metric, dict) and "value" in metric:
                        year = metric.get("year")

                        # Skip future projections (year > current year)
                        if year and year > current_year:
                            continue

                        # Skip very old data (older than 15 years)
                        if year and year < current_year - 15:
                            continue

                        # Clean up the metric name for display
                        display_name = metric_key.replace("_", " ").title()
                        metrics[display_name] = {
                            "value": metric["value"],
                            "year": year,
                        }

        return metrics

    def _validate_question(self, question: dict) -> bool:
        """Validate that a question has all required fields and valid values."""
        required_fields = ["prompt", "choices", "correct_index"]
        if not all(field in question for field in required_fields):
            return False
        if len(question.get("choices", [])) != 4:
            return False
        if not isinstance(question.get("correct_index"), int):
            return False
        if question["correct_index"] < 0 or question["correct_index"] > 3:
            return False
        return True

    def _extract_number_from_text(self, text: str) -> float | None:
        """Extract a numeric value from text like '46%', '12.5 years', '$5,000', etc."""
        import re
        if not text:
            return None
        # Remove currency symbols, commas, and common units
        cleaned = re.sub(r'[$€£,]', '', str(text))
        # Find numbers (including decimals)
        matches = re.findall(r'[-+]?\d*\.?\d+', cleaned)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return None
        return None

    def _find_matching_metric(self, question_prompt: str, metrics: dict) -> tuple[str, float] | None:
        """Try to find which metric the question is asking about."""
        prompt_lower = question_prompt.lower()

        # Map of keywords to metric patterns
        keyword_mappings = {
            'life expectancy': ['life expectancy'],
            'literacy': ['literacy'],
            'forest': ['forest coverage', 'forest'],
            'gdp': ['gdp', 'gdppercapita'],
            'unemployment': ['unemployment'],
            'infant mortality': ['infant mortality'],
            'population density': ['population density'],
            'urban population': ['urban population'],
            'service': ['service workers'],
            'agriculture': ['agriculture workers'],
            'industry': ['industry workers'],
            'internet': ['internet'],
            'doctors': ['medical doctors', 'doctors'],
            'co2': ['co2 emissions'],
            'alcohol': ['alcohol consumption'],
            'smoking': ['smoking'],
            'median age': ['median age'],
            'fertility': ['teen fertility', 'fertility rate'],
            'marriage': ['marriage'],
            'working hours': ['working hours'],
            'cell phone': ['cell phones'],
            'broadband': ['broadband'],
            'cars': ['cars trucks'],
            'electricity': ['electricity'],
            'roads': ['roads paved'],
            'water': ['renewable water'],
            'agricultural land': ['agricultural land'],
            'murder': ['murder'],
            'traffic death': ['traffic deaths'],
            'suicide': ['suicide'],
            'military': ['military expenditure'],
            'armed forces': ['armed forces'],
            'gasoline': ['pump price', 'gasoline'],
            'teeth': ['bad teeth'],
            'bmi': ['body mass index', 'bmi'],
            'food supply': ['food supply', 'kilocalories'],
            'sugar': ['sugar'],
            'inequality': ['inequality', 'gini'],
            'inflation': ['inflation'],
            'exports': ['exports'],
            'imports': ['imports'],
            'tax': ['tax revenue'],
            'billionaire': ['billionaire'],
            'poverty': ['poverty', 'extreme poverty'],
            'school': ['years in school', 'mean years'],
            'children out of school': ['children out of school'],
        }

        # Find which keyword matches the prompt
        for keyword, metric_patterns in keyword_mappings.items():
            if keyword in prompt_lower:
                # Find the matching metric in our data
                for metric_name, metric_data in metrics.items():
                    metric_name_lower = metric_name.lower()
                    for pattern in metric_patterns:
                        if pattern in metric_name_lower:
                            value = metric_data.get('value')
                            if value is not None:
                                try:
                                    return (metric_name, float(value))
                                except (ValueError, TypeError):
                                    pass
        return None

    def _validate_and_fix_answer(self, question: dict, metrics: dict) -> dict | None:
        """
        Validate that the correct answer matches the actual data.
        If not, try to fix the correct_index. Returns None if unfixable.
        """
        choices = question.get("choices", [])
        correct_index = question.get("correct_index", 0)
        prompt = question.get("prompt", "")

        # Try to find which metric this question is about
        metric_match = self._find_matching_metric(prompt, metrics)
        if not metric_match:
            # Can't validate - let it through but log
            logger.debug(f"Could not match question to metric: {prompt[:50]}...")
            return question

        metric_name, actual_value = metric_match

        # Extract numbers from all choices
        choice_values = []
        for choice in choices:
            num = self._extract_number_from_text(choice)
            choice_values.append(num)

        # Find the best matching choice
        best_match_index = None
        best_match_diff = float('inf')

        for i, choice_val in enumerate(choice_values):
            if choice_val is not None:
                diff = abs(choice_val - actual_value)
                if diff < best_match_diff:
                    best_match_diff = diff
                    best_match_index = i

        # Check if we found a good match within tolerance
        tolerance = max(actual_value * 0.15, 2)  # 15% tolerance or at least 2
        if best_match_index is None or best_match_diff > tolerance:
            # No choice matches the actual data - reject this question
            logger.error(
                f"Rejecting question - no choice matches actual data. "
                f"Metric: {metric_name}, Actual value: {actual_value}, "
                f"Choices: {choices}, Choice values: {choice_values}"
            )
            return None

        # Fix correct_index if needed
        if best_match_index != correct_index:
            logger.warning(
                f"Auto-fixed correct_index: {correct_index} -> {best_match_index} "
                f"for metric '{metric_name}' (actual: {actual_value})"
            )
            question["correct_index"] = best_match_index

        return question

    def generate_questions(self, country_name: str, country_data: dict, count: int = 5) -> list:
        """
        Generate ALL questions for a country in a single AI call.
        Returns list of question dicts.
        """
        if not self.client:
            logger.error("OpenAI client not available")
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
            # Calculate tokens needed: ~300 tokens per question
            max_tokens = max(2000, count * 350)

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
                max_tokens=max_tokens,
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

            # Validate each question and fix answers if needed
            valid_questions = []
            for q in questions_data:
                if not self._validate_question(q):
                    logger.warning(f"Invalid question structure skipped: {q}")
                    continue

                # Validate and auto-fix the correct answer against actual data
                fixed_q = self._validate_and_fix_answer(q, metrics)
                if fixed_q:
                    valid_questions.append(fixed_q)
                else:
                    logger.warning(f"Question rejected due to data mismatch: {q.get('prompt', '')[:50]}...")

            logger.info(f"Generated {len(valid_questions)} valid questions for {country_name}")
            return valid_questions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return []
