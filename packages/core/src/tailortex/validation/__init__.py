"""TailorTex claim validation system."""

from tailortex.validation.claim_validator import validate_claims
from tailortex.validation.latex_validator import validate_latex

__all__ = ["validate_claims", "validate_latex"]
