"""
Combined question generator that orchestrates template and AI generators.
Handles caching and database operations.
"""

import logging
from typing import Optional

from django.db import transaction

from ..models import Country, Category, Question, Fact
from .template_generator import TemplateQuestionGenerator, DATASET_TO_MODEL_CATEGORY
from .ai_generator import AIQuestionGenerator

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """
    Main question generator that:
    1. Checks DB for cached questions
    2. If missing, generates ALL questions using AI
    3. Caches in DB and returns
    """

    # Target question counts - ALL AI generated
    TOTAL_QUESTIONS = 5

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

    def _get_cached_questions(self, country: Country) -> list[Question]:
        """Get cached questions from DB."""
        return list(country.questions.all()[:5])

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

        question = Question.objects.create(
            country=country,
            category=category,
            prompt=ai_question["prompt"],
            choices=ai_question["choices"],
            correct_index=ai_question["correct_index"],
            difficulty=ai_question.get("difficulty", 2),
            explanation=ai_question.get("explanation", ""),
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
    def generate_for_country(self, country: Country) -> tuple[list[Question], Optional[str]]:
        """
        Generate questions for a country using AI.
        Returns (questions, fun_fact).

        ALL questions are AI-generated from the dataset.
        """
        # Check for cached questions
        cached = self._get_cached_questions(country)
        if len(cached) >= self.TOTAL_QUESTIONS:
            fun_fact = self._get_cached_fun_fact(country)
            return cached, fun_fact

        # Get country data from dataset
        country_data = self.template_generator.get_country_data(country.name)
        if not country_data:
            logger.warning(f"No dataset data for country: {country.name}")
            # Try variations of the name
            for name_variant in [country.name, country.name.title(), country.name.upper()]:
                country_data = self.template_generator.get_country_data(name_variant)
                if country_data:
                    break

        if not country_data:
            return [], None

        questions = []
        fun_fact = None

        # Generate ALL questions using AI
        try:
            ai_questions, ai_fun_fact = self.ai_generator.generate_questions(
                country.name,
                country_data,
                count=self.TOTAL_QUESTIONS
            )

            for ai_q in ai_questions:
                try:
                    q = self._save_ai_question(country, ai_q)
                    questions.append(q)
                except Exception as e:
                    logger.error(f"Failed to save AI question: {e}")

            if ai_fun_fact:
                try:
                    self._save_fun_fact(country, ai_fun_fact)
                    fun_fact = ai_fun_fact
                except Exception as e:
                    logger.error(f"Failed to save fun fact: {e}")

        except Exception as e:
            logger.error(f"AI generation failed: {e}")

        # If no fun fact from AI, try to get cached one
        if not fun_fact:
            fun_fact = self._get_cached_fun_fact(country)

        return questions, fun_fact

    def get_questions_for_country(self, country_code: str) -> tuple[list[Question], Optional[str], Optional[str]]:
        """
        Main entry point: Get or generate questions for a country by ISO2 code.
        Returns (questions, fun_fact, error_message).
        """
        country = self.get_country_by_code(country_code)
        if not country:
            return [], None, f"Country not found: {country_code}"

        try:
            questions, fun_fact = self.generate_for_country(country)
            return questions, fun_fact, None
        except Exception as e:
            logger.error(f"Failed to generate questions for {country_code}: {e}")
            return [], None, str(e)


# Singleton instance for convenience
_generator_instance: Optional[QuestionGenerator] = None


def get_question_generator() -> QuestionGenerator:
    """Get the singleton question generator instance."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = QuestionGenerator()
    return _generator_instance
