"""TailorTex evidence matching engine."""

from tailortex.matching.scorer import MatchScore, score_experience, score_project, score_profile
from tailortex.matching.selector import select_for_resume

__all__ = [
    "MatchScore",
    "score_experience",
    "score_project",
    "score_profile",
    "select_for_resume",
]
