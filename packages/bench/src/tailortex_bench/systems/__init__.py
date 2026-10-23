"""System registry."""

from tailortex_bench.systems.external import External
from tailortex_bench.systems.prompt_baseline import PromptBaseline
from tailortex_bench.systems.tailortex_system import TailorTex
from tailortex_bench.systems.untailored import Untailored

__all__ = ["External", "PromptBaseline", "TailorTex", "Untailored"]
