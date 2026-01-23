from __future__ import annotations

from typing import Iterable

XP_PER_CORRECT = 10
STREAK_BONUS_STEP = 0.2
XP_PER_UNLOCK = 40

QUIZ_POINTS_MAX = 100


def calculate_xp(correct_flags: Iterable[bool]) -> int:
    """
    Calculate XP using a streak multiplier.

    Each correct answer grants XP_PER_CORRECT, multiplied by
    1 + (streak - 1) * STREAK_BONUS_STEP for consecutive correct answers.
    """
    streak = 0
    xp_total = 0
    for is_correct in correct_flags:
        if is_correct:
            streak += 1
            multiplier = 1 + (streak - 1) * STREAK_BONUS_STEP
            xp_total += int(round(XP_PER_CORRECT * multiplier))
        else:
            streak = 0
    return xp_total


def calculate_quiz_points(correct_count: int, total: int) -> int:
    """Return points based on accuracy percentage (0-100)."""
    if total <= 0:
        return 0
    return int(round((correct_count / total) * QUIZ_POINTS_MAX))


def calculate_match_points(correct_count: int, total: int) -> int:
    """Match points use the same percentage-based formula for now."""
    return calculate_quiz_points(correct_count, total)
