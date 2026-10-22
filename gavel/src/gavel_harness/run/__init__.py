"""Execution layer: Harbor jobs, generation attempts and executors.

:func:`generate` runs sealed generation packages through the generating
executor on Harbor's docker environment and returns one
:class:`GenerationResult` per package; :mod:`.session` describes the attempt
flow, :mod:`.job` the Harbor job, :mod:`.watchdog` the stall watchdog.
"""

from .session import GenerationResult, generate

__all__ = ["GenerationResult", "generate"]
