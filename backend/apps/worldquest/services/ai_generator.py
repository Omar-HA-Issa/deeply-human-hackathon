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

1. "did_you_know" - A fascinating, DETAILED hook fact (2-3 sentences) that ADDS VALUE beyond the question. This should provide CONTEXT, HISTORY, GLOBAL COMPARISONS, or CAUSE-AND-EFFECT that the user wouldn't learn just from answering the question.

2. "prompt" - Simple, direct question that includes the data year (e.g., "As of 2022, what is..." or "What was X in 2021?"). NOT analytical like "What can be inferred..."

3. "choices" - Exactly 4 options

4. "correct_index" - Index of correct answer (0-3)

5. "surprising_fact" - Shown when user gets it WRONG. Start with "Surprising, right?" then explain (2-3 sentences) WHY the correct answer is counterintuitive. Include global comparisons (e.g., "the global average is X"), historical trends, regional context, or explain the underlying causes.

6. "insight" - A 5-8 word takeaway lesson

7. "explanation" - 1-2 sentence explanation

8. "category" - One of: "economic", "social", "physical", "environmental"

EXAMPLE:
{{
  "questions": [
    {{
      "did_you_know": "Despite its reputation as a tech powerhouse, Germany has struggled with rural internet infrastructure. While cities enjoy fast connections, many countryside areas still rely on outdated copper lines from the 1990s.",
      "prompt": "As of 2023, what percentage of Germans use the internet?",
      "choices": ["72%", "78%", "85%", "91%"],
      "correct_index": 2,
      "surprising_fact": "Surprising, right? At 85%, Germany lags behind Nordic neighbors like Denmark (93%) and the Netherlands (91%). The government's 2018 broadband initiative aims to close this digital divide, but progress has been slower than expected.",
      "insight": "Economic strength doesn't guarantee digital infrastructure",
      "explanation": "As of 2023, 85% of Germans use the internet.",
      "difficulty": 1,
      "category": "social"
    }}
  ]
}}

CRITICAL RULES FOR "did_you_know" - MUST ADD NEW INFORMATION:
- NEVER just restate or paraphrase the question or answer
- MUST teach something the user wouldn't learn from just answering the question
- Include at least ONE of: historical context, global comparison, cause-and-effect, or surprising connection
- BAD EXAMPLE: "Japan has an interesting life expectancy. The country is known for having long-living citizens." (This adds nothing!)
- GOOD EXAMPLE: "Japan's secret to longevity includes a diet rich in fish and vegetables, strong social bonds, and universal healthcare. The island of Okinawa has more centenarians per capita than anywhere else on Earth." (Teaches WHY!)

CRITICAL RULES FOR "surprising_fact" - MUST EXPLAIN WHY:
- NEVER just repeat the correct answer
- MUST explain WHY this answer might surprise people
- Include global/regional comparisons (e.g., "For comparison, the global average is X" or "This is higher than neighboring countries")
- Explain underlying causes, historical reasons, or contributing factors
- BAD EXAMPLE: "Surprising, right? Germany has a 78% internet usage rate." (Just restates the answer!)
- GOOD EXAMPLE: "Surprising, right? Despite being Europe's largest economy, Germany's internet infrastructure in rural areas has lagged behind neighbors like Denmark (93%) and the Netherlands (91%). Government initiatives since 2018 are working to close this digital divide." (Explains context and reasons!)

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

DIMENSIONAL COVERAGE - You are generating exactly 5 questions. Each MUST be from a DIFFERENT category:

Question 1 - ECONOMY (pick ONE): GDP per capita, unemployment rate, inequality/Gini index, exports, imports, inflation, poverty rate, billionaires count
Question 2 - DEMOGRAPHICS (pick ONE): Median age, population density, urban population %, population growth, marriage age
Question 3 - HEALTH (pick ONE): Life expectancy, infant mortality, doctors per capita, alcohol consumption, smoking rate, BMI
Question 4 - ENVIRONMENT (pick ONE): Forest coverage %, CO2 emissions, agricultural land %, renewable water resources
Question 5 - TECHNOLOGY/LIFESTYLE (pick ONE): Internet users %, cell phones per capita, vehicles per capita, working hours, electricity use

