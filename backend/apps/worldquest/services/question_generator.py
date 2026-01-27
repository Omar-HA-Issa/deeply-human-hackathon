"""
Combined question generator that orchestrates template and AI generators.
Handles caching and database operations.
"""

import logging
import random
from typing import Optional

from django.db import transaction

from ..models import Country, Category, Question, Fact
from .template_generator import TemplateQuestionGenerator, DATASET_TO_MODEL_CATEGORY
from .ai_generator import AIQuestionGenerator

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """
    Main question generator that:
    1. Checks DB for cached questions (pool of 5)
    2. If missing, generates ALL questions using AI
    3. Returns all 5 for each quiz
    """

    # Total questions to cache per country (larger pool for variety)
    QUESTIONS_POOL_SIZE = 10
    # Questions to serve per quiz
    QUESTIONS_PER_QUIZ = 5

    def __init__(self):
        self.template_generator = TemplateQuestionGenerator()  # Used only to load dataset
        self.ai_generator = AIQuestionGenerator()

    def get_or_create_category(self, category_name: str) -> Category:
        """Get or create a category by name."""
        # Normalize category name to match model choices
        normalized = category_name.lower()
        if normalized not in [c[0] for c in Category.Names.choices]:
            # Default to mental if unknown
            normalized = "mental"

        category, _ = Category.objects.get_or_create(name=normalized)
        return category

    def get_country_by_code(self, country_code: str) -> Optional[Country]:
        """Get country by ISO2 code."""
        try:
            return Country.objects.get(iso2=country_code.upper())
        except Country.DoesNotExist:
            return None

    def get_country_by_name(self, country_name: str) -> Optional[Country]:
        """Get country by name."""
        try:
            return Country.objects.get(name__iexact=country_name)
        except Country.DoesNotExist:
            return None

    def _get_alternate_names(self, country_name: str) -> list[str]:
        """Get alternate names for a country to match dataset naming conventions."""
        # Mapping from common names to dataset names
        name_variants = {
            "Democratic Republic of the Congo": ["Congo, Dem. Rep.", "DRC", "DR Congo"],
            "Republic of the Congo": ["Congo, Rep.", "Congo"],
            "South Korea": ["Korea, Rep.", "Korea"],
            "North Korea": ["Korea, Dem. Rep."],
            "United States": ["USA", "United States of America"],
            "United Kingdom": ["UK", "Britain", "Great Britain"],
            "Russia": ["Russian Federation"],
            "Iran": ["Iran, Islamic Rep."],
            "Egypt": ["Egypt, Arab Rep."],
            "Venezuela": ["Venezuela, RB"],
            "Yemen": ["Yemen, Rep."],
            "Syria": ["Syrian Arab Republic"],
            "Laos": ["Lao", "Lao PDR"],
            "Vietnam": ["Viet Nam"],
            "Ivory Coast": ["Cote d'Ivoire", "Côte d'Ivoire"],
            "Czech Republic": ["Czechia"],
            "East Timor": ["Timor-Leste"],
            "Cape Verde": ["Cabo Verde"],
            "Gambia": ["Gambia, The"],
            "Bahamas": ["Bahamas, The"],
            "Kyrgyzstan": ["Kyrgyz Republic"],
            "Slovakia": ["Slovak Republic"],
            "Micronesia": ["Micronesia, Fed. Sts."],
        }

        # Start with the original name and common variations
        alternates = [country_name, country_name.title(), country_name.upper()]

        # Add mapped variants
        if country_name in name_variants:
            alternates.extend(name_variants[country_name])

        # Also check reverse mapping
        for standard_name, variants in name_variants.items():
            if country_name in variants:
                alternates.append(standard_name)
                alternates.extend(variants)

        return alternates

    def _get_cached_questions(self, country: Country, random_select: bool = True) -> list[Question]:
        """
        Get cached questions from DB.
        If random_select=True, returns random QUESTIONS_PER_QUIZ from the pool.
        If random_select=False, returns all cached questions (for checking pool size).
        """
        all_questions = list(country.questions.all())

        if not random_select:
            return all_questions

        # Randomly select QUESTIONS_PER_QUIZ from the pool
        if len(all_questions) <= self.QUESTIONS_PER_QUIZ:
            return all_questions

        return random.sample(all_questions, self.QUESTIONS_PER_QUIZ)

    def _save_template_question(self, country: Country, gen_question) -> Question:
        """Save a template-generated question to DB."""
        category = self.get_or_create_category(gen_question.category_name)

        question = Question.objects.create(
            country=country,
            category=category,
            prompt=gen_question.prompt,
            choices=gen_question.choices,
            correct_index=gen_question.correct_index,
            difficulty=gen_question.difficulty,
            explanation=gen_question.explanation,
            source=Question.Source.DATASET,
        )
        return question

    def _save_ai_question(self, country: Country, ai_question: dict) -> Question:
        """Save an AI-generated question to DB."""
        # Default to mental category for AI questions
        category = self.get_or_create_category("mental")

        # Get values directly - don't use fallback chains that create duplicates
        did_you_know = ai_question.get("did_you_know", "")
        surprising_fact = ai_question.get("surprising_fact", "")
        explanation = ai_question.get("explanation", "")

        question = Question.objects.create(
            country=country,
            category=category,
            prompt=ai_question["prompt"],
            choices=ai_question["choices"],
            correct_index=ai_question["correct_index"],
            difficulty=ai_question.get("difficulty", 2),
            explanation=explanation,
            did_you_know=did_you_know,
            surprising_fact=surprising_fact,
            insight=ai_question.get("insight", ""),
            source=Question.Source.AI,
        )
        return question

    def _save_fun_fact(self, country: Country, fun_fact: str) -> Fact:
        """Save a fun fact to DB."""
        category = self.get_or_create_category("mental")

        fact = Fact.objects.create(
            country=country,
            category=category,
            title="Fun Fact",
            content=fun_fact,
        )
        return fact

    def _get_cached_fun_fact(self, country: Country) -> Optional[str]:
        """Get cached fun fact from DB."""
        fact = country.facts.filter(title="Fun Fact").first()
        return fact.content if fact else None

    @transaction.atomic
    def generate_for_country(self, country: Country) -> list[Question]:
        """
        Generate questions for a country using AI.
        Returns a random selection of QUESTIONS_PER_QUIZ questions.

        Maintains a pool of QUESTIONS_POOL_SIZE questions per country.
        ALL questions are AI-generated from the dataset.
        """
        # Check if we have enough questions in the pool
        all_cached = self._get_cached_questions(country, random_select=False)
        if len(all_cached) >= self.QUESTIONS_POOL_SIZE:
            # Pool is full, return random selection
            return random.sample(all_cached, self.QUESTIONS_PER_QUIZ)

        # Need to generate more questions
        questions_needed = self.QUESTIONS_POOL_SIZE - len(all_cached)
        logger.info(f"Generating {questions_needed} new questions for {country.name} (pool: {len(all_cached)}/{self.QUESTIONS_POOL_SIZE})")

        # Get country data from dataset
        country_data = self.template_generator.get_country_data(country.name)
        if not country_data:
            logger.warning(f"No dataset data for country: {country.name}")
            # Try alternate names (dataset uses different naming conventions)
            alternate_names = self._get_alternate_names(country.name)
            for name_variant in alternate_names:
                country_data = self.template_generator.get_country_data(name_variant)
                if country_data:
                    logger.info(f"Found data using alternate name: {name_variant}")
                    break

        if not country_data:
            # Return whatever we have cached
            if all_cached:
                return random.sample(all_cached, min(len(all_cached), self.QUESTIONS_PER_QUIZ))
            return []

        new_questions = []

        # Generate questions using AI
        try:
            logger.info("Attempting AI question generation for %s", country.name)
            ai_questions = self.ai_generator.generate_questions(
                country.name,
                country_data,
                count=questions_needed
            )

            if ai_questions:
                logger.info("AI generation succeeded for %s (%s questions)", country.name, len(ai_questions))
                for ai_q in ai_questions:
                    try:
                        q = self._save_ai_question(country, ai_q)
                        new_questions.append(q)
                    except Exception as e:
                        logger.error(f"Failed to save AI question: {e}")
            else:
                logger.warning(
                    "AI generation returned no questions for %s; falling back to template questions.",
                    country.name,
                )
                template_questions = self.template_generator.generate_questions(
                    country.name,
                    count=questions_needed,
                )
                for tmpl_q in template_questions:
                    try:
                        q = self._save_template_question(country, tmpl_q)
                        new_questions.append(q)
                    except Exception as e:
                        logger.error(f"Failed to save template question: {e}")

        except Exception as e:
            logger.error("AI generation failed for %s: %s", country.name, e)
            logger.warning("Falling back to template questions for %s", country.name)

            template_questions = self.template_generator.generate_questions(
                country.name,
                count=questions_needed,
            )
            for tmpl_q in template_questions:
                try:
                    q = self._save_template_question(country, tmpl_q)
                    new_questions.append(q)
                except Exception as save_error:
                    logger.error(f"Failed to save template question: {save_error}")

        # Combine cached + new, return random selection
        all_questions = all_cached + new_questions
        return random.sample(all_questions, min(len(all_questions), self.QUESTIONS_PER_QUIZ))

    def get_questions_for_country(self, country_code: str) -> tuple[list[Question], Optional[str]]:
        """
        Main entry point: Get or generate questions for a country by ISO2 code.
        Returns (questions, error_message).
        """
        country = self.get_country_by_code(country_code)
        if not country:
            return [], f"Country not found: {country_code}"

        try:
            questions = self.generate_for_country(country)
            return questions, None
        except Exception as e:
            logger.error(f"Failed to generate questions for {country_code}: {e}")
            return [], str(e)


# Singleton instance for convenience
_generator_instance: Optional[QuestionGenerator] = None


def get_question_generator() -> QuestionGenerator:
    """Get the singleton question generator instance."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = QuestionGenerator()
    return _generator_instance
