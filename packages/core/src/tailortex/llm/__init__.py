"""TailorTex LLM provider layer."""

from tailortex.llm.base import LLMError, LLMProvider, LLMResponse
from tailortex.llm.prompts import (
    BULLET_REWRITE_PROMPT,
    JOB_DESCRIPTION_PARSER_PROMPT,
    MODE_INSTRUCTIONS,
    RESUME_IMPORT_PROMPT,
)

__all__ = [
    "LLMError",
    "LLMProvider",
    "LLMResponse",
    "BULLET_REWRITE_PROMPT",
    "JOB_DESCRIPTION_PARSER_PROMPT",
    "MODE_INSTRUCTIONS",
    "RESUME_IMPORT_PROMPT",
]
