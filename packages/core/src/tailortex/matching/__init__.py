"""TailorTex evidence matching engine."""

from tailortex.matching.scorer import MatchScore, score_experience, score_profile, score_project
from tailortex.matching.selector import select_for_resume

__all__ = [
    "MatchScore",
    "score_experience",
    "score_profile",
    "score_project",
    "select_for_resume",
]
