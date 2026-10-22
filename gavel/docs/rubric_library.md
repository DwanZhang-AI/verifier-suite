# Rubric library: contents and rebuild

`src/gavel_harness/rubric/library_v1/` is the rubric library the method ships:
19,603 entries in six domains, built without any model call. `NOTICE` names the
sources, their licenses and the sha256 of every input file.

| Domain | Source | Membership |
|---|---|---|
| `finance`, `legal` | PRBench parquet files | tasks the hash split (salt `rubric-v1`) assigns to the library half |
| `finance_hard`, `legal_hard` | PRBench parquet files | every task |
| `airline_ops` | tau2-bench `data/tau2/domains/airline/tasks.json` | every task not listed in `rubric/library_v1_inputs/tau2_held_out_ids.txt` |
| `banking_ops` | tau2-bench `data/tau2/domains/banking_knowledge/documents/` | every document |

## Rebuilding library_v1

Every input is public or ships with the package. Reading the parquet files needs
the `rubric` extra (`pip install "gavel-harness[rubric]"`).

1. Download the four PRBench splits (`finance`, `legal`, `finance_hard`,
   `legal_hard`) from <https://huggingface.co/datasets/ScaleAI/PRBench> as
   `<name>.parquet` into one directory, and check their sha256 against `NOTICE`.
2. Write the PRBench library/evaluation split:

   ```bash
   python -m gavel_harness.rubric.cli split --prbench ./prbench --out ./splits
   ```

   This writes `./splits/prbench_splits_v1.tsv` and refuses to overwrite an
   existing one.
3. Check out tau2-bench at the commit named in `NOTICE`.
4. Build:

   ```bash
   python -m gavel_harness.rubric.build \
     --prbench ./prbench --prbench-splits ./splits/prbench_splits_v1.tsv \
     --tau2-domains ./tau2-bench/data/tau2/domains --out ./library
   ```

   `--tau2-held-out` defaults to the shipped held-out list, which library_v1 was
   built with; pass another list to hold out other tau2 tasks.

`./library` then equals `library_v1` file for file, including `build_audit.json`.
The build also writes a `MANIFEST.json` per domain, which binds the domain's
files to a content version; `library_v1` predates that file, and
`python -m gavel_harness.rubric.cli validate` accepts trees with or without it.
