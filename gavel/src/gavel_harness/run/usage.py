"""Token usage of one task: the counted attempts summed, or the reason it is unknown.

The source is each counted attempt's ``usage`` field, Harbor's ``agent_result``
(the executor's own accounting parsed from its log): ``n_input_tokens``
(cached tokens included), ``n_cache_tokens`` and ``n_output_tokens``, plus
``cost_usd``. A task's usage sums its counted attempts, A and, when it ran, B.
When any counted attempt lacks one of the three counts, or reports 0 for all
three, the task's usage is ``{"unavailable": reason}``: never a partial sum and
never zero. Harbor writes 0 for a count its agent log does not carry (e.g.
``OpenCode.populate_context_post_run``), so three zeros say that the log held
no token counts, not that the agent used none.

The same rule reads the attempt rows of the original harness's run manifests
(:mod:`gavel_harness.export.from_run`), which have the same keys.

Trials discarded for rate-limit contamination are not counted attempts. In a
metered run the result also carries ``meter``: the proxy's ledger totals
(:class:`~gavel_harness.meter.TrialUsage` fields) summed over the trials of
the same attempts, an independent account of the same requests. The two are
reported side by side, not reconciled: the CLI also counts requests the agent
log does not, such as session-title calls.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, fields
from typing import Any

from ..meter import TrialUsage

TOKEN_FIELDS = ("n_input_tokens", "n_cache_tokens", "n_output_tokens")


def task_usage(attempts: Sequence[Mapping[str, Any]],
               meter: Sequence[TrialUsage] | None) -> dict[str, Any]:
    """The usage of a task whose counted attempt records are ``attempts``.

    ``meter`` holds the ledger totals of the same attempts' trials, or None for
    an unmetered run.
    """
    if not attempts:
        raise ValueError("a task has at least one counted attempt")
    usage: dict[str, Any] = {}
    reason = _missing(attempts)
    if reason is not None:
        usage["unavailable"] = reason
    else:
        for name in TOKEN_FIELDS:
            usage[name] = sum(record["usage"][name] for record in attempts)
        costs = [record["usage"].get("cost_usd") for record in attempts]
        usage["cost_usd"] = (sum(costs) if all(isinstance(c, (int, float)) for c in costs)
                             else None)
        usage["attempts"] = len(attempts)
    if meter is not None:
        usage["meter"] = {field.name: sum(getattr(row, field.name) for row in meter)
                          for field in fields(TrialUsage)}
    return usage


def meter_row(usage: TrialUsage) -> dict[str, int]:
    """One trial's ledger totals as JSON data."""
    return asdict(usage)


def _missing(attempts: Sequence[Mapping[str, Any]]) -> str | None:
    for record in attempts:
        trial = record.get("trial_dir")
        where = f"attempt {record.get('attempt')}" + (f" (trial {trial})" if trial else "")
        result = record.get("usage")
        if not isinstance(result, Mapping):
            return f"{where} has no agent_result: its agent never ran"
        absent = [name for name in TOKEN_FIELDS
                  if not isinstance(result.get(name), int) or isinstance(result.get(name), bool)]
        if absent:
            return f"{where}: the agent log gave no {', '.join(absent)}"
        if not any(result[name] for name in TOKEN_FIELDS):
            return f"{where}: the agent log gave no token counts (Harbor recorded 0 for each)"
    return None
