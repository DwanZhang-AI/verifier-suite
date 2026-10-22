"""judge.rubric: the domain rubric library.

ingest   PRBench loading (column-whitelisted) + frozen deterministic splits
library  full-data tree model: entries, category files, README/INDEX, validation
build    library_v1 tree from the frozen LIBRARY split (zero LLM, deterministic)
cli      split | validate
"""
from .ingest import WEIGHT_MAP, JUDGE_EVIDENCE, load_prbench, split_tasks, load_split  # noqa: F401
from .library import Entry, entries_from_tasks, write_domain, load_domain              # noqa: F401