STRICT RULES FOR DIVERSITY:
- Pick ONLY ONE metric from each category above
- NEVER ask two questions about similar topics (e.g., don't ask about both male AND female life expectancy)
- Each question should teach something completely different about the country
- Aim for surprising or counterintuitive facts that challenge assumptions

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

                        # Skip future projections (year > current year) - too confusing
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
        if len({str(choice).strip() for choice in question.get("choices", [])}) != 4:
            return False
        if not isinstance(question.get("correct_index"), int):
            return False
        if question["correct_index"] < 0 or question["correct_index"] > 3:
            return False
        return True

    def _normalize_choice_precision(self, question: dict) -> dict:
        """Normalize all numeric choices to the same precision so answers aren't obvious."""
        import re

        choices = question.get("choices", [])
        if not choices:
            return question

        # Extract numeric values and their units from choices
        parsed = []
        for choice in choices:
            match = re.match(r'^([$€£]?)(\d+\.?\d*)\s*(.*)$', str(choice).strip())
            if match:
                prefix, num_str, suffix = match.groups()
                try:
                    num = float(num_str)
                    parsed.append((prefix, num, suffix, True))
                except ValueError:
                    parsed.append((None, None, None, False))
            else:
                parsed.append((None, None, None, False))

        # Check if all choices are numeric
        if not all(p[3] for p in parsed):
            return question  # Mixed format, can't normalize

        # Determine if any choice has decimals
        has_decimals = any('.' in str(p[1]) and p[1] != int(p[1]) for p in parsed if p[1] is not None)

        # Normalize all to same format (round to whole numbers for cleaner look)
        new_choices = []
        for prefix, num, suffix, valid in parsed:
            if valid:
                # Round to whole number for cleaner appearance
                rounded = int(round(num))
                new_choice = f"{prefix}{rounded}"
                if suffix:
                    new_choice += f" {suffix}" if not suffix.startswith('%') else suffix
                new_choices.append(new_choice.strip())
            else:
                new_choices.append(choices[parsed.index((prefix, num, suffix, valid))])

        question["choices"] = new_choices
        return question

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

        # Get the correct choice value to fix text fields
        correct_choice_value = choice_values[best_match_index]
        if correct_choice_value is not None:
            # Fix numbers in surprising_fact and explanation to match the correct choice
            import re
            for field in ["surprising_fact", "explanation", "did_you_know"]:
                if field in question and question[field]:
                    text = question[field]
                    # Find percentages or numbers that are close to actual_value but wrong
                    # and replace them with the correct choice value
                    def replace_wrong_number(match):
                        num = float(match.group(1))
                        # If this number is close to actual_value (within 20%), replace it
                        if abs(num - actual_value) < actual_value * 0.2:
                            # Format to match the original (with or without decimal)
                            if '.' in match.group(1):
                                return f"{correct_choice_value:.1f}"
                            else:
                                return f"{int(round(correct_choice_value))}"
                        return match.group(0)

                    # Match numbers followed by % or standalone decimals
                    question[field] = re.sub(r'(\d+\.?\d*)(?=%)', replace_wrong_number, text)

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
            # Calculate tokens needed: ~500 tokens per question for detailed facts
            max_tokens = max(3000, count * 500)

            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trivia question generator. Generate engaging quiz questions with DETAILED educational facts. Every question MUST include a meaningful 'did_you_know' (2-3 sentences with context/history/comparisons) and 'surprising_fact' (2-3 sentences explaining WHY the answer is surprising). Never skip these fields. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
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

                # Normalize choice precision so answers aren't obvious
                q = self._normalize_choice_precision(q)

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
